"""
穿搭推荐 API 路由
根据目的地天气自动推荐穿搭
"""
from fastapi import APIRouter, Query
from backend.app.services.wardrobe_recommend import recommend_wardrobe

router = APIRouter(prefix="/api/wardrobe", tags=["穿搭推荐"])


@router.get("/recommend", summary="穿搭推荐")
async def wardrobe_recommend(
    city: str = Query(..., min_length=1, description="城市名称"),
):
    result = await recommend_wardrobe(city)
    return {"city": city, "recommendation": result}
