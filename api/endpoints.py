import json
import re
from typing import Optional, List, Literal, Any, TypeAlias
from fastapi import APIRouter, Query, HTTPException, status , Depends
from pydantic import BaseModel, Field
from client import get_connection


router = APIRouter()

def fetch_unique_values(column_name: str) -> List[str]:
    conn = get_connection()
    if not conn:
        return []

    try:
        with conn.cursor() as cur:
            query = f"SELECT DISTINCT {column_name} FROM k8s_resources ORDER BY {column_name};" # Added ORDER BY for consistent lists
            cur.execute(query)
            result = [row[0] for row in cur.fetchall()]
        return result
    except Exception as e:
        print(f"Error fetching unique values for {column_name}: {e}")
        return []
    finally:
        if conn:
            conn.close()

@router.get("/filters/cluster_names", response_model=List[str], summary="Get available Cluster Names")
def get_cluster_names():
    return fetch_unique_values("cluster_name")

@router.get("/filters/namespaces", response_model=List[str], summary="Get available Namespaces")
def get_namespaces():
    return fetch_unique_values("namespace")

@router.get("/filters/resource_types", response_model=List[str], summary="Get available Resource Types")
def get_resource_types():
    return fetch_unique_values("resource_type")

# --- Type Aliases (for clarity in function signatures) ---
# These are just descriptive names for the 'str' type.
# Literal types are used here if you have a fixed, predefined set of allowed values.
# If these should be dynamically fetched from the DB, use 'str' instead of 'Literal'.
# For 'Namespace', it's problematic to use Literal with a runtime function call,
# so we'll use 'str' for flexibility in the search endpoint.
ClusterName: TypeAlias = Literal["Teh1", "Teh2", "all"] # Example fixed values
ResourceType: TypeAlias = Literal["configmap", "all"] # Example fixed values
Namespace: TypeAlias = str # Use str for dynamic namespaces to avoid import-time DB issues

# --- Pydantic Models for API Response Structure ---
class LineMatch(BaseModel):
    line_number: int = Field(..., description="The line number where the keyword was found.")
    highlighted_text: str = Field(..., description="The full line of text with the keyword highlighted (includes HTML tags).")

class ResourceMatch(BaseModel):
    cluster_name: str = Field(..., description="The name of the Kubernetes/OKD cluster.")
    namespace: str = Field(..., description="The namespace of the resource.")
    resource_type: str = Field(..., description="The type of the resource (e.g., Deployment, Pod).")
    resource_name: str = Field(..., description="The name of the resource.")
    matched_lines: List[LineMatch] = Field(..., description="A list of lines where the keyword was found, with HTML highlighting.")

class SearchResponse(BaseModel):
    total_matches: int = Field(..., description="The total number of resources found containing the keyword.")
    results: List[ResourceMatch] = Field(..., description="A list of matching resources.")

# --- Main Search API Endpoint ---
@router.get(
    "/api/search",
    response_model=SearchResponse,
    summary="Search Kubernetes/OKD Resources (JSON API)",
    description="This API allows searching Kubernetes/OKD resources by cluster name, namespace, resource type, and resource name, and also searches for a keyword within the raw JSON content of the resources. Returns JSON data with highlighted lines."
)
def search_configmap_kv_pairs_api(
    cluster_name: ClusterName = Query(...),
    namespace: Namespace = Query(...),
    resource_name: Optional[str] = Query(None),
    keyword: str = Query(...)
):
    conn = get_connection()
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database connection failed. Please try again later."
        )

    try:
        with conn.cursor() as cur:
            query = """
                SELECT cluster_name, namespace, configmap_name, key, value
                FROM configmap_kv_pairs
                WHERE 1=1
            """
            values = []

            if cluster_name != "all":
                query += " AND cluster_name = %s"
                values.append(cluster_name)

            if namespace != "all":
                query += " AND namespace = %s"
                values.append(namespace)

            if resource_name:
                query += " AND configmap_name ILIKE %s"
                values.append(f"%{resource_name}%")

            if keyword:
                query += " AND (key ILIKE %s OR value ILIKE %s)"
                values.append(f"%{keyword}%")
                values.append(f"%{keyword}%")

            cur.execute(query, values)
            rows = cur.fetchall()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database query failed: {e}"
        )
    finally:
        if conn:
            conn.close()

    def highlight(text: str, keyword: str) -> str:
        return re.sub(
            re.escape(keyword),
            lambda match: f'<span class="highlight">{match.group(0)}</span>',
            text,
            flags=re.IGNORECASE
        )
        #pattern,replacment,text,flags

    results = []
        
    grouped = {}
    for i, (cluster, ns, cm_name, k, v) in enumerate(rows):
        key_line = f'"{k}": "{v}"'
        highlighted_line = highlight(key_line, keyword)
        line_match = LineMatch(line_number=i + 1, highlighted_text=highlighted_line)

        key = (cluster, ns, cm_name)
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(line_match)

    for (cluster, ns, cm_name), matches in grouped.items():
        pretty_json = json.dumps(
            {match.highlighted_text.split(":")[0].strip('"'): match.highlighted_text.split(":")[1].strip().strip('"') for match in matches},
            indent=2,
            ensure_ascii=False
        )
        results.append(ResourceMatch(
            cluster_name=cluster,
            namespace=ns,
            resource_type="ConfigMap",
            resource_name=cm_name,
            pretty_json=pretty_json,
            matched_lines=matches
        ))

    return SearchResponse(total_matches=len(results), results=results)




#----laklak endpoint-----

class TeamResponse(BaseModel):
    name: str
    cluster_name: str
    team: Optional[str] = None
    msg: Optional[str] = None
    
conn = get_connection()
@router.post("/namespace/team", response_model=TeamResponse)
def get_namespace_team(name: str, cluster_name: str, ):
    
    conn = get_connection()
    cur=conn.cursor()
    query = """
    SELECT team
    FROM metadata
    WHERE name = %s AND cluster_name = %s
    """
    try:
        cur.execute(query, (name, cluster_name))
        row = cur.fetchone()
        if row is None:
            raise HTTPException(
                status_code=404,
                detail=f"Namespace '{name}' not found in cluster '{cluster_name}'"
            )
        return TeamResponse(
            name=name,
            cluster_name=cluster_name,
            team=row[0],
            msg="just for you dears ashkan & alireza , odin love you guys!"
        )
        
    except conn.Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    finally:
        if conn:
            conn.close()

