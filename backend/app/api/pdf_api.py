"""
PDF 导出 API 路由
将行程方案导出为 PDF 文件并提供下载
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.database import get_db
from backend.app.models.models import TripPlan
from backend.app.services.pdf_export import export_trip_pdf
import os

router = APIRouter(prefix='/api/pdf', tags=['PDF导出'])


@router.get('/export/{trip_id}', summary='导出行程PDF')
async def export_pdf(trip_id: str, db: AsyncSession = Depends(get_db)):
    """
    根据行程ID导出为 PDF 文件并下载

    参数:
        trip_id: 行程ID

    返回:
        PDF 文件下载响应
    """
    result = await db.execute(select(TripPlan).where(TripPlan.id == trip_id))
    trip = result.scalar_one_or_none()
    if not trip:
        raise HTTPException(status_code=404, detail='行程不存在')

    filepath = await export_trip_pdf(
        destination=trip.destination,
        days=trip.days,
        details=trip.details,
        creator=trip.creator,
    )

    if not os.path.exists(filepath):
        raise HTTPException(status_code=500, detail='PDF生成失败')

    filename = os.path.basename(filepath)
    return FileResponse(
        path=filepath,
        media_type='application/pdf',
        filename=filename,
    )

