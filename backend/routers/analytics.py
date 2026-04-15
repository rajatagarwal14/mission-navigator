import json
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import StaffUser
from models.conversation import ChatSession, ChatMessage
from models.analytics import QueryLog
from core.security import get_current_user
from schemas.analytics import AnalyticsDashboard
from services.analytics_service import analytics_service

router = APIRouter(prefix="/api/admin/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=AnalyticsDashboard)
async def get_dashboard(
    days: int = Query(default=30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    """Get full analytics dashboard data."""
    overview = await analytics_service.get_overview(db)
    top_questions = await analytics_service.get_top_questions(db)
    top_resources = await analytics_service.get_top_resources(db)
    usage_trend = await analytics_service.get_usage_trend(db, days=days)

    return AnalyticsDashboard(
        overview=overview,
        top_questions=top_questions,
        top_resources=top_resources,
        usage_trend=usage_trend,
    )


@router.get("/sessions")
async def get_recent_sessions(
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    """List recent chat sessions with IP addresses and message counts."""
    result = await db.execute(
        select(ChatSession)
        .order_by(desc(ChatSession.started_at))
        .limit(limit)
    )
    sessions = result.scalars().all()
    return [
        {
            "id": s.id,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "last_activity": s.last_activity.isoformat() if s.last_activity else None,
            "message_count": s.message_count,
            "crisis_flagged": s.crisis_flagged,
            "ip_address": s.ip_address,
            "user_agent": s.user_agent,
            "source": s.source,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    """Get all messages for a specific chat session."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [
        {
            "role": m.role,
            "content": m.content,
            "created_at": m.created_at.isoformat() if m.created_at else None,
            "crisis_tier": m.crisis_tier,
            "resources_cited": json.loads(m.resources_cited) if m.resources_cited else [],
        }
        for m in messages
    ]


@router.get("/query-logs")
async def get_query_logs(
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    """Get recent query logs showing what users asked and what resources were returned."""
    result = await db.execute(
        select(QueryLog)
        .order_by(desc(QueryLog.created_at))
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "session_id": log.session_id,
            "query_text": log.query_text,
            "resources_cited": json.loads(log.resources_cited) if log.resources_cited else [],
            "crisis_tier": log.crisis_tier,
            "response_time_ms": log.response_time_ms,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.post("/resource-click")
async def log_resource_click(
    session_id: str,
    resource_name: str,
    resource_url: str = None,
    db: AsyncSession = Depends(get_db),
):
    """Log a resource click (no auth required - called from chat widget)."""
    await analytics_service.log_resource_click(db, session_id, resource_name, resource_url)
    return {"status": "ok"}
