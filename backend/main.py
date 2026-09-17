"""
FastAPI 程序唯一启动入口
全局 app 实例、路由注册、数据库初始化、异常处理统一在此定义
"""
import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from backend.app.models.database import init_db
from backend.app.api.trip_api import router as trip_router
from backend.app.api.weather_api import router as weather_router
from backend.app.api.budget_api import router as budget_router
from backend.app.api.pdf_api import router as pdf_router
from backend.app.api.map_api import router as map_router
from backend.app.api.wardrobe_api import router as wardrobe_router
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时初始化数据库"""
    await init_db()
    yield


app = FastAPI(
    title='TripAgent - 智能旅行规划系统',
    description='基于 AI 的智能旅行规划系统，支持行程生成、天气查询、预算分摊、PDF导出',
    version='2.0.0',
    lifespan=lifespan,
)

# CORS: 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# 注册路由
app.include_router(trip_router)
app.include_router(weather_router)
app.include_router(budget_router)
app.include_router(pdf_router)
app.include_router(map_router)
app.include_router(wardrobe_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常捕获中间件，统一返回错误信息"""
    import traceback
    err_msg = str(exc)
    try:
        err_msg.encode("gbk")
    except UnicodeEncodeError:
        err_msg = "编码错误（包含特殊字符）"
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            'detail': '服务器内部错误',
            'message': err_msg,
        },
    )


@app.get('/')
async def root():
    """服务根路径，返回前端页面"""
    from fastapi.responses import FileResponse
    index_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'index.html')
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type='text/html; charset=utf-8')
    return {
        'service': 'TripAgent - 智能旅行规划系统',
        'version': '2.0.0',
        'docs': '/docs',
    }


@app.get('/health')
async def health_check():
    """健康检查接口"""
    return {'status': 'ok'}

