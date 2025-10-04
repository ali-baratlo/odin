import json
import hashlib
from datetime import datetime
from kubernetes.client import ApiClient
from psycopg2.extras import Json
from datetime import datetime
from utils.diff import get_diff


def insert_resources(resource_json, cluster_name, resource_type, conn, cursor):
    metadata = resource_json.metadata
    name = metadata.name
    namespace = metadata.namespace
    uid = metadata.uid
    version = metadata.resource_version
    labels = metadata.labels or {}
    annotations = metadata.annotations or {}

    api_client = ApiClient()
    resource_dict = api_client.sanitize_for_serialization(resource_json)
    hash_val = get_resource_hash(resource_dict)

    cursor.execute("""
        SELECT version_int, hash, raw_json FROM k8s_resources
        WHERE cluster_name = %s AND namespace = %s AND resource_type = %s AND resource_name = %s
        ORDER BY version_int DESC LIMIT 1;
    """, (cluster_name, namespace, resource_type, name))
    last = cursor.fetchone()

    pretty_json_str = json.dumps(resource_dict, indent=2)
    pretty_json = Json(json.loads(pretty_json_str))

    if last and last[1] == hash_val:
        print(f"No changes in {resource_type} '{name}' in ns '{namespace}'")
    else:
        new_version = (last[0] + 1) if last else 1

        cursor.execute("""
            INSERT INTO k8s_resources (
                cluster_name, namespace, resource_type, resource_name, resource_uid,
                version, version_int, collected_at, raw_json, pretty_json, labels, annotations, hash
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (
            cluster_name,
            namespace,
            resource_type,
            name,
            uid,
            version,
            new_version,
            datetime.now(),
            Json(resource_dict),
            pretty_json,
            Json(labels),
            Json(annotations),
            hash_val
        ))
        print(f"Inserted version {new_version} of {resource_type} '{name}' in '{namespace}'")

        if last:
            diff = get_diff(last[2], resource_dict)
            cursor.execute("""
                INSERT INTO resource_audit_logs (
                    cluster_name, namespace, resource_type, resource_name,
                    version_old, version_new, diff, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                cluster_name, namespace, resource_type, name,
                last[0], new_version, Json(diff), datetime.now()
            ))
            
    
    #iterable dict 
    data = resource_dict.get("data", {})
    if data:
        for k, v in data.items():
            cursor.execute("""
                INSERT INTO configmap_kv_pairs (
                    cluster_name, namespace, configmap_name, key, value, collected_at
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (cluster_name, namespace, configmap_name, key) 
                DO UPDATE SET
                    value = EXCLUDED.value,
                    collected_at = EXCLUDED.collected_at
            """, (
                cluster_name,
                namespace,
                name,
                k,
                v,
                datetime.now()
            ))
        print(f"Stored {len(data)} key-value pairs from ConfigMap '{name}' in namespace '{namespace}'")
    else:
        print(f"ConfigMap '{name}' in namespace '{namespace}' has no data.")





def insert_metadata(namespaces, cluster_name, conn, cursor):
    for n in namespaces.items:
        metadata = n.metadata
        name = metadata.name
        label = metadata.labels or None
        cluster_name = cluster_name  
        team = label.get("snappcloud.io/team") if label else None
        environment = label.get("environment") if label else None
        annotations = metadata.annotations or None
        uid = metadata.uid
        resource_version = metadata.resource_version
        creation_timestamp = str(metadata.creation_timestamp) if metadata.creation_timestamp else None
        self_link = getattr(metadata, "self_link", None)
        generate_name = metadata.generate_name or None
        owner_references = metadata.owner_references or None
        
        query = """
        INSERT INTO metadata (
            uid, name, cluster_name, labels, team, environment, annotations, resource_version,
            creation_timestamp, self_link, generate_name, owner_references
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (uid) DO UPDATE SET
            name = EXCLUDED.name,
            cluster_name = EXCLUDED.cluster_name,
            labels = EXCLUDED.labels,
            team = EXCLUDED.team,
            environment = EXCLUDED.environment,
            annotations = EXCLUDED.annotations,
            resource_version = EXCLUDED.resource_version,
            creation_timestamp = EXCLUDED.creation_timestamp,
            self_link = EXCLUDED.self_link,
            generate_name = EXCLUDED.generate_name,
            owner_references = EXCLUDED.owner_references
        """
        cursor.execute(query, (
            uid,
            name,
            cluster_name, 
            json.dumps(label) if label else None,  # Convert dict to JSON
            team,
            environment,
            json.dumps(annotations) if annotations else None,  # Convert dict to JSON
            resource_version,
            creation_timestamp,
            self_link,
            generate_name,
            json.dumps(owner_references) if owner_references else None  # Convert list to JSON
        ))
def get_resource_hash(resource_dict):
    """
    Compute a hash value for a given kubernetes resource dictionary.

    Args:
        resource_dict (dict): a dictionary representing a kubernetes resource

    Returns:
        str: a SHA-256 hash value of the resource dictionary
    """
    clean = json.dumps(resource_dict, sort_keys=True)
    return hashlib.sha256(clean.encode('utf-8')).hexdigest()
    