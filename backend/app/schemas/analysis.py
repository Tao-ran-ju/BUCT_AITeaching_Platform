"""数据驾驶舱相关模型。"""
from typing import Optional

from pydantic import BaseModel


class MetricCard(BaseModel):
    """核心指标卡。"""

    key: str
    label: str
    value: float
    unit: str = ""
    trend: Optional[float] = None  # 相对上周期变化


class HeatmapCell(BaseModel):
    """能力矩阵热力图单元格。"""

    knowledge_point: str
    value: float = 0.0  # 0-1


class DashboardOverview(BaseModel):
    """驾驶舱总览。"""

    metrics: list[MetricCard]
    heatmap: list[HeatmapCell]
