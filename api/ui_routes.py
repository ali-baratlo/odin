from fastapi import Request, APIRouter, Query, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pymongo.collection import Collection
from api import endpoints
from utils.db import get_resource_collection
from utils.presenter import get_structured_data
from typing import Optional, Any, List, Dict
import json
import re
import html

templates = Jinja2Templates(directory="templates")
router = APIRouter()

def highlight_text(text: str, keyword: str) -> str:
    """Safely escapes and highlights a keyword in a string of text."""
    if not keyword or not text:
        return html.escape(text)

    safe_text = html.escape(text)
    return re.sub(
        f'({re.escape(keyword)})',
        r'<span class="highlight">\1</span>',
        safe_text,
        flags=re.IGNORECASE
    )

def create_snippets(text: str, keyword: str, context_lines: int = 2) -> List[Dict[str, Any]]:
    """
    Creates a single, continuous list of contextual snippets from a block of text.
    """
    lines = text.splitlines()
    line_indices_to_show = set()

    # Find all lines containing the keyword and add their context to a set
    for i, line in enumerate(lines):
        if keyword.lower() in line.lower():
            start = max(0, i - context_lines)
            end = min(len(lines), i + context_lines + 1)
            for j in range(start, end):
                line_indices_to_show.add(j)

    # Build the snippets from the sorted, unique indices
    snippets = []
    sorted_indices = sorted(list(line_indices_to_show))
    for index in sorted_indices:
        snippets.append({
            "line_number": index + 1,
            "line_text": highlight_text(lines[index], keyword)
        })

    return snippets

@router.get("/", response_class=HTMLResponse, summary="Home page with search")
def home_page(request: Request):
    """Renders the main search page."""
    return templates.TemplateResponse("search_results.html", {"request": request, "results": [], "total_matches": 0})

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
    and preparing data for presentation, including contextual snippets for ConfigMaps.
    """
    try:
        search_results = endpoints._query_resources(collection=collection, keyword=keyword, cluster_name=cluster_name, namespace=namespace, resource_type=resource_type, resource_name=resource_name, limit=limit)

        for result in search_results:
            structured_data = get_structured_data(result)

            if result.get('resource_type') == 'ConfigMap' and keyword:
                filtered_data = {}
                if isinstance(structured_data, dict):
                    for key, value in structured_data.items():
                        if keyword.lower() in key.lower() or (isinstance(value, str) and keyword.lower() in value.lower()):
                            highlighted_key = highlight_text(key, keyword)
                            if isinstance(value, str) and '\n' in value:
                                filtered_data[highlighted_key] = create_snippets(value, keyword)
                            else:
                                filtered_data[highlighted_key] = highlight_text(str(value), keyword)
                result['structured_data'] = filtered_data
                result['is_configmap_search'] = True
            else:
                result['structured_data'] = highlight_recursive(structured_data, keyword) if keyword else structured_data
                result['is_configmap_search'] = False

            pretty_data = json.dumps(result.get('data', {}), indent=2)
            result['highlighted_data'] = highlight_text(pretty_data, keyword)

        return templates.TemplateResponse("search_results.html", {"request": request, "results": search_results, "total_matches": len(search_results), "keyword": keyword, "cluster_name": cluster_name, "namespace": namespace, "resource_type": resource_type, "resource_name": resource_name, "limit": limit})
    except Exception as e:
        return templates.TemplateResponse("search_results.html", {"request": request, "error": f"An unexpected error occurred: {e}", "results": [], "total_matches": 0})

def highlight_recursive(data: Any, keyword: str) -> Any:
    """Helper function to highlight keywords in nested data structures."""
    if isinstance(data, dict):
        return {key: highlight_recursive(value, keyword) for key, value in data.items()}
    if isinstance(data, list):
        return [highlight_recursive(item, keyword) for item in data]
    if isinstance(data, str):
        return highlight_text(data, keyword)
    return data