from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatRequest(BaseModel):
    session_id: str
    message: str
    source: str = "widget"


class ResourceInfo(BaseModel):
    name: str
    category: str
    description: str
    phone: Optional[str] = None
    url: Optional[str] = None


class CrisisResponse(BaseModel):
    is_crisis: bool
    tier: Optional[int] = None
    message: str
    resources: List[ResourceInfo] = []


class ChatResponse(BaseModel):
    session_id: str
    message: str
    resources: List[ResourceInfo] = []
    crisis: Optional[CrisisResponse] = None
    created_at: datetime = None


class MessageHistory(BaseModel):
    role: str
    content: str
    created_at: datetime
    resources: List[ResourceInfo] = []
