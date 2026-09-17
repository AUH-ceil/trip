"""
PDF 行程导出 Skill
使用 reportlab 生成行程计划的 PDF 文件，修复中文/异步/表格/乱码问题
"""
import os
import re
import asyncio
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
# 导入中文字体支持
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# 全局注册内置中文字体（无需额外字体文件）
pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
FONT_CN = 'STSong-Light'

# 清洗脏文本：删除乱码占位n、多余符号
def clean_raw_text(text: str) -> str:
    # 批量清除无意义的n占位字符、连续横线
    text = re.sub(r'n+', '', text)
    text = re.sub(r'-{3,}', '', text)
    text = re.sub(r'>{2,}', '', text)
    return text.strip()

# 解析Markdown简易表格，返回Table对象
def parse_md_table(line_list, body_style):
    table_data = []
    for line in line_list:
        line = line.strip()
        if not line.startswith('|'):
            continue
        # 去除首尾|，按|分割单元格
        cells = [c.strip() for c in line.strip('|').split('|')]
        row_p = [Paragraph(cell, body_style) for cell in cells]
        table_data.append(row_p)
    if not table_data:
        return None
    # 生成表格并设置样式
    table = Table(table_data)
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), FONT_CN),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(table_style)
    return table

async def export_trip_pdf(destination: str, days: int, details: str, creator: str = 'anonymous') -> str:
    """
    生成行程计划的 PDF 文件

    参数:
        destination: 目的地
        days: 行程天数
        details: 行程详情文本
        creator: 创建者

    返回:
        PDF 文件路径
    """
    # 修复1：改用项目根目录定位，不再硬编码四层父目录
    base_path = os.path.abspath(__file__)
    project_root = os.path.dirname(os.path.dirname(base_path))
    output_dir = os.path.join(project_root, 'outputs')
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_name = destination.replace(' ', '_').replace('/', '_').replace('\\', '_')[:30]
    filepath = os.path.join(output_dir, f'trip_{safe_name}_{timestamp}.pdf')

    doc = SimpleDocTemplate(filepath, pagesize=A4,
                            topMargin=20 * mm, bottomMargin=20 * mm,
                            leftMargin=15*mm, rightMargin=15*mm)
    styles = getSampleStyleSheet()

    # 修复2：所有样式绑定中文字体，解决中文空白乱码
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=20, spaceAfter=12, alignment=1,
        fontName=FONT_CN
    )
    heading_style = ParagraphStyle(
        'CustomHeading', parent=styles['Heading2'],
        fontSize=14, spaceBefore=10, spaceAfter=6,
        fontName=FONT_CN
    )
    body_style = ParagraphStyle(
        'CustomBody', parent=styles['Normal'],
        fontSize=11, spaceAfter=4, leading=18,
        fontName=FONT_CN
    )

    elements = []
    # 移除emoji避免字体缺失乱码
    elements.append(Paragraph(f'{destination} 行程计划', title_style))
    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph(f'行程天数：{days} 天', heading_style))
    elements.append(Paragraph(f'创建者：{creator}', heading_style))
    elements.append(Spacer(1, 4 * mm))

    # 清洗原始文本，过滤乱码n
    clean_details = clean_raw_text(details)
    lines = [line.strip() for line in clean_details.split('\n')]
    table_buffer = []

    for line in lines:
        if not line:
            # 遇到空行，先处理缓存的表格
            if table_buffer:
                tbl = parse_md_table(table_buffer, body_style)
                if tbl:
                    elements.append(tbl)
                    elements.append(Spacer(1,3*mm))
                table_buffer.clear()
            continue
        # 判断是表格行，存入缓存
        if line.startswith('|'):
            table_buffer.append(line)
            continue
        # 非表格行，先输出缓存表格
        if table_buffer:
            tbl = parse_md_table(table_buffer, body_style)
            if tbl:
                elements.append(tbl)
                elements.append(Spacer(1,3*mm))
            table_buffer.clear()
        # 普通标题/正文
        if line.startswith('#'):
            content = line.lstrip('#').strip()
            elements.append(Paragraph(content, heading_style))
        else:
            elements.append(Paragraph(line, body_style))
    # 循环结束，处理剩余表格
    if table_buffer:
        tbl = parse_md_table(table_buffer, body_style)
        if tbl:
            elements.append(tbl)

    # 修复4：同步阻塞操作放到线程池，不阻塞异步事件循环
    await asyncio.to_thread(doc.build, elements)

    return filepath