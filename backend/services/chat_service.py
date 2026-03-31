import json
import time
import uuid
from datetime import datetime
from typing import AsyncGenerator, Optional, Tuple, List, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.conversation import ChatSession, ChatMessage
from models.analytics import QueryLog
from services.safety_service import safety_service
from services.rag_service import rag_service
from services.llm_service import llm_service
from schemas.chat import ResourceInfo


class ChatService:
    async def get_or_create_session(self, db: AsyncSession, session_id: str, source: str = "widget") -> ChatSession:
        """Get existing session or create a new one."""
        result = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        session = result.scalar_one_or_none()

        if not session:
            session = ChatSession(id=session_id, source=source)
            db.add(session)
            await db.flush()

        return session

    async def get_conversation_history(self, db: AsyncSession, session_id: str, limit: int = 6) -> list[dict]:
        """Get recent conversation history for context."""
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(reversed(result.scalars().all()))
        return [{"role": m.role, "content": m.content} for m in messages]

    async def process_message(
        self, db: AsyncSession, session_id: str, message: str, source: str = "widget"
    ) -> Tuple[str, List[ResourceInfo], Optional[int]]:
        """Process a user message through the full pipeline. Returns (response, resources, crisis_tier)."""
        start_time = time.time()

        # Get or create session
        session = await self.get_or_create_session(db, session_id, source)

        # Layer 1: Crisis detection (pre-LLM)
        crisis_tier, crisis_response = safety_service.check_crisis(message)

        if crisis_tier == 1 and crisis_response:
            # Immediate crisis - bypass LLM
            await self._save_message(db, session, "user", message, crisis_tier=1)
            await self._save_message(db, session, "assistant", crisis_response, crisis_tier=1)
            session.crisis_flagged = True
            await self._log_query(db, session_id, message, crisis_response, [], 1, start_time)
            await db.commit()
            return crisis_response, [], 1

        # Check for off-topic
        if safety_service.is_off_topic(message):
            response = safety_service.get_off_topic_response()
            await self._save_message(db, session, "user", message)
            await self._save_message(db, session, "assistant", response)
            await self._log_query(db, session_id, message, response, [], None, start_time)
            await db.commit()
            return response, [], None

        # Layer 2: RAG retrieval
        chunks = rag_service.retrieve(message, n_results=5)
        context = rag_service.format_context(chunks)
        resource_infos = rag_service.extract_resource_info(chunks)

        # Get conversation history
        history = await self.get_conversation_history(db, session_id)

        # Layer 3: LLM generation
        response = await llm_service.generate(
            user_message=message,
            context=context,
            conversation_history=history,
            crisis_tier=crisis_tier,
        )

        # Layer 4: Output validation
        context_phones = [r["phone"] for r in resource_infos if r.get("phone")]
        context_urls = [r["url"] for r in resource_infos if r.get("url")]
        is_valid, reason = safety_service.validate_response(response, context_phones, context_urls)

        if not is_valid:
            # Regenerate with stricter prompt
            response = await llm_service.generate(
                user_message=message + "\n\n[SYSTEM: Your previous response was filtered. Respond ONLY with resource referrals from the provided context. Do not include medical advice.]",
                context=context,
                conversation_history=history,
                crisis_tier=crisis_tier,
            )

        # Save messages
        resources_json = json.dumps([r["name"] for r in resource_infos])
        await self._save_message(db, session, "user", message, crisis_tier=crisis_tier)
        await self._save_message(db, session, "assistant", response, crisis_tier=crisis_tier, resources_cited=resources_json)

        if crisis_tier:
            session.crisis_flagged = True

        # Log query for analytics
        await self._log_query(db, session_id, message, response, [r["name"] for r in resource_infos], crisis_tier, start_time)

        await db.commit()

        resources = [
            ResourceInfo(
                name=r["name"],
                category=r["category"],
                description=r["description"],
                phone=r.get("phone"),
                url=r.get("url"),
            )
            for r in resource_infos
        ]

        return response, resources, crisis_tier

    async def process_message_stream(
        self, db: AsyncSession, session_id: str, message: str, source: str = "widget"
    ) -> AsyncGenerator[dict, None]:
        """Process a message with streaming response. Yields events."""
        start_time = time.time()

        session = await self.get_or_create_session(db, session_id, source)

        # Crisis detection
        crisis_tier, crisis_response = safety_service.check_crisis(message)

        if crisis_tier == 1 and crisis_response:
            await self._save_message(db, session, "user", message, crisis_tier=1)
            await self._save_message(db, session, "assistant", crisis_response, crisis_tier=1)
            session.crisis_flagged = True
            await self._log_query(db, session_id, message, crisis_response, [], 1, start_time)
            await db.commit()
            yield {"event": "crisis", "data": crisis_response}
            yield {"event": "done", "data": ""}
            return

        # Off-topic check
        if safety_service.is_off_topic(message):
            response = safety_service.get_off_topic_response()
            await self._save_message(db, session, "user", message)
            await self._save_message(db, session, "assistant", response)
            await self._log_query(db, session_id, message, response, [], None, start_time)
            await db.commit()
            yield {"event": "token", "data": response}
            yield {"event": "done", "data": ""}
            return

        # RAG
        chunks = rag_service.retrieve(message, n_results=5)
        context = rag_service.format_context(chunks)
        resource_infos = rag_service.extract_resource_info(chunks)

        # Send resources first
        if resource_infos:
            yield {"event": "resources", "data": resource_infos}

        # Get history
        history = await self.get_conversation_history(db, session_id)

        # Stream LLM response
        full_response = ""
        async for token in llm_service.generate_stream(
            user_message=message,
            context=context,
            conversation_history=history,
            crisis_tier=crisis_tier,
        ):
            full_response += token
            yield {"event": "token", "data": token}

        # Save
        resources_json = json.dumps([r["name"] for r in resource_infos])
        await self._save_message(db, session, "user", message, crisis_tier=crisis_tier)
        await self._save_message(db, session, "assistant", full_response, crisis_tier=crisis_tier, resources_cited=resources_json)

        if crisis_tier:
            session.crisis_flagged = True

        await self._log_query(db, session_id, message, full_response, [r["name"] for r in resource_infos], crisis_tier, start_time)
        await db.commit()

        yield {"event": "done", "data": ""}

    async def _save_message(
        self, db: AsyncSession, session: ChatSession, role: str, content: str,
        crisis_tier: int = None, resources_cited: str = None
    ):
        msg = ChatMessage(
            session_id=session.id,
            role=role,
            content=content,
            crisis_tier=crisis_tier,
            resources_cited=resources_cited,
        )
        db.add(msg)
        session.message_count += 1
        session.last_activity = datetime.utcnow()

    async def _log_query(
        self, db: AsyncSession, session_id: str, query: str, response: str,
        resources: list, crisis_tier: int, start_time: float
    ):
        elapsed_ms = int((time.time() - start_time) * 1000)
        log = QueryLog(
            session_id=session_id,
            query_text=query,
            response_text=response,
            resources_cited=json.dumps(resources),
            crisis_tier=crisis_tier,
            response_time_ms=elapsed_ms,
        )
        db.add(log)


chat_service = ChatService()
