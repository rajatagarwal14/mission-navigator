from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text
from database import Base


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=True)
    query_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=True)
    resources_cited = Column(Text, nullable=True)  # JSON array
    crisis_tier = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ResourceClick(Base):
    __tablename__ = "resource_clicks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, nullable=True)
    resource_name = Column(String, nullable=False)
    resource_url = Column(String, nullable=True)
    clicked_at = Column(DateTime, default=datetime.utcnow)
