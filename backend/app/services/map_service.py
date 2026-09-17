"""
景点/地点检索 Skill
使用 DeepSeek LLM 生成景点数据（含坐标、描述、推荐理由）
同时兼容高德 API 作为坐标回退补充
"""
import json
import httpx
from langchain_openai import ChatOpenAI
from backend.utils.env_loader import get_deepseek_api_key, get_gaode_api_key

# 高德 API 仅用于补充坐标（当 LLM 返回的坐标不可用时）
GAODE_BASE = "https://restapi.amap.com/v3"


def _init_llm() -> ChatOpenAI:
    api_key = get_deepseek_api_key()
    return ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=api_key,
        openai_api_base="https://api.deepseek.com/v1",
        temperature=0.3,
        max_tokens=2048,
    )


async def search_pois(keyword: str, city: str = "", page_size: int = 5) -> str:
    """
    使用大模型搜索指定地点的景点/地点信息

    参数:
        keyword: 搜索关键词（如 "富士山", "故宫"）
        city: 城市名称（可选）
        page_size: 返回结果数量

    返回:
        格式化地点信息字符串
    """
    api_key = get_deepseek_api_key()
    if not api_key:
        return "错误：未配置 DeepSeek API Key"

    try:
        llm = _init_llm()

        city_part = f"位于 {city}" if city else ""
        prompt = f"""你是一个精确的景点检索助手。用户可能搜索**具体景点名称**或**类别**。

规则：
1. 如果关键词是**具体景点/地点名称**（如故宫、富士山、埃菲尔铁塔、天安门），**只返回该地点本身**（最多1个结果），不要附加任何其他无关景点
2. 如果关键词是**类别**（如热门景点、自然风光、美食、购物），返回该类别下最热门的{page_size}个地点
3. 如果既有具体名字又有类别含义，以具体名字为准

当前搜索关键词："{keyword}"
城市：{city_part or "不限"}

请严格按照以下 JSON 格式返回（只返回 JSON 数组）：
[
  {{
    "name": "景点名称",
    "address": "详细地址",
    "lat": 纬度数字,
    "lng": 经度数字,
    "description": "简要介绍（20字以内）",
    "type": "景点/餐饮/购物/住宿",
    "rating": 评分(1-5)
  }}
]"""

        messages = [
            {"role": "system", "content": "你是一个精确的景点检索助手，只返回符合搜索关键词的准确结果，不会编造不相关的景点。"},
            {"role": "user", "content": prompt}
        ]

        resp = await llm.ainvoke(messages)
        raw_content = resp.content if hasattr(resp, "content") else str(resp)

        # 提取 JSON 数组
        json_str = raw_content.strip()
        # 如果 LLM 在代码块中返回 JSON
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        pois = json.loads(json_str)
        if not isinstance(pois, list):
            pois = [pois]

        # 尝试高德 API 补充/校正坐标
        gaode_key = get_gaode_api_key()
        if gaode_key:
            for poi in pois:
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        gao_params = {
                            "key": gaode_key,
                            "keywords": poi.get("name", ""),
                            "city": city,
                            "offset": 1,
                            "output": "JSON",
                        }
                        gao_resp = await client.get(
                            f"{GAODE_BASE}/place/text", params=gao_params
                        )
                        gao_data = gao_resp.json()
                        if gao_data.get("status") == "1" and gao_data.get("pois"):
                            p = gao_data["pois"][0]
                            loc = p.get("location", "")
                            if loc and "," in loc:
                                lng, lat = loc.split(",")
                                poi["lng"] = float(lng)
                                poi["lat"] = float(lat)
                            if not poi.get("address"):
                                poi["address"] = p.get("address", "")
                except Exception:
                    pass  # 高德补充失败不影响 LLM 结果

        result_lines = [f"🔍 {city} 搜索「{keyword}」结果："]
        for poi in pois[:page_size]:
            name = poi.get("name", "未知")
            address = poi.get("address", "暂无地址")
            lat = poi.get("lat", "")
            lng = poi.get("lng", "")
            desc = poi.get("description", "")
            rating = poi.get("rating", "")
            poi_type = poi.get("type", "")

            loc_str = f"{lng},{lat}" if lng and lat else ""
            result_lines.append(f"  🏷 {name}")
            if desc:
                result_lines.append(f"     📝 {desc}")
            result_lines.append(f"     地址：{address} | 坐标：{loc_str}")
            if rating:
                result_lines.append(f"     ⭐ 评分：{rating}")
            if poi_type:
                result_lines.append(f"     类型：{poi_type}")

        return "\n".join(result_lines)

    except json.JSONDecodeError as e:
        return f"景点数据解析失败：{str(e)}，原始返回：{raw_content[:200]}"
    except Exception as e:
        return f"景点检索异常：{str(e)}"


async def search_pois_structured(
    keyword: str, city: str = "", page_size: int = 5
) -> list:
    """
    返回结构化景点数据（含JSON坐标），供前端地图渲染使用

    参数:
        keyword: 搜索关键词
        city: 城市名称
        page_size: 返回数量

    返回:
        list[dict]: 每个景点包含 name, address, lat, lng, description, type, rating
    """
    api_key = get_deepseek_api_key()
    if not api_key:
        return []

    try:
        llm = _init_llm()
        city_part = f"位于 {city}" if city else ""

        prompt = f"""你是一个精确的景点检索助手。用户可能搜索**具体景点名称**（如"故宫""富士山""埃菲尔铁塔"）或**类别**（如"热门景点""美食"）。

规则：
1. 如果关键词是**具体景点/地点名称**（如故宫、富士山、埃菲尔铁塔、天安门），**只返回该地点本身**（最多1个结果），不要附加任何其他景点
2. 如果关键词是**类别**（如热门景点、自然风光、美食、购物），可以返回该类别下最热门的多个结果
3. 如果关键词既有具体名字又有类别含义，以具体名字为准，只返回该地点

当前搜索关键词："{keyword}"
城市：{city_part or "不限"}

请严格按照以下 JSON 格式返回（只返回 JSON 数组）：
[
  {{
    "name": "景点名称",
    "address": "详细地址",
    "lat": 纬度数字,
    "lng": 经度数字,
    "description": "简要介绍（20字以内）",
    "type": "景点/餐饮/购物/住宿",
    "rating": 评分数字(1-5)
  }}
]"""

        messages = [
            {"role": "system", "content": "你是一个精确的景点检索助手。"},
            {"role": "user", "content": prompt}
        ]

        resp = await llm.ainvoke(messages)
        raw_content = resp.content if hasattr(resp, "content") else str(resp)

        json_str = raw_content.strip()
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()

        pois = json.loads(json_str)
        if not isinstance(pois, list):
            pois = [pois]

        # 用高德 API 校正坐标
        gaode_key = get_gaode_api_key()
        if gaode_key:
            for poi in pois:
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        gao_params = {
                            "key": gaode_key,
                            "keywords": poi.get("name", ""),
                            "city": city,
                            "offset": 1,
                            "output": "JSON",
                        }
                        gao_resp = await client.get(
                            f"{GAODE_BASE}/place/text", params=gao_params
                        )
                        gao_data = gao_resp.json()
                        if gao_data.get("status") == "1" and gao_data.get("pois"):
                            p = gao_data["pois"][0]
                            loc = p.get("location", "")
                            if loc and "," in loc:
                                lng, lat = loc.split(",")
                                poi["lng"] = float(lng)
                                poi["lat"] = float(lat)
                except Exception:
                    pass

        return pois[:page_size]

    except Exception as e:
        # print removed
        return []


async def generate_map_html(keyword: str, city: str = "", page_size: int = 10) -> str:
    """使用大模型生成包含景点地图的完整 HTML 页面"""
    pois = await search_pois_structured(keyword, city, page_size)
    if not pois:
        return "<div style='padding:40px;text-align:center;color:#94a3b8;font-size:16px;'>\\U0001f50d 未找到相关景点</div>"

    import json as _json
    pois_json = _json.dumps(pois, ensure_ascii=False, indent=2)

    api_key = get_deepseek_api_key()
    if not api_key:
        return _build_fallback_map(pois)

    try:
        llm = _init_llm()

    
        pois_json_str = _json.dumps(pois, ensure_ascii=False, indent=2)
        prompt_parts = []
        prompt_parts.append("你是一个 HTML/CSS/JS 地图制作专家。请根据以下景点数据，生成一个完整可直接运行的 HTML 页面，包含交互式地图。")
        prompt_parts.append("")
        prompt_parts.append("要求：")
        prompt_parts.append("1. 使用 Leaflet.js（CDN: unpkg.com/leaflet@1.9.4）")
        prompt_parts.append("2. 地图瓦片使用 OpenStreetMap")
        prompt_parts.append("3. 在地图上为每个景点添加 Marker 标记，点击弹出信息窗（名称、描述、评分）")
        prompt_parts.append("4. 自动调整地图视野（fitBounds）以显示所有标记")
        prompt_parts.append("5. 页面整体风格：干净、现代、中文界面")
        prompt_parts.append("6. 添加一个景点列表面板，点击列表项可在地图上高亮对应标记")
        prompt_parts.append("7. 地图容器宽 100%，高 500px")
        prompt_parts.append(f"8. 页面标题格式为：{city} {keyword} 景点地图")
        prompt_parts.append("9. 纯前端，不需要后端接口")
        prompt_parts.append("10. 在页面底部加一行小字：数据来源：AI 生成，仅供参考")
        prompt_parts.append("")
        prompt_parts.append("景点数据（JSON）：")
        prompt_parts.append(pois_json_str)
        prompt_parts.append("")
        prompt_parts.append("请直接输出完整的 HTML 代码（不要用 markdown 代码块包裹）。")
        prompt = "\n".join(prompt_parts)


        messages = [
            {"role": "system", "content": "你是一个 HTML/地图专家，只输出可直接运行的 HTML 代码。"},
            {"role": "user", "content": prompt}
        ]

        resp = await llm.ainvoke(messages)
        html = resp.content if hasattr(resp, "content") else str(resp)

        html = html.strip()
        if html.startswith("```html"):
            html = html[7:]
        elif html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]
        html = html.strip()
        return html

    except Exception as e:
        # print removed
        return _build_fallback_map(pois)


def _build_fallback_map(pois: list) -> str:
    """LLM 生成失败时的回退地图 HTML"""
    import json as _json
    city_name = pois[0].get("address", "")[:10] if pois else ""
    title = f"{city_name}景点地图" if city_name else "景点地图"

    markers_js_parts = ["var bounds = [];"]
    for p in pois:
        lat = p.get("lat", 0)
        lng = p.get("lng", 0)
        name = p.get("name", "")
        desc = p.get("description", "")
        popup = f"<strong>{name}</strong><br/>{desc}"
        markers_js_parts.append(
            f"L.marker([{lat}, {lng}]).addTo(map).bindPopup('{popup}');\n        bounds.push([{lat}, {lng}]);"
        )
    markers_js = "\n        ".join(markers_js_parts)

    items_html = ""
    for p in pois:
        rating_html = f"\\u2b50 {p.get('rating', '')}" if p.get("rating") else ""
        items_html += (
            f'<div class="item"><div class="dot"></div>'
            f'<span class="name">{p["name"]}</span>'
            f'<span class="meta">{rating_html}</span></div>\\n'
        )

    first_lat = pois[0].get("lat", 0)
    first_lng = pois[0].get("lng", 0)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{title}</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
*{{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}}
body{{background:#f0f7ff}}
.header{{background:linear-gradient(135deg,#0ea5e9,#6366f1);color:white;padding:16px 20px}}
.header h1{{font-size:20px;font-weight:600}}
.header p{{font-size:13px;opacity:.85;margin-top:4px}}
#map{{height:500px;width:100%}}
.list{{padding:16px 20px;background:white}}
.list h3{{font-size:15px;color:#475569;margin-bottom:10px}}
.item{{display:flex;align-items:center;padding:8px 0;border-bottom:1px solid #f1f5f9}}
.item:last-child{{border:none}}
.item .dot{{width:10px;height:10px;border-radius:50%;background:#6366f1;margin-right:10px;flex-shrink:0}}
.item .name{{font-size:14px;font-weight:500;color:#1e293b}}
.item .meta{{font-size:12px;color:#94a3b8;margin-left:auto}}
.footer{{text-align:center;padding:12px;font-size:12px;color:#94a3b8}}
</style>
</head>
<body>
<div class="header"><h1>\\U0001f5fa {title}</h1><p>共 {len(pois)} 个景点</p></div>
<div id="map"></div>
<div class="list"><h3>\\U0001f4cd 景点列表</h3>
{items_html}</div>
<div class="footer">数据来源：AI 生成，仅供参考</div>
<script>
var map = L.map('map').setView([{first_lat}, {first_lng}], 10);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png',{{attribution:'&copy; OSM',maxZoom:18}}).addTo(map);
{markers_js}
if(bounds.length>0) map.fitBounds(bounds,{{padding:[40,40]}});
</script>
</body>
</html>"""
