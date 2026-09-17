"""
异步数据库引擎与会话管理
使用 aiosqlite + SQLAlchemy 异步接口
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# 数据库文件路径（项目根目录）
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'trip.db')
DATABASE_URL = f'sqlite+aiosqlite:///{DB_PATH}'

# 异步引擎
engine = create_async_engine(DATABASE_URL, echo=False)

# 异步会话工厂
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类"""
    pass


async def get_db():
    """
    异步数据库会话依赖注入
    用于 FastAPI Depends，自动管理会话的生命周期
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """异步初始化数据库，创建所有表"""
    async with engine.begin() as conn:
        from backend.app.models.models import TripPlan, BudgetRecord  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)

