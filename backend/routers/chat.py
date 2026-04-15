import json
from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas.chat import ChatRequest, ChatResponse, MessageHistory
from services.chat_service import chat_service
from models.conversation import ChatMessage

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _get_client_ip(request: Request) -> str:
    """Extract real client IP from request headers."""
    # Check forwarded headers (Cloudflare, proxies)
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"


@router.post("", response_model=ChatResponse)
async def send_message(request: ChatRequest, req: Request, db: AsyncSession = Depends(get_db)):
    """Send a message and get a complete response."""
    ip = _get_client_ip(req)
    ua = req.headers.get("user-agent", "")
    try:
        response_text, resources, crisis_tier = await chat_service.process_message(
            db=db,
            session_id=request.session_id,
            message=request.message,
            source=request.source,
            ip_address=ip,
            user_agent=ua,
        )
    except Exception as e:
        # Graceful fallback if LLM fails
        response_text = (
            "I'm sorry, I'm having a temporary issue connecting to my AI service. "
            "In the meantime, you can reach the Road Home Program directly:\n\n"
            "**Phone:** (312) 942-8387 (VETS)\n"
            "**Website:** [roadhomeprogram.org](https://roadhomeprogram.org)\n\n"
            "If you're in crisis, please call the **Veterans Crisis Line: 988** (press 1)."
        )
        resources = []
        crisis_tier = None
        import traceback
        traceback.print_exc()

    crisis_data = None
    if crisis_tier == 1:
        from schemas.chat import CrisisResponse
        crisis_data = CrisisResponse(is_crisis=True, tier=1, message=response_text)

    return ChatResponse(
        session_id=request.session_id,
        message=response_text,
        resources=resources,
        crisis=crisis_data,
    )


@router.get("/stream")
async def stream_message(
    request: Request,
    session_id: str = Query(...),
    message: str = Query(...),
    source: str = Query(default="widget"),
    db: AsyncSession = Depends(get_db),
):
    """Stream a response via Server-Sent Events."""
    ip = _get_client_ip(request)
    ua = request.headers.get("user-agent", "")

    async def event_generator():
        async for event in chat_service.process_message_stream(
            db=db,
            session_id=session_id,
            message=message,
            source=source,
            ip_address=ip,
            user_agent=ua,
        ):
            event_type = event["event"]
            data = event["data"]
            yield f"event: {event_type}\ndata: {json.dumps(data) if event_type == 'resources' else data}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions/{session_id}/history")
async def get_history(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get conversation history for a session."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return [
        MessageHistory(
            role=m.role,
            content=m.content,
            created_at=m.created_at,
            resources=json.loads(m.resources_cited) if m.resources_cited else [],
        )
        for m in messages
    ]
