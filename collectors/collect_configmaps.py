from kubernetes import client, config
from utils.db import insert_resources
from client import get_connection
from cluster_config import CLUSTERS

def collect_configmaps():
    """
    Collects ConfigMaps from the 'production' namespaces in the OKD cluster and inserts them into the database.

    This function connects to the specified OKD cluster using the provided kubeconfig, selects namespaces labeled
    as 'production', and retrieves ConfigMaps from these namespaces. The collected ConfigMaps are then inserted
    into a database.

    If no production namespaces are found or if there is an issue connecting to the database, an error message is printed,
    and the function exits.

    Raises:
        Prints error messages if production namespaces are not found or if database connection fails.

    """
    
    '''first we need to load kubeconfig and connect to the cluster'''
    
    for cluster in CLUSTERS:
        cluster_name = cluster["name"]
        #kubeconfig_path = cluster["kubeconfig"]
        #cluster_context = cluster["context"]
        api_server =cluster["api_server"]
        token = cluster["token"]
        
        print(f"\n Collecting from {cluster_name}")
        
        #ca_cert_path = "/path/to/ca.crt"           
        configuration = client.Configuration()
        configuration.host = api_server
        configuration.verify_ssl = False
        #configuration.ssl_ca_cert = ca_cert_path
        configuration.api_key = {"authorization": f"Bearer {token}"}
        
        client.Configuration.set_default(configuration)
        
        okdc = client.CoreV1Api()

        label_selector = cluster.get("label_selector", "")
        namespaces = okdc.list_namespace(label_selector=label_selector)
        if not namespaces.items:
            print(f"Error [{cluster_name}]: this cluster have not production namespace")
            return  

        '''Connect to database'''   
        conn = get_connection()
        if conn is None:
            print("Could not connect to DB")
            return

        cursor = conn.cursor()

        for n in namespaces.items:
            #print(n.metadata.name)
            namespaces_name = n.metadata.name
            configmaps = okdc.list_namespaced_config_map(namespace=namespaces_name)
            if not configmaps.items:
                print(f"Error [{cluster_name}]: this namespace have not configmaps")
                return
            else:
                '''we need to get the configmaps from the production environment'''
                for cm in configmaps.items:
                    
                    #insert configmap into database
                      
                    insert_resources(cm ,
                                     cluster_name=cluster_name ,
                                     resource_type="configmap" ,
                                     conn=conn,
                                     cursor=cursor)

        conn.commit()
        cursor.close()
        conn.close()    
    
        print("All data committed and connection closed.")
    