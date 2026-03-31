from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import StaffUser
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
