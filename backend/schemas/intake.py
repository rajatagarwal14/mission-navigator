from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class IntakeStartRequest(BaseModel):
    session_id: Optional[str] = None


class IntakeMessageRequest(BaseModel):
    intake_id: str
    message: str


class IntakeSubmitRequest(BaseModel):
    intake_id: str
    consent_given: bool


class IntakeResponse(BaseModel):
    intake_id: str
    state: str
    message: str
    is_complete: bool = False
    summary: Optional[str] = None


class IntakeSubmissionView(BaseModel):
    id: str
    summary: str
    urgency: Optional[str] = None
    consent_given: bool
    submitted_at: Optional[datetime] = None
    reviewed: bool = False
    created_at: datetime
