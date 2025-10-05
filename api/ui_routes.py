from fastapi import Request, APIRouter, Query, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pymongo.collection import Collection
from api import endpoints
from utils.db import get_resource_collection
from utils.presenter import get_structured_data
from typing import Optional, Any
import json
import re
import html

templates = Jinja2Templates(directory="templates")
router = APIRouter()

def highlight_recursive(data: Any, keyword: str) -> Any:
    """
    Recursively traverses a data structure (dict, list) and highlights
    all string values that contain the keyword.
    """
    if not keyword:
        return data

    if isinstance(data, dict):
        return {key: highlight_recursive(value, keyword) for key, value in data.items()}

    if isinstance(data, list):
        return [highlight_recursive(item, keyword) for item in data]

    if isinstance(data, str):
        safe_str = html.escape(data)
        return re.sub(
            f'({re.escape(keyword)})',
            r'<span class="highlight">\1</span>',
            safe_str,
            flags=re.IGNORECASE
        )

    return data

@router.get("/", response_class=HTMLResponse, summary="Home page with search")
def home_page(request: Request):
    """Renders the main search page."""
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
    limit: int = Query(100, description="Maximum number of results to return"),
):
    """
    Handles the UI search functionality by calling the shared query logic
    and preparing data for presentation with highlighting.
    """
    try:
        search_results = endpoints._query_resources(
            collection=collection,
            keyword=keyword,
            cluster_name=cluster_name,
            namespace=namespace,
            resource_type=resource_type,
            resource_name=resource_name,
            limit=limit
        )

        for result in search_results:
            structured_data = get_structured_data(result)

            # For ConfigMaps, only show matching key/value pairs in the summary
            if result.get('resource_type') == 'ConfigMap' and keyword:
                filtered_data = {}
                if isinstance(structured_data, dict):
                    for key, value in structured_data.items():
                        if keyword.lower() in key.lower() or keyword.lower() in str(value).lower():
                            filtered_data[key] = value
                result['structured_data'] = highlight_recursive(filtered_data, keyword)
            else:
                result['structured_data'] = highlight_recursive(structured_data, keyword)

            # Generate highlighted data for the "Raw Data" view
            pretty_data = json.dumps(result.get('data', {}), indent=2)
            safe_data = html.escape(pretty_data)

            if keyword:
                result['highlighted_data'] = re.sub(
                    f'({re.escape(keyword)})',
                    r'<span class="highlight">\1</span>',
                    safe_data,
                    flags=re.IGNORECASE
                )
            else:
                result['highlighted_data'] = safe_data

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
                "limit": limit,
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "search_results.html",
            {"request": request, "error": f"An unexpected error occurred: {e}", "results": [], "total_matches": 0}
        )