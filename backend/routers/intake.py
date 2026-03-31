from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models.user import StaffUser
from models.intake import IntakeSession
from core.security import get_current_user
from schemas.intake import (
    IntakeStartRequest,
    IntakeMessageRequest,
    IntakeResponse,
    IntakeSubmissionView,
)
from services.intake_service import intake_service

router = APIRouter(prefix="/api/intake", tags=["intake"])


@router.post("/start", response_model=IntakeResponse)
async def start_intake(
    body: IntakeStartRequest = None,
    db: AsyncSession = Depends(get_db),
):
    """Start a new intake session."""
    session_id = body.session_id if body else None
    intake_id, question = await intake_service.start_session(db, chat_session_id=session_id)
    return IntakeResponse(
        intake_id=intake_id,
        state="GREETING",
        message=question,
    )


@router.post("/message", response_model=IntakeResponse)
async def intake_message(body: IntakeMessageRequest, db: AsyncSession = Depends(get_db)):
    """Send a message in the intake conversation."""
    state, response, is_complete, summary = await intake_service.process_message(
        db, body.intake_id, body.message
    )
    return IntakeResponse(
        intake_id=body.intake_id,
        state=state,
        message=response,
        is_complete=is_complete,
        summary=summary,
    )


@router.get("/admin/submissions")
async def list_submissions(
    db: AsyncSession = Depends(get_db),
    current_user: StaffUser = Depends(get_current_user),
):
    """List all submitted intakes (staff only)."""
    result = await db.execute(
        select(IntakeSession)
        .where(IntakeSession.submitted_at.isnot(None))
        .order_by(IntakeSession.submitted_at.desc())
    )
    sessions = result.scalars().all()
    return [
        IntakeSubmissionView(
            id=s.id,
            summary=s.summary or "",
            consent_given=s.consent_given,
            submitted_at=s.submitted_at,
            reviewed=s.reviewed_at is not None,
            created_at=s.created_at,
        )
        for s in sessions
    ]
