from fastapi import Request, APIRouter, Query, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pymongo.collection import Collection
from api import endpoints
from utils.db import get_resource_collection
from typing import Optional
import json

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/", response_class=HTMLResponse, summary="Home page with search")
def home_page(request: Request):
    """
    Renders the main search page.
    """
    return templates.TemplateResponse(
        "search_results.html",
        {"request": request, "results": [], "total_matches": 0}
    )

@router.get("/search", response_class=HTMLResponse, summary="Search for resources")
def ui_search(
    request: Request,
    collection: Collection = Depends(get_resource_collection),
    keyword: Optional[str] = Query(None),
    cluster_name: Optional[str] = Query(None),
    namespace: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_name: Optional[str] = Query(None),
):
    """
    Handles the UI search functionality by calling the shared query logic.
    """
    try:
        # Call the shared query logic, which returns a list of dictionaries
        search_results = endpoints._query_resources(
            collection=collection,
            keyword=keyword,
            cluster_name=cluster_name,
            namespace=namespace,
            resource_type=resource_type,
            resource_name=resource_name
        )

        # The results are already dicts. Just add the pretty-printed data field for the template.
        for result in search_results:
            result['pretty_data'] = json.dumps(result.get('data', {}), indent=2)

        return templates.TemplateResponse(
            "search_results.html",
            {
                "request": request,
                "results": search_results,
                "total_matches": len(search_results),
                "keyword": keyword,
                "cluster_name": cluster_name,
                "namespace": namespace,
                "resource_type": resource_type,
                "resource_name": resource_name,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "search_results.html",
            {"request": request, "error": f"An unexpected error occurred: {e}", "results": [], "total_matches": 0}
        )