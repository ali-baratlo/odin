from kubernetes import client, config
from utils.db import insert_metadata
from client import get_connection
from cluster_config import CLUSTERS

def metadata():
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

        #This method retrieves metadata about namespaces
        label_selector = "environment=production"
        namespaces = okdc.list_namespace(label_selector=label_selector)
        
        #The not operator checks if namespaces.items is "falsy." In Python, an empty list ([]) is considered falsy.
        if not namespaces.items:
            print(f"Error [{cluster_name}]: this cluster have not production namespace")
            return  
        
        '''Connect to database'''
        conn = get_connection()
        if conn is None:
            print("Could not connect to DB")
            return

        cursor = conn.cursor()
        
        insert_metadata(namespaces,
                        cluster_name=cluster_name,
                        conn=conn,
                        cursor=cursor)
        
        conn.commit()
        cursor.close()
        conn.close()    
    
        print("All data committed and connection closed.")