from fastapi import Request , APIRouter , Query  ,HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from api import endpoints
from typing import Optional


templates = Jinja2Templates(directory="templates")
router = APIRouter()

#I/O blocking protected with async :)
@router.get("/",response_class=HTMLResponse, summary="Lets dive into any cluster") # type: ignore
async def home_page(request : Request):
    return templates.TemplateResponse(
        "search_results.html",
        {"request": request, "results": [], "total_matches": 0, "keyword": ""}
    )

@router.get("/search" , response_class=HTMLResponse , summary="search on resources")
async def master_search(
    request : Request,
    cluster_name: endpoints.ClusterName=Query(...),
    namespace : endpoints.Namespace=Query(...),
    resource_name: Optional[str]=Query(None),
    keyword: str = Query(...)
) :
    try:
        search_response = endpoints.search_configmap_kv_pairs_api(
            cluster_name=cluster_name,
            namespace=namespace,
            resource_name=resource_name,
            keyword=keyword
        )
        return templates.TemplateResponse(
            "search_results.html",
            {
                "request": request,
                "results": search_response.results,
                "total_matches": search_response.total_matches,
                "keyword": keyword
            }
        )
    except HTTPException as e:
        return templates.TemplateResponse(
            "search_results.html",
            {"request": request, "error": e.detail, "results": [], "total_matches": 0, "keyword": keyword}
        )
    except Exception as e:
        return templates.TemplateResponse(
            "search_results.html",
            {"request": request, "error": f"An unexpected error occurred: {e}", "results": [], "total_matches": 0, "keyword": keyword}

        )