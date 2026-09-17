# TripAgent · AI 智能旅行规划系统

基于大模型的旅行规划助手：输入目的地和天数，Agent 会自动查询天气、检索景点、推荐穿搭，最后生成一份完整的行程方案，并支持保存历史行程、多人预算分摊和 PDF 导出。

前后端同仓库，后端 FastAPI，前端是单文件 HTML，启动后浏览器直接访问即可，无需额外构建。

## 功能

| 模块 | 说明 |
| --- | --- |
| ✏️ AI 行程生成 | 输入目的地 / 天数 / 偏好，LangChain Agent 自主调用工具生成逐日行程，自动入库 |
| ☁️ 天气预报 | 7 日预报，天气状况和风向自动翻译为中文 |
| 🧣 穿搭推荐 | 按目的地实时温度分 5 档给出穿搭建议和行李清单 |
| 💰 预算分摊 | 多人旅行费用明细自动计算人均 |
| 🗺 景点检索 | 关键词检索景点（含经纬度），支持在页面内渲染 Leaflet 地图，或由 AI 直接生成一张地图 HTML |
| 📄 PDF 导出 | 行程一键导出 A4 PDF（内置中文字体，支持 Markdown 表格） |
| 📋 历史行程 | 查看、回看、导出所有已生成的行程 |

## 技术栈

- **后端**：FastAPI 0.104 + Uvicorn + SQLAlchemy 2.0（异步）+ aiosqlite（SQLite）
- **AI**：LangChain 1.3 `create_agent`（LangGraph 模式）+ DeepSeek Chat
- **外部服务**：WeatherAPI（天气）、高德开放平台（坐标校正）
- **PDF**：ReportLab（`STSong-Light` 内置中文字体，无需额外字体文件）
- **前端**：原生 HTML/JS + Tailwind CDN + Leaflet CDN

## 目录结构

```
trip/
├── backend/
│   ├── main.py                 # 唯一启动入口：路由注册、建表、CORS、全局异常
│   ├── trip.db                 # SQLite 数据库（首次启动自动生成，已被 gitignore）
│   ├── trip_agent/
│   │   ├── agent.py            # TripAgent：注册 3 个 Skill 工具，调度大模型
│   │   └── prompt_template.py  # 系统提示词与用户提示词模板
│   ├── app/
│   │   ├── api/                # 路由层：trip / weather / budget / pdf / map / wardrobe
│   │   ├── services/           # 业务层：景点检索、天气、穿搭、预算、PDF 生成
│   │   ├── models/             # ORM 实体 TripPlan、BudgetRecord + 异步引擎
│   │   └── schemas/            # Pydantic 请求/响应模型
│   └── utils/env_loader.py     # .env 读取
├── frontend/index.html         # 全部前端页面（单文件）
├── outputs/                    # 旧版 PDF 输出目录
└── requirements.txt
```

## 快速开始

### 1. 环境要求

- Python **3.10+**（实测 3.13.13）
- 能访问外网（调用 DeepSeek / WeatherAPI / 高德 / CDN 静态资源）

### 2. 安装依赖

```bash
git clone <你的仓库地址>
cd trip

# 创建虚拟环境
python -m venv trip_venv

# 激活虚拟环境
trip_venv\Scripts\activate        # Windows CMD
.\trip_venv\Scripts\Activate.ps1  # Windows PowerShell
source trip_venv/bin/activate     # macOS / Linux

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置密钥

在**项目根目录**新建 `.env` 文件（该文件已被 `.gitignore` 忽略，不会进仓库）：

```ini
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxx
GAODE_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
HEFENG_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
```

各密钥申请地址：

| 变量名 | 用途 | 申请地址 |
| --- | --- | --- |
| `DEEPSEEK_API_KEY` | 行程生成、景点检索、地图生成（**必填**） | https://platform.deepseek.com/ |
| `GAODE_API_KEY` | 景点坐标校正（可选，填了更准） | https://lbs.amap.com/ （Web 服务类型 Key） |
| `HEFENG_API_KEY` | 天气与穿搭（可选） | https://www.weatherapi.com/ |

> ⚠️ 变量名虽然叫 `HEFENG_API_KEY`，但代码实际请求的是 **WeatherAPI**（`api.weatherapi.com`）的接口，所以这里要填 WeatherAPI 的 Key。
>
> 缺少 `DEEPSEEK_API_KEY` 时服务能启动，但生成行程会失败；缺少天气 Key 时天气/穿搭接口会返回「未配置 WeatherAPI Key」。

> `.env` 放在**项目根目录**即可，`env_loader.py` 会基于自身文件位置自动定位，项目克隆到任意路径都能正确读取。

### 4. 启动服务

**必须在项目根目录 `trip/` 下执行**，因为代码使用的是 `backend.xxx` 包路径：

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

首次启动会自动创建数据库表，无需手动初始化。

### 5. 访问

| 地址 | 说明 |
| --- | --- |
| http://127.0.0.1:8000/ | 前端主页面（5 个功能 Tab） |
| http://127.0.0.1:8000/docs | Swagger 交互式 API 文档 |
| http://127.0.0.1:8000/health | 健康检查 |
| http://127.0.0.1:8000/redoc | ReDoc API 文档 |

## API 一览

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/trip/generate` | 生成行程（body: `destination`, `days`, `preferences`, `creator`） |
| GET | `/api/trip/history` | 历史行程列表（按创建时间倒序） |
| GET | `/api/trip/{trip_id}` | 单个行程详情 |
| GET | `/api/weather/forecast?city=北京&days=7` | 天气预报（`days` 1–7） |
| GET | `/api/wardrobe/recommend?city=北京` | 穿搭推荐 |
| POST | `/api/budget/split` | 预算分摊（body: `person_count`, `items[]`, `trip_id`） |
| GET | `/api/map/search?city=北京&keyword=热门景点` | 景点检索（文本） |
| GET | `/api/map/places?city=北京&keyword=美食` | 景点检索（结构化，含坐标） |
| GET | `/api/map/generate?city=北京&keyword=热门景点` | 返回一张 AI 生成的完整地图 HTML 页面 |
| GET | `/api/pdf/export/{trip_id}` | 导出行程 PDF |

调试示例：

```bash
curl -X POST http://127.0.0.1:8000/api/trip/generate \
  -H "Content-Type: application/json" \
  -d '{"destination":"北京","days":3,"preferences":"偏好:美食","creator":"web_user"}'
```

## 数据存储

- 数据库：SQLite，文件在 `backend/trip.db`，首次启动由 `init_db()` 自动建表。
- 两张表：`trip_plans`（行程）、`budget_records`（预算记录）。
- 想重置数据，直接删掉 `backend/trip.db` 再重启即可。
- 导出的 PDF 落在 `backend/app/outputs/`（文件名形如 `trip_北京_20260917_153000.pdf`）。

## 常见问题

**启动报 `ModuleNotFoundError: No module named 'backend'`**
没有在项目根目录下启动。先 `cd` 到 `trip/`，再执行第 4 步的命令。

**生成的行程里英文单词少了字母 n**
`backend/app/services/pdf_export.py` 里的清理规则 `re.sub(r'n+', '', text)` 没有边界限制，会把正文中所有字母 `n` 删掉（如 `London` → `Lodo`）。中文行程影响不大，但混有英文地名时请留意。

**导出的 PDF 是空白的 / 中文变方块**
确认 `reportlab` 已正确安装。代码用的是 ReportLab 内置的 `STSong-Light` CID 字体，不需要额外字体文件。

**端口 8000 被占用**
换端口启动：`python -m uvicorn backend.main:app --port 8001`，同时把 `frontend/index.html` 里的 `API_BASE` 一并改掉。

**Windows 控制台打印中文报 `UnicodeEncodeError`**
`backend/main.py` 的全局异常处理已做兜底，不影响接口返回。也可以在启动前执行 `set PYTHONIOENCODING=utf-8`。

**地图 / 前端样式加载不出来**
前端依赖 unpkg 和 Tailwind CDN，需要能访问外网。

## License

仅供学习交流使用。行程、景点、坐标等数据由 AI 生成，仅供参考，出行前请自行核实。
