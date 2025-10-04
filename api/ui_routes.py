from fastapi import Request, APIRouter, Query, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pymongo.collection import Collection
from api import endpoints
from utils.db import get_resource_collection
from typing import Optional
import json
import re
import html

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
    Handles the UI search functionality by calling the shared query logic
    and adding highlighting to the results.
    """
    try:
        search_results = endpoints._query_resources(
            collection=collection,
            keyword=keyword,
            cluster_name=cluster_name,
            namespace=namespace,
            resource_type=resource_type,
            resource_name=resource_name
        )

        for result in search_results:
            # First, get the pretty-printed JSON data
            pretty_data = json.dumps(result.get('data', {}), indent=2)

            # Escape HTML characters to prevent XSS
            safe_data = html.escape(pretty_data)

            # If a keyword was used, highlight it
            if keyword:
                # Use re.sub for case-insensitive replacement and wrap with a span
                highlighted_data = re.sub(
                    f'({re.escape(keyword)})',
                    r'<span class="highlight">\1</span>',
                    safe_data,
                    flags=re.IGNORECASE
                )
                result['highlighted_data'] = highlighted_data
            else:
                result['highlighted_data'] = safe_data

            # Also keep the raw data for the ConfigMap view
            result['pretty_data'] = pretty_data

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