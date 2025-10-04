import os
import yaml
from pathlib import Path

# Path where ConfigMap with cluster definitions is mounted
CLUSTERS_CONFIG_PATH = os.environ.get(
    "CLUSTERS_CONFIG_PATH",
    "/etc/odin/clusters.yaml"
)

def load_clusters():
    """
    Loads cluster definitions from a YAML file and injects tokens from environment variables.
    Returns:
        list of dicts: Each dict contains name, api_server, token_env, and token.
    """
    try:
        clusters = yaml.safe_load(Path(CLUSTERS_CONFIG_PATH).read_text())
    except FileNotFoundError:
        raise RuntimeError(f"Cluster config file not found: {CLUSTERS_CONFIG_PATH}")

    if not isinstance(clusters, list):
        raise ValueError(f"Invalid cluster config format in {CLUSTERS_CONFIG_PATH}")

    for cluster in clusters:
        token_env = cluster.get("token_env")
        if not token_env:
            raise ValueError(f"Cluster {cluster.get('name')} is missing 'token_env' field")
        cluster["token"] = os.environ.get(token_env)
        if not cluster["token"]:
            raise RuntimeError(f"Token for {token_env} not found in environment variables")

    return clusters

# This is the variable your other code imports
CLUSTERS = load_clusters()