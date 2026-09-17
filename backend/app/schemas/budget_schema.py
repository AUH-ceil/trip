"""
预算相关 Pydantic 请求/响应数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class BudgetItem(BaseModel):
    """单项费用"""
    name: str = Field(..., description='费用项目名称')
    amount: float = Field(..., ge=0, description='金额')


class BudgetRequest(BaseModel):
    """预算分摊请求体"""
    trip_id: Optional[str] = Field('', description='关联行程ID(可选)')
    person_count: int = Field(..., ge=1, le=1000, description='分摊人数')
    items: List[BudgetItem] = Field(..., min_length=1, description='费用明细列表')


class BudgetResponse(BaseModel):
    """预算分摊响应体"""
    id: str
    total_amount: float
    person_count: int
    items: List[dict]
    per_person: float
    created_at: str

