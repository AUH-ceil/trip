"""
预算分摊计算 API 路由
支持多人旅行费用自动分摊计算
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.models.database import get_db
from backend.app.models.models import BudgetRecord
from backend.app.schemas.budget_schema import BudgetRequest, BudgetResponse
from backend.app.services.budget_split import split_budget
import json

router = APIRouter(prefix='/api/budget', tags=['预算分摊'])


@router.post('/split', response_model=BudgetResponse, summary='计算预算分摊')
async def calculate_budget(req: BudgetRequest, db: AsyncSession = Depends(get_db)):
    """
    根据费用明细和人数计算人均分摊金额，并保存记录

    参数:
        req: 预算分摊请求体（person_count, items, trip_id）

    返回:
        包含总金额、人均金额、费用明细的响应
    """
    items_dict = [{'name': i.name, 'amount': i.amount} for i in req.items]
    total = round(sum(i.amount for i in req.items), 2)

    result = await split_budget(total, req.person_count, items_dict)

    record = BudgetRecord(
        trip_id=req.trip_id or '',
        total_amount=result['total_amount'],
        person_count=result['person_count'],
        items=json.dumps(result['items'], ensure_ascii=False),
        per_person=result['per_person'],
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return BudgetResponse(
        id=record.id,
        total_amount=record.total_amount,
        person_count=record.person_count,
        items=json.loads(record.items),
        per_person=record.per_person,
        created_at=record.created_at.isoformat() if record.created_at else '',
    )

