from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class KnowledgeDocumentCreate(BaseModel):
    title: str
    category: str
    content: str
    url: Optional[str] = None
    phone: Optional[str] = None


class KnowledgeDocumentUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    url: Optional[str] = None
    phone: Optional[str] = None


class KnowledgeDocumentResponse(BaseModel):
    id: int
    title: str
    category: str
    content: str
    url: Optional[str] = None
    phone: Optional[str] = None
    source: str
    chunks_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeDocumentList(BaseModel):
    documents: List[KnowledgeDocumentResponse]
    total: int
