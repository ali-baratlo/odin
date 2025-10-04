import json
from kubernetes import client
from kubernetes.client import ApiClient
from cluster_config import CLUSTERS
from utils.db import get_resource_collection, get_audit_log_collection
from models.resource import Resource, AuditLog
from jsondiff import diff

def collect_resources():
    """
    Collects various Kubernetes resources from configured clusters and stores them in MongoDB.
    """
    resource_collection = get_resource_collection()
    audit_log_collection = get_audit_log_collection()
    api_client = ApiClient()

    RESOURCE_TYPES_TO_COLLECT = [
        {"name": "ConfigMap", "list_func": "list_namespaced_config_map", "api": "CoreV1Api"},
        {"name": "Secret", "list_func": "list_namespaced_secret", "api": "CoreV1Api"},
        {"name": "Deployment", "list_func": "list_namespaced_deployment", "api": "AppsV1Api"},
        {"name": "Service", "list_func": "list_namespaced_service", "api": "CoreV1Api"},
        {"name": "Ingress", "list_func": "list_namespaced_ingress", "api": "NetworkingV1Api"},
    ]

    for cluster in CLUSTERS:
        cluster_name = cluster["name"]
        api_server = cluster["api_server"]
        token = cluster["token"]
        namespace_label_selector = cluster.get("namespace_label_selector", "") # Get the label selector

        print(f"\nCollecting from {cluster_name}")

        configuration = client.Configuration()
        configuration.host = api_server
        configuration.verify_ssl = False
        configuration.api_key = {"authorization": f"Bearer {token}"}

        core_v1_api = client.CoreV1Api(client.ApiClient(configuration))
        apps_v1_api = client.AppsV1Api(client.ApiClient(configuration))
        networking_v1_api = client.NetworkingV1Api(client.ApiClient(configuration))

        api_map = {
            "CoreV1Api": core_v1_api,
            "AppsV1Api": apps_v1_api,
            "NetworkingV1Api": networking_v1_api
        }

        try:
            # Use the label selector to filter namespaces
            namespaces = core_v1_api.list_namespace(label_selector=namespace_label_selector)
        except Exception as e:
            print(f"Error fetching namespaces from {cluster_name} with selector '{namespace_label_selector}': {e}")
            continue

        for ns in namespaces.items:
            namespace_name = ns.metadata.name
            for resource_type_info in RESOURCE_TYPES_TO_COLLECT:
                resource_type_name = resource_type_info["name"]
                list_func_name = resource_type_info["list_func"]
                api_name = resource_type_info["api"]

                api_instance = api_map[api_name]
                list_func = getattr(api_instance, list_func_name)

                try:
                    resources = list_func(namespace=namespace_name)
                except Exception as e:
                    print(f"Error fetching {resource_type_name} from {namespace_name} in {cluster_name}: {e}")
                    continue

                for item in resources.items:
                    resource_dict = api_client.sanitize_for_serialization(item)
                    full_resource_str = json.dumps(resource_dict)

                    query = {
                        "cluster_name": cluster_name,
                        "namespace": namespace_name,
                        "resource_type": resource_type_name,
                        "resource_name": item.metadata.name,
                    }

                    existing_resource = resource_collection.find_one(query)

                    if existing_resource:
                        if existing_resource["resource_version"] != item.metadata.resource_version:
                            difference = diff(existing_resource["data"], resource_dict, syntax='symmetric')

                            audit_log = AuditLog(
                                resource_id=str(existing_resource["_id"]),
                                old_version=existing_resource["resource_version"],
                                new_version=item.metadata.resource_version,
                                diff=difference,
                            )
                            audit_log_collection.insert_one(audit_log.dict())

                            resource_collection.update_one(
                                {"_id": existing_resource["_id"]},
                                {
                                    "$set": {
                                        "resource_version": item.metadata.resource_version,
                                        "data": resource_dict,
                                        "full_resource_string": full_resource_str,
                                        "created_at": audit_log.changed_at
                                    }
                                }
                            )
                            print(f"Updated {resource_type_name} '{item.metadata.name}' in '{namespace_name}'")
                    else:
                        new_resource = Resource(
                            cluster_name=cluster_name,
                            namespace=namespace_name,
                            resource_type=resource_type_name,
                            resource_name=item.metadata.name,
                            resource_version=item.metadata.resource_version,
                            data=resource_dict,
                            full_resource_string=full_resource_str,
                        )
                        resource_collection.insert_one(new_resource.dict())
                        print(f"Inserted new {resource_type_name} '{item.metadata.name}' in '{namespace_name}'")

    print("\nResource collection complete.")