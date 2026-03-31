from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class AnalyticsOverview(BaseModel):
    total_sessions: int
    messages_today: int
    unique_users_7d: int
    crisis_alerts: int


class TopQuestion(BaseModel):
    question: str
    count: int


class TopResource(BaseModel):
    name: str
    citations: int
    clicks: int


class UsageTrendPoint(BaseModel):
    date: str
    sessions: int
    messages: int


class AnalyticsDashboard(BaseModel):
    overview: AnalyticsOverview
    top_questions: List[TopQuestion]
    top_resources: List[TopResource]
    usage_trend: List[UsageTrendPoint]
