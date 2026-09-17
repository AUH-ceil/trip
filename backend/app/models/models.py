"""
数据库 ORM 实体模型
行程计划表、预算记录表
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Float, Integer, DateTime
from backend.app.models.database import Base


def generate_uuid() -> str:
    """生成 UUID 字符串作为主键"""
    return uuid.uuid4().hex[:16]


class TripPlan(Base):
    """行程计划数据库实体"""
    __tablename__ = 'trip_plans'

    id = Column(String(16), primary_key=True, default=generate_uuid)
    destination = Column(String(200), nullable=False, comment='目的地')
    days = Column(Integer, nullable=False, comment='行程天数')
    details = Column(Text, nullable=False, comment='行程详细内容(JSON格式)')
    creator = Column(String(100), default='anonymous', comment='创建者')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'destination': self.destination,
            'days': self.days,
            'details': self.details,
            'creator': self.creator,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class BudgetRecord(Base):
    """预算分摊记录数据库实体"""
    __tablename__ = 'budget_records'

    id = Column(String(16), primary_key=True, default=generate_uuid)
    trip_id = Column(String(16), nullable=True, comment='关联行程ID')
    total_amount = Column(Float, nullable=False, comment='总金额')
    person_count = Column(Integer, nullable=False, comment='人数')
    items = Column(Text, nullable=False, comment='费用明细(JSON)')
    per_person = Column(Float, nullable=False, comment='人均费用')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'trip_id': self.trip_id,
            'total_amount': self.total_amount,
            'person_count': self.person_count,
            'items': self.items,
            'per_person': self.per_person,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

