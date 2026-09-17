"""
天气预报 API 路由
查询指定城市的实时天气和多日预报
"""
from fastapi import APIRouter, Query
from backend.app.services.weather_service import get_weather_forecast

router = APIRouter(prefix='/api/weather', tags=['天气预报'])


@router.get('/forecast', summary='获取天气预报')
async def forecast_weather(
    city: str = Query(..., min_length=1, description='城市名称'),
    days: int = Query(3, ge=1, le=7, description='预报天数'),
):
    """
    查询指定城市的天气预报

    参数:
        city: 城市名称（支持中文，如"北京"）
        days: 预报天数，最多7天

    返回:
        格式化的天气信息
    """
    result = await get_weather_forecast(city, days)
    #return {'city': city, 'days': days, 'forecast': result}
    resp_data = {'city': city, 'days': days, 'forecast': result}
    # print removed
    return resp_data

