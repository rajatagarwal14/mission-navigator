from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from database import Base


class IntakeSession(Base):
    __tablename__ = "intake_sessions"

    id = Column(String, primary_key=True)
    chat_session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=True)
    state = Column(String, default="GREETING")
    collected_data = Column(Text, nullable=True)  # JSON object
    summary = Column(Text, nullable=True)
    consent_given = Column(Boolean, default=False)
    submitted_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("staff_users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
