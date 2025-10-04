from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from pymongo.collection import Collection

from utils.db import get_resource_collection
from models.resource import Resource

router = APIRouter()

class ResourceOut(Resource):
    id: str = Field(alias="_id")

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

def fetch_unique_values(field: str, collection: Collection = Depends(get_resource_collection)) -> List[str]:
    """Fetches unique values for a given field from the resources collection."""
    return collection.distinct(field)

@router.get("/filters/cluster_names", response_model=List[str], summary="Get available Cluster Names")
def get_cluster_names(collection: Collection = Depends(get_resource_collection)):
    """
    Returns a list of all unique cluster names present in the database.
    """
    return fetch_unique_values("cluster_name", collection)

@router.get("/filters/namespaces", response_model=List[str], summary="Get available Namespaces")
def get_namespaces(collection: Collection = Depends(get_resource_collection)):
    """
    Returns a list of all unique namespace names present in the database.
    """
    return fetch_unique_values("namespace", collection)

@router.get("/filters/resource_types", response_model=List[str], summary="Get available Resource Types")
def get_resource_types(collection: Collection = Depends(get_resource_collection)):
    """
    Returns a list of all unique resource types (e.g., ConfigMap, Secret) present in the database.
    """
    return fetch_unique_values("resource_type", collection)

@router.get("/api/resources", response_model=List[ResourceOut], summary="List and search for Kubernetes resources")
def get_resources(
    collection: Collection = Depends(get_resource_collection),
    keyword: Optional[str] = Query(None, description="A keyword to search for in the resource name and its stringified data."),
    cluster_name: Optional[str] = Query(None, description="Filter results by cluster name."),
    namespace: Optional[str] = Query(None, description="Filter results by namespace."),
    resource_type: Optional[str] = Query(None, description="Filter results by resource type (e.g., Deployment)."),
    resource_name: Optional[str] = Query(None, description="Filter results by resource name (supports partial matching)."),
    skip: int = Query(0, description="The number of records to skip for pagination."),
    limit: int = Query(100, description="The maximum number of records to return."),
):
    """
    Provides a unified endpoint for listing and searching Kubernetes resources.

    - **Filtering**: You can filter resources by `cluster_name`, `namespace`, `resource_type`, and `resource_name`.
    - **Searching**: Use the `keyword` parameter to perform a case-insensitive search across the resource's name and its entire data content.
    - **Pagination**: Use `skip` and `limit` to paginate through the results.
    """
    query_parts = []

    if cluster_name:
        query_parts.append({"cluster_name": cluster_name})
    if namespace:
        query_parts.append({"namespace": namespace})
    if resource_type:
        query_parts.append({"resource_type": resource_type})
    if resource_name:
        name_regex = {"$regex": resource_name, "$options": "i"}
        query_parts.append({"resource_name": name_regex})

    if keyword:
        # Search against the new string field
        keyword_regex = {"$regex": keyword, "$options": "i"}
        query_parts.append({"full_resource_string": keyword_regex})

    query = {}
    if query_parts:
        query = {"$and": query_parts}

    cursor = collection.find(query).skip(skip).limit(limit)

    results = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        results.append(doc)
        
    return results

@router.get("/api/resources/{resource_id}", response_model=ResourceOut, summary="Inspect a single resource")
def get_resource(resource_id: str, collection: Collection = Depends(get_resource_collection)):
    """
    Retrieves a single resource by its unique MongoDB ID.
    """
    if not ObjectId.is_valid(resource_id):
        raise HTTPException(status_code=400, detail="Invalid resource ID format.")
        
    resource = collection.find_one({"_id": ObjectId(resource_id)})
    
    if resource:
        resource["_id"] = str(resource["_id"])
        return resource

    raise HTTPException(status_code=404, detail="Resource not found.")