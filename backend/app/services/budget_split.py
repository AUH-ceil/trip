"""
预算分摊计算 Skill
根据费用明细和人数计算人均分摊
"""
from typing import List, Dict


async def split_budget(total_amount: float, person_count: int, items: List[Dict]) -> Dict:
    """
    计算多人预算人均分摊

    参数:
        total_amount: 总金额
        person_count: 人数
        items: 费用明细列表，每项包含 name 和 amount

    返回:
        包含总金额、人均金额、费用明细的字典
    """
    if person_count <= 0:
        return {'error': '人数必须大于0'}
    if total_amount <= 0:
        return {'error': '总金额必须大于0'}

    per_person = round(total_amount / person_count, 2)

    detail_items = []
    for item in items:
        detail_items.append({
            'name': item.get('name', '未命名'),
            'amount': round(item.get('amount', 0), 2),
        })

    return {
        'total_amount': round(total_amount, 2),
        'person_count': person_count,
        'items': detail_items,
        'per_person': per_person,
    }

