from fastapi import Request, APIRouter, Query, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from api import endpoints
from typing import Optional

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/", response_class=HTMLResponse, summary="Home page with search")
async def home_page(request: Request):
    """
    Renders the main search page.
    """
    return templates.TemplateResponse(
        "search_results.html",
        {"request": request, "results": [], "total_matches": 0}
    )

@router.get("/search", response_class=HTMLResponse, summary="Search for resources")
async def ui_search(
    request: Request,
    keyword: Optional[str] = Query(None),
    cluster_name: Optional[str] = Query(None),
    namespace: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_name: Optional[str] = Query(None),
):
    """
    Handles the UI search functionality by calling the new unified API endpoint.
    """
    try:
        # Call the refactored API endpoint
        search_results = await endpoints.get_resources(
            keyword=keyword,
            cluster_name=cluster_name,
            namespace=namespace,
            resource_type=resource_type,
            resource_name=resource_name
        )

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
    except HTTPException as e:
        return templates.TemplateResponse(
            "search_results.html",
            {"request": request, "error": e.detail, "results": [], "total_matches": 0}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "search_results.html",
            {"request": request, "error": f"An unexpected error occurred: {e}", "results": [], "total_matches": 0}
        )