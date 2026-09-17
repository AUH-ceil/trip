"""
行程生成 API 路由
包含生成新行程、查询历史行程列表、查询单个行程详情
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.database import get_db
from backend.app.models.models import TripPlan
from backend.app.schemas.trip_schema import TripRequest, TripResponse, TripListItem
from backend.trip_agent.agent import trip_agent
import json

router = APIRouter(prefix='/api/trip', tags=['行程管理'])


@router.post('/generate', response_model=TripResponse, summary='生成新行程')
async def generate_trip(req: TripRequest, db: AsyncSession = Depends(get_db)):
    """
    根据目的地、天数和偏好生成 AI 行程方案，并持久化到数据库

    参数:
        req: 行程生成请求体（destination, days, preferences, creator）

    返回:
        包含行程ID、目的地、天数、详情、创建信息的响应
    """
    details = await trip_agent.generate_trip(req.destination, req.days, req.preferences)

    trip = TripPlan(
        destination=req.destination,
        days=req.days,
        details=details,
        creator=req.creator or 'anonymous',
    )
    db.add(trip)
    await db.commit()
    await db.refresh(trip)

    return TripResponse(
        id=trip.id,
        destination=trip.destination,
        days=trip.days,
        details=trip.details,
        creator=trip.creator,
        created_at=trip.created_at.isoformat() if trip.created_at else '',
    )


@router.get('/history', response_model=list[TripListItem], summary='查询历史行程列表')
async def list_trips(db: AsyncSession = Depends(get_db)):
    """获取所有已保存的行程计划列表，按创建时间倒序"""
    result = await db.execute(
        select(TripPlan).order_by(TripPlan.created_at.desc())
    )
    trips = result.scalars().all()
    return [
        TripListItem(
            id=t.id,
            destination=t.destination,
            days=t.days,
            creator=t.creator,
            created_at=t.created_at.isoformat() if t.created_at else '',
        )
        for t in trips
    ]


@router.get('/{trip_id}', response_model=TripResponse, summary='查询单个行程详情')
async def get_trip(trip_id: str, db: AsyncSession = Depends(get_db)):
    """根据行程ID获取详细行程内容"""
    result = await db.execute(select(TripPlan).where(TripPlan.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail='行程不存在')
    return TripResponse(
        id=trip.id,
        destination=trip.destination,
        days=trip.days,
        details=trip.details,
        creator=trip.creator,
        created_at=trip.created_at.isoformat() if trip.created_at else '',
    )

