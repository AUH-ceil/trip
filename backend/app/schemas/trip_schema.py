"""
行程相关 Pydantic 请求/响应数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TripRequest(BaseModel):
    """行程生成请求体"""
    destination: str = Field(..., min_length=1, max_length=200, description='旅行目的地')
    days: int = Field(..., ge=1, le=30, description='行程天数')
    preferences: Optional[str] = Field('', max_length=500, description='偏好说明(例如:美食/文化/自然)')
    creator: Optional[str] = Field('anonymous', max_length=100, description='创建者')


class TripResponse(BaseModel):
    """行程生成响应体"""
    id: str
    destination: str
    days: int
    details: str
    creator: str
    created_at: str


class TripListItem(BaseModel):
    """历史行程列表项"""
    id: str
    destination: str
    days: int
    creator: str
    created_at: str

