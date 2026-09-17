"""天气预报 Skill"""
import httpx
from backend.utils.env_loader import get_weather_api_key

WEATHER_BASE = "https://api.weatherapi.com/v1"

# 天气状况中文翻译
WEATHER_CN = {
    "Sunny": "晴", "Clear": "晴", "晴朗": "晴",
    "Partly cloudy": "多云", "Partly Cloudy": "多云", "Cloudy": "多云",
    "Overcast": "阴",
    "Mist": "薄雾", "Fog": "雾",
    "Light rain": "小雨", "Moderate rain": "中雨", "Heavy rain": "大雨",
    "Patchy rain possible": "零星小雨", "Patchy light rain": "零星小雨",
    "Light drizzle": "毛毛雨", "Drizzle": "毛毛雨",
    "Thundery outbreaks possible": "雷阵雨", "Thundery outbreaks in nearby": "附近雷阵雨",
    "Patchy light rain with thunder": "雷阵雨", "Moderate or heavy rain with thunder": "雷暴雨",
    "Light snow": "小雪", "Moderate snow": "中雪", "Heavy snow": "大雪",
    "Blizzard": "暴风雪", "Patchy snow possible": "零星小雪",
    "Ice pellets": "冰雹", "Sleet": "冻雨",
    "Haze": "霾", "Smoke": "烟霾",
    "Foggy": "浓雾", "Windy": "大风", "Breezy": "微风",
    "Hot": "炎热", "Cold": "寒冷",
}

# 风向中文翻译（16方位 + 英文全称）
WIND_DIR_CN = {
    "N": "北风", "NNE": "东北偏北", "NE": "东北风", "ENE": "东北偏东",
    "E": "东风", "ESE": "东南偏东", "SE": "东南风", "SSE": "东南偏南",
    "S": "南风", "SSW": "西南偏南", "SW": "西南风", "WSW": "西南偏西",
    "W": "西风", "WNW": "西北偏西", "NW": "西北风", "NNW": "西北偏北",
    "North": "北风", "Northeast": "东北风", "East": "东风", "Southeast": "东南风",
    "South": "南风", "Southwest": "西南风", "West": "西风", "Northwest": "西北风",
}

_CITY_EN_MAP = {
    "北京": "Beijing", "上海": "Shanghai", "广州": "Guangzhou",
    "深圳": "Shenzhen", "成都": "Chengdu", "杭州": "Hangzhou",
    "武汉": "Wuhan", "西安": "Xi'an", "重庆": "Chongqing",
    "南京": "Nanjing", "苏州": "Suzhou", "天津": "Tianjin",
    "长沙": "Changsha", "郑州": "Zhengzhou", "青岛": "Qingdao",
    "大连": "Dalian", "厦门": "Xiamen", "昆明": "Kunming",
    "沈阳": "Shenyang", "哈尔滨": "Harbin", "济南": "Jinan",
    "福州": "Fuzhou", "合肥": "Hefei", "海口": "Haikou",
    "三亚": "Sanya", "桂林": "Guilin", "丽江": "Lijiang",
    "拉萨": "Lhasa", "乌鲁木齐": "Urumqi", "贵阳": "Guiyang",
    "南宁": "Nanning", "太原": "Taiyuan", "南昌": "Nanchang",
    "长春": "Changchun", "呼和浩特": "Hohhot", "兰州": "Lanzhou",
    "西宁": "Xining", "银川": "Yinchuan", "石家庄": "Shijiazhuang",
    "香港": "Hong Kong", "澳门": "Macau", "台北": "Taipei",
    "东京": "Tokyo", "大阪": "Osaka", "京都": "Kyoto",
    "首尔": "Seoul", "曼谷": "Bangkok", "巴黎": "Paris",
    "伦敦": "London", "纽约": "New York", "洛杉矶": "Los Angeles",
    "悉尼": "Sydney", "新加坡": "Singapore",
    "富士山": "Mount Fuji", "富士": "Mount Fuji",
}


async def get_weather_forecast(city: str, days: int = 3) -> str:
    api_key = get_weather_api_key()
    if not api_key:
        return "错误：未配置 WeatherAPI Key"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            city_en = _CITY_EN_MAP.get(city, city)

            search_resp = await client.get(
                f"{WEATHER_BASE}/search.json",
                params={"key": api_key, "q": city_en}
            )
            search_data = search_resp.json()

            q_param = city_en
            city_display = city
            if isinstance(search_data, list) and len(search_data) > 0:
                matched = [s for s in search_data
                           if city.lower() in s.get("name", "").lower()
                           or city_en.lower() in s.get("name", "").lower()]
                target = matched[0] if matched else search_data[0]
                q_param = target.get("url") or target.get("name", city_en)
                city_display = target.get("name", city)

            params = {
                "key": api_key,
                "q": q_param,
                "days": days,
                "aqi": "no"
            }
            resp = await client.get(f"{WEATHER_BASE}/forecast.json", params=params)
            data = resp.json()

            if "error" in data:
                return f'天气查询失败：{data["error"]["message"]}'

            forecast_list = data["forecast"]["forecastday"]
            result = [f"📍 {city_display}天气预报："]
            for day in forecast_list[:days]:
                d = day["day"]
                date = day["date"]
                cond_en = d.get("condition", {}).get("text", "")
                cond = WEATHER_CN.get(cond_en, cond_en or "未知")
                low = d.get("mintemp_c", "?")
                high = d.get("maxtemp_c", "?")
                maxwind_kph = d.get("maxwind_kph", 0)

                hours = day.get("hour", [])
                wind_dir = ""
                wind_kph = maxwind_kph
                if hours:
                    for h in hours:
                        t = h.get("time", "")
                        if "12:00" in t or "13:00" in t or "14:00" in t:
                            wind_dir = h.get("wind_dir", "") or ""
                            wind_kph = h.get("wind_kph", wind_kph) or wind_kph
                            break
                    if not wind_dir:
                        for h in hours:
                            wind_dir = h.get("wind_dir", "") or ""
                            if wind_dir:
                                wind_kph = h.get("wind_kph", wind_kph) or wind_kph
                                break

                wind_part = ""
                if wind_dir:
                    wind_part = f" {WIND_DIR_CN.get(wind_dir, wind_dir)}"
                if wind_kph:
                    wind_part += f" {wind_kph}km/h"
                if not wind_part:
                    wind_part = " 无风数据"

                line = f"  📅 {date} {cond} 🌡 {low}~{high}°C 💨{wind_part}"
                result.append(line)

            final_text = "\n".join(result)
            return final_text

    except Exception as e:
        return f"天气服务异常：{str(e)}"
