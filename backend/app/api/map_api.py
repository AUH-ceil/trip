"""
景点地图检索 API 路由
支持景点搜索和地图坐标数据返回
"""
from fastapi import APIRouter, Query
from backend.app.services.map_service import search_pois, search_pois_structured

router = APIRouter(prefix="/api/map", tags=["景点检索"])


@router.get("/search", summary="搜索景点（文本）")
async def search_attractions(
    city: str = Query(..., min_length=1, description="城市名称"),
    keyword: str = Query("热门景点", description="搜索关键词"),
    page_size: int = Query(10, ge=1, le=20, description="返回结果数量"),
):
    """搜索景点并返回格式化文本描述"""
    result = await search_pois(keyword, city, page_size)
    return {"city": city, "keyword": keyword, "results": result}


@router.get("/places", summary="搜索景点（结构化数据，含坐标）")
async def search_places(
    city: str = Query(..., min_length=1, description="城市名称"),
    keyword: str = Query("热门景点", description="搜索关键词"),
    page_size: int = Query(10, ge=1, le=20, description="返回结果数量"),
):
    """搜索景点并返回结构化 JSON 数据（含经纬度坐标），供前端地图渲染"""
    pois = await search_pois_structured(keyword, city, page_size)
    return {
        "city": city,
        "keyword": keyword,
        "places": pois,
    }
@router.get("/generate", summary="生成景点地图 HTML")
async def generate_map(
    city: str = Query(..., min_length=1, description="城市名称"),
    keyword: str = Query("热门景点", description="搜索关键词"),
    page_size: int = Query(10, ge=1, le=20, description="返回结果数量"),
):
    """
    使用大模型生成可交互的景点地图 HTML 页面
    返回完整的 HTML 字符串，可直接在浏览器中渲染
    """
    from backend.app.services.map_service import generate_map_html

    html = await generate_map_html(keyword, city, page_size)
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=html, status_code=200, media_type="text/html; charset=utf-8")
