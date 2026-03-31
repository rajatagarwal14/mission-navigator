import json
import uuid
from datetime import datetime
from typing import Tuple, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.intake import IntakeSession
from models.conversation import ChatSession
from services.safety_service import safety_service
from data.system_prompts import CRISIS_IMMEDIATE_RESPONSE

# State machine for intake flow
INTAKE_STATES = {
    "GREETING": {
        "question": (
            "Welcome to the Road Home Program intake process. I'm here to help gather some "
            "information so that when our team reaches out to you, they'll already have a good "
            "understanding of your needs.\n\n"
            "Everything you share here is confidential and will only be seen by the Road Home "
            "intake team.\n\n"
            "To get started, could you tell me a little about what brings you to the Road Home Program today?"
        ),
        "next": "CONNECTION",
        "field": "reason",
    },
    "CONNECTION": {
        "question": "Thank you for sharing that. Could you tell me about your connection to military service? For example, are you a veteran, active-duty service member, family member, or caregiver?",
        "next": "SERVICE_DETAILS",
        "field": "connection",
    },
    "SERVICE_DETAILS": {
        "question": "And which branch of service, and approximately when did you/your loved one serve?",
        "next": "LOCATION",
        "field": "service_details",
    },
    "LOCATION": {
        "question": "What state do you currently live in? This helps us determine which services are available to you.",
        "next": "URGENCY",
        "field": "location",
    },
    "URGENCY": {
        "question": "On a scale of 1-10, how urgently do you feel you need support right now? There's no wrong answer - this just helps our team prioritize.",
        "next": "FAMILY",
        "field": "urgency",
    },
    "FAMILY": {
        "question": "Are there any family members who might also benefit from support services? Road Home provides care for the whole family at no cost.",
        "next": "CONTACT",
        "field": "family_needs",
    },
    "CONTACT": {
        "question": "Finally, what is the best way for our intake team to reach you? You can share a phone number, email, or both - whatever you're most comfortable with.",
        "next": "CONSENT",
        "field": "contact_preference",
    },
    "CONSENT": {
        "question": (
            "Thank you for sharing all of this. Before I create a summary for our intake team, "
            "I want to confirm: **Do you consent to sharing this information with the Road Home "
            "Program intake team?** They will use it to prepare for your first conversation.\n\n"
            "Please reply **yes** or **no**."
        ),
        "next": "COMPLETE",
        "field": "consent",
    },
}


class IntakeService:
    async def start_session(self, db: AsyncSession, chat_session_id: Optional[str] = None) -> Tuple[str, str]:
        """Start a new intake session. Returns (intake_id, first_question)."""
        intake_id = str(uuid.uuid4())

        session = IntakeSession(
            id=intake_id,
            chat_session_id=chat_session_id,
            state="GREETING",
            collected_data=json.dumps({}),
        )
        db.add(session)
        await db.commit()

        return intake_id, INTAKE_STATES["GREETING"]["question"]

    async def process_message(self, db: AsyncSession, intake_id: str, message: str) -> Tuple[str, str, bool, Optional[str]]:
        """Process an intake message. Returns (state, response, is_complete, summary)."""
        # Crisis check first
        crisis_tier, crisis_response = safety_service.check_crisis(message)
        if crisis_tier == 1:
            return "CRISIS", CRISIS_IMMEDIATE_RESPONSE, False, None

        result = await db.execute(select(IntakeSession).where(IntakeSession.id == intake_id))
        session = result.scalar_one_or_none()
        if not session:
            return "ERROR", "Session not found. Please start a new intake.", False, None

        current_state = session.state
        state_config = INTAKE_STATES.get(current_state)

        if not state_config:
            return "COMPLETE", "This intake session has already been completed.", True, session.summary

        # Save the response to collected data
        collected = json.loads(session.collected_data or "{}")
        field_name = state_config.get("field", current_state.lower())
        collected[field_name] = message

        # Handle consent state specially
        if current_state == "CONSENT":
            if message.lower().strip() in ["yes", "y", "yeah", "sure", "ok", "okay"]:
                session.consent_given = True
                summary = self._generate_summary(collected)
                session.summary = summary
                session.state = "COMPLETE"
                session.submitted_at = datetime.utcnow()
                session.collected_data = json.dumps(collected)
                await db.commit()

                response = (
                    "Thank you for your consent. I've created a summary for our intake team.\n\n"
                    "**Here's what will be shared:**\n\n"
                    f"{summary}\n\n"
                    "A member of the Road Home Program intake team will reach out to you soon. "
                    "If you need immediate support, please call **(312) 942-8387 (VETS)**.\n\n"
                    "Thank you for reaching out - it takes real courage."
                )
                return "COMPLETE", response, True, summary
            else:
                session.state = "COMPLETE"
                session.collected_data = json.dumps(collected)
                await db.commit()
                return "COMPLETE", (
                    "No problem at all. Your information will not be shared. "
                    "If you'd like to start the process again later, you're always welcome to. "
                    "You can also contact the Road Home Program directly at **(312) 942-8387**."
                ), True, None

        # Move to next state
        next_state = state_config["next"]
        session.state = next_state
        session.collected_data = json.dumps(collected)
        await db.commit()

        if next_state == "COMPLETE":
            return "COMPLETE", "Intake complete.", True, None

        next_config = INTAKE_STATES.get(next_state)
        acknowledgment = "Thank you for sharing that. "
        return next_state, acknowledgment + next_config["question"], False, None

    def _generate_summary(self, data: dict) -> str:
        """Generate a formatted summary for the intake team."""
        parts = ["**Intake Summary**\n"]

        if data.get("reason"):
            parts.append(f"**Reason for Contact:** {data['reason']}")
        if data.get("connection"):
            parts.append(f"**Military Connection:** {data['connection']}")
        if data.get("service_details"):
            parts.append(f"**Service Details:** {data['service_details']}")
        if data.get("location"):
            parts.append(f"**Location:** {data['location']}")
        if data.get("urgency"):
            parts.append(f"**Urgency Level:** {data['urgency']}")
        if data.get("family_needs"):
            parts.append(f"**Family Needs:** {data['family_needs']}")
        if data.get("contact_preference"):
            parts.append(f"**Preferred Contact:** {data['contact_preference']}")

        return "\n".join(parts)


intake_service = IntakeService()
