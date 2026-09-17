"""
穿搭推荐 Skill
根据天气温度输出穿搭建议（适配WeatherAPI）
"""
import httpx
from backend.utils.env_loader import get_weather_api_key

# 温度穿搭分级
WARDROBE_TIPS = {
    'hot': {
        'range': (30, 60),
        'advice': '🔥 炎热天气，建议穿短袖、短裤、裙子、凉鞋，注意防晒',
        'items': 'T恤、短裤、连衣裙、防晒衣、遮阳帽、墨镜、凉鞋',
    },
    'warm': {
        'range': (20, 29),
        'advice': '🌤 温暖舒适，单衣即可，可备薄外套',
        'items': '衬衫、薄T恤、牛仔裤、运动鞋、薄外套',
    },
    'mild': {
        'range': (10, 19),
        'advice': '🍂 微凉天气，建议长袖+外套',
        'items': '长袖T恤、卫衣、夹克、长裤、运动鞋',
    },
    'cool': {
        'range': (0, 9),
        'advice': '❄️ 寒冷天气，建议厚外套、毛衣',
        'items': '毛衣、厚外套、围巾、长裤、靴子',
    },
    'cold': {
        'range': (-100, -1),
        'advice': '🧊 严寒天气，建议羽绒服、保暖内衣',
        'items': '羽绒服、保暖内衣、毛线帽、手套、雪地靴',
    },
}


def _get_wardrobe_level(temp: float) -> dict:
    """根据温度获取穿搭推荐等级"""
    for level, config in WARDROBE_TIPS.items():
        low, high = config['range']
        if low <= temp <= high:
            return config
    return WARDROBE_TIPS['mild']


async def recommend_wardrobe(city: str) -> str:
    """
    根据目的地实时温度推荐穿搭

    参数:
        city: 城市名称

    返回:
        格式化的穿搭推荐文本
    """
    api_key = get_weather_api_key()
    if not api_key:
        return '错误：未配置 WeatherAPI Key'

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # WeatherAPI 实时天气接口，一步获取定位+实时温度
            params = {
                "key": api_key,
                "q": city,
                "aqi": "no"
            }
            resp = await client.get("https://api.weatherapi.com/v1/current.json", params=params)
            data = resp.json()

            # 接口鉴权/城市不存在判断
            if "error" in data:
                return f'天气查询失败：{data["error"]["message"]}'

            # 安全取值，避免KeyError
            location = data.get("location", {})
            current = data.get("current", {})
            temp = float(current.get("temp_c", 20))
            weather_text = current.get("condition", {}).get("text", "多云")
            city_name = location.get("name", city)

        wardrobe = _get_wardrobe_level(temp)
        return (
            f'🧳 {city_name} 穿搭推荐\n'
            f'  当前天气：{weather_text} | 温度：{temp}°C\n'
            f'  推荐：{wardrobe["advice"]}\n'
            f'  建议携带：{wardrobe["items"]}'
        )

    except httpx.HTTPError as e:
        return f"网络请求异常：{str(e)}"
    except Exception as e:
        return f"穿搭推荐服务异常：{str(e)}"