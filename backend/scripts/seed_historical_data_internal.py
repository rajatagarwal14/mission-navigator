"""
Seed 30 days of realistic historical data using the app's own database connection.
Called from main.py on startup when SEED_DEMO_DATA=true and DB is empty.
"""
import asyncio
import json
import random
import uuid
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database import async_session, init_db
from models.conversation import ChatSession, ChatMessage
from models.analytics import QueryLog, ResourceClick
from models.intake import IntakeSession

VETERAN_QUESTIONS = [
    "What mental health services does Road Home offer?",
    "How do I schedule an appointment?",
    "Is there a cost for treatment at Road Home?",
    "I'm a Vietnam veteran, can I still get help?",
    "My spouse is struggling with my PTSD, is there help for families?",
    "What is the Accelerated Treatment Program?",
    "Do you treat MST (military sexual trauma)?",
    "I have trouble sleeping and keep having nightmares, what can you do?",
    "What is EMDR therapy and does Road Home offer it?",
    "Can I get help even with a less than honorable discharge?",
    "How long does the treatment program last?",
    "Do you offer telehealth or virtual appointments?",
    "I'm a caregiver for a veteran, can I get support?",
    "My child is having problems since I came back from deployment",
    "What are the symptoms of PTSD?",
    "I don't want medication, are there other options?",
    "Is there a support group for veterans at Road Home?",
    "I'm active duty, can I still use your services?",
    "My husband won't admit he needs help, what can I do?",
    "Are services available for National Guard members?",
    "What is the Do You Love a Vet program?",
    "I need help with substance use and mental health together",
    "How is Road Home different from the VA?",
    "Can you help with anxiety and depression from deployment?",
    "What happens at the first appointment?",
    "I served in Iraq and Afghanistan, do you specialize in combat trauma?",
    "How do I get a referral to Road Home?",
    "Can I bring a family member to my appointment?",
    "Does Road Home accept insurance?",
    "What is CPT therapy and is it effective for PTSD?",
]

ASSISTANT_RESPONSES = [
    "The Road Home Program offers a range of no-cost mental health services including the Accelerated Treatment Program (ATP), outpatient therapy, couples counseling, and caregiver support. Call (312) 942-8387 to get started.",
    "Scheduling is easy — just call (312) 942-8387 (VETS) or visit roadhomeprogram.org. The intake team will walk you through the process.",
    "All Road Home Program services are completely FREE, regardless of your discharge status. This is one of the things that makes Road Home unique.",
    "Absolutely. Road Home serves veterans of ALL eras — Vietnam, Gulf War, post-9/11, and more. Your service matters.",
    "Yes, family support is a core part of what we do. Road Home offers couples counseling, family therapy, and the 'Do You Love a Vet' support group.",
    "The Accelerated Treatment Program (ATP) is an intensive outpatient program that compresses months of treatment into a focused 2-3 week period.",
    "Yes, Road Home has experience treating MST survivors with trauma-informed, compassionate care. All services are confidential.",
    "What you're describing — sleep problems and nightmares — are common symptoms of PTSD. Road Home specializes in CPT and EMDR, which are very effective.",
    "EMDR (Eye Movement Desensitization and Reprocessing) is an evidence-based therapy for trauma. Road Home clinicians are trained in EMDR.",
    "Yes — Road Home serves veterans regardless of discharge status. All services are at no cost.",
    "The ATP is typically 2-3 weeks of intensive daily treatment. The intake team will help determine the right level of care for you.",
    "Road Home offers both in-person and telehealth appointments. Call (312) 942-8387 to discuss what works best for you.",
    "Absolutely. Caregivers are heroes too. Road Home offers dedicated caregiver support groups and counseling.",
]

RESOURCES = [
    "Road Home Program",
    "Veterans Crisis Line",
    "TRICARE Mental Health",
    "Military OneSource",
    "VA Mental Health Services",
    "Do You Love a Vet Support Group",
    "Accelerated Treatment Program (ATP)",
    "Warrior Care Network",
    "Cohen Veterans Network",
    "Give an Hour",
    "Headstrong Project",
    "SAMHSA Helpline",
]

CRISIS_QUESTIONS = [
    "I don't want to be here anymore",
    "I've been thinking about hurting myself",
    "I feel like ending it all",
    "I can't take this pain anymore",
]

CRISIS_RESPONSE = (
    "I hear you, and I want you to know that you are not alone. "
    "Please reach out to the Veterans Crisis Line right now: Call 988 (press 1), "
    "Text 838255. Road Home Program is also available at (312) 942-8387. "
    "You don't have to face this alone — trained counselors are available 24/7."
)


def sessions_for_day(base_date, days_back):
    weekday = base_date.weekday()
    progress = max(0.5, 1.0 - (days_back / 30) * 0.4)
    base = random.randint(5, 12) if weekday < 5 else random.randint(2, 5)
    return max(1, int(base * progress))


def rand_time(base_date):
    return base_date.replace(
        hour=random.randint(8, 20),
        minute=random.randint(0, 59),
        second=random.randint(0, 59),
        microsecond=0,
    )


async def seed():
    await init_db()

    async with async_session() as db:
        # Double-check not already seeded
        result = await db.execute(select(func.count(QueryLog.id)))
        if (result.scalar() or 0) >= 10:
            print("Already seeded, skipping.")
            return

        now = datetime.utcnow()
        crisis_days = set(random.sample(range(2, 28), 6))
        total = {"sessions": 0, "messages": 0, "logs": 0, "clicks": 0}

        for days_back in range(29, -1, -1):
            base_date = (now - timedelta(days=days_back)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            for s_idx in range(sessions_for_day(base_date, days_back)):
                session_id = str(uuid.uuid4())
                session_time = rand_time(base_date)
                is_crisis = (days_back in crisis_days and s_idx == 0)
                num_exchanges = 1 if is_crisis else random.randint(2, 6)
                msg_time = session_time
                session_resources = []

                session = ChatSession(
                    id=session_id,
                    started_at=session_time,
                    last_activity=session_time,
                    message_count=num_exchanges * 2,
                    crisis_flagged=is_crisis,
                    source=random.choice(["widget", "widget", "intake"]),
                )
                db.add(session)

                for ex in range(num_exchanges):
                    if is_crisis and ex == 0:
                        user_q = random.choice(CRISIS_QUESTIONS)
                        asst_r = CRISIS_RESPONSE
                        resources = []
                        crisis_tier = 1
                    else:
                        user_q = random.choice(VETERAN_QUESTIONS)
                        asst_r = random.choice(ASSISTANT_RESPONSES)
                        resources = random.sample(RESOURCES, random.randint(1, 3))
                        session_resources.extend(resources)
                        crisis_tier = None

                    msg_time += timedelta(minutes=random.randint(1, 4))
                    db.add(ChatMessage(session_id=session_id, role="user", content=user_q,
                                       created_at=msg_time, crisis_tier=crisis_tier))

                    msg_time += timedelta(seconds=random.randint(3, 20))
                    db.add(ChatMessage(session_id=session_id, role="assistant", content=asst_r,
                                       created_at=msg_time, crisis_tier=crisis_tier,
                                       resources_cited=json.dumps(resources) if resources else None))

                    db.add(QueryLog(session_id=session_id, query_text=user_q, response_text=asst_r,
                                    resources_cited=json.dumps(resources), crisis_tier=crisis_tier,
                                    response_time_ms=random.randint(350, 2800), created_at=msg_time))
                    total["logs"] += 1

                session.last_activity = msg_time
                total["sessions"] += 1
                total["messages"] += num_exchanges * 2

                for res in set(session_resources):
                    if random.random() < 0.65:
                        db.add(ResourceClick(
                            session_id=session_id, resource_name=res,
                            resource_url="https://roadhomeprogram.org",
                            clicked_at=session_time + timedelta(minutes=random.randint(2, 15)),
                        ))
                        total["clicks"] += 1

            # Commit per day to avoid huge transactions
            await db.commit()

        print(f"Seeded: {total['sessions']} sessions, {total['messages']} messages, "
              f"{total['logs']} logs, {total['clicks']} clicks")

        # Seed intake submissions
        await _seed_intake(db, now, total)
        print(f"Intake submissions seeded: {total.get('intake', 0)}")


INTAKE_SUMMARIES = [
    {
        "connection": "veteran", "branch": "Army", "era": "Post-9/11 (OEF/OIF)",
        "concerns": "PTSD and sleep difficulties following two combat deployments to Afghanistan",
        "location": "Illinois", "urgency": "moderate", "family": "spouse and two children",
    },
    {
        "connection": "family_member", "branch": "N/A", "era": "N/A",
        "concerns": "Supporting husband who served in the Marine Corps and is struggling with anger and isolation",
        "location": "Illinois", "urgency": "high", "family": "married with children",
    },
    {
        "connection": "veteran", "branch": "Navy", "era": "Gulf War",
        "concerns": "Depression, survivor's guilt, and difficulty reintegrating into civilian life",
        "location": "Indiana", "urgency": "moderate", "family": "single",
    },
    {
        "connection": "veteran", "branch": "Air Force", "era": "Post-9/11",
        "concerns": "MST-related trauma and anxiety affecting work and relationships",
        "location": "Illinois", "urgency": "high", "family": "partner",
    },
    {
        "connection": "caregiver", "branch": "N/A", "era": "N/A",
        "concerns": "Caring for a Vietnam veteran parent with PTSD and dementia, seeking respite and support",
        "location": "Illinois", "urgency": "moderate", "family": "adult child caregiver",
    },
    {
        "connection": "veteran", "branch": "Marines", "era": "Post-9/11 (OEF/OIF)",
        "concerns": "TBI-related symptoms combined with PTSD, having difficulty maintaining employment",
        "location": "Wisconsin", "urgency": "high", "family": "spouse",
    },
    {
        "connection": "veteran", "branch": "Army National Guard", "era": "Post-9/11",
        "concerns": "Anxiety, hypervigilance, and nightmares since returning from Iraq deployment",
        "location": "Illinois", "urgency": "low", "family": "married with children",
    },
    {
        "connection": "family_member", "branch": "N/A", "era": "N/A",
        "concerns": "Son recently returned from Afghanistan and is withdrawn, drinking heavily",
        "location": "Illinois", "urgency": "high", "family": "parent of veteran",
    },
    {
        "connection": "veteran", "branch": "Coast Guard", "era": "Vietnam",
        "concerns": "Long-untreated PTSD, recurring flashbacks, and social isolation",
        "location": "Illinois", "urgency": "moderate", "family": "widowed",
    },
    {
        "connection": "veteran", "branch": "Army", "era": "Post-9/11",
        "concerns": "Transitioning out of active duty, struggling with identity and purpose",
        "location": "Illinois", "urgency": "low", "family": "engaged, no children yet",
    },
    {
        "connection": "veteran", "branch": "Marines", "era": "Gulf War",
        "concerns": "Chronic pain and PTSD, previous suicide attempt two years ago",
        "location": "Illinois", "urgency": "high", "family": "divorced, children nearby",
    },
    {
        "connection": "family_member", "branch": "N/A", "era": "N/A",
        "concerns": "Wife of active duty service member dealing with deployment stress and anxiety",
        "location": "Illinois", "urgency": "moderate", "family": "two young children",
    },
]


def _make_summary(d: dict) -> str:
    return (
        f"**Connection to Service:** {d['connection'].replace('_', ' ').title()}\n"
        f"**Branch:** {d['branch']}\n"
        f"**Service Era:** {d['era']}\n"
        f"**Primary Concerns:** {d['concerns']}\n"
        f"**Location (State):** {d['location']}\n"
        f"**Urgency:** {d['urgency'].title()}\n"
        f"**Family Situation:** {d['family'].title()}\n"
        f"**Preferred Contact:** Phone call in the morning"
    )


async def _seed_intake(db: AsyncSession, now: datetime, total: dict):
    total["intake"] = 0
    for i, info in enumerate(INTAKE_SUMMARIES):
        days_back = random.randint(1, 29)
        submitted = now - timedelta(days=days_back, hours=random.randint(0, 8),
                                     minutes=random.randint(0, 59))
        reviewed = i < 8  # first 8 are reviewed, rest pending

        session_id = str(uuid.uuid4())
        # Create a matching chat session for intake
        chat_sess = ChatSession(
            id=session_id,
            started_at=submitted - timedelta(minutes=random.randint(5, 20)),
            last_activity=submitted,
            message_count=random.randint(8, 16),
            crisis_flagged=False,
            source="intake",
        )
        db.add(chat_sess)

        intake = IntakeSession(
            id=str(uuid.uuid4()),
            chat_session_id=session_id,
            state="COMPLETED",
            collected_data=json.dumps(info),
            summary=_make_summary(info),
            consent_given=True,
            submitted_at=submitted,
            reviewed_at=submitted + timedelta(hours=random.randint(2, 48)) if reviewed else None,
            created_at=submitted - timedelta(minutes=random.randint(5, 20)),
        )
        db.add(intake)
        total["intake"] = i + 1

    await db.commit()


if __name__ == "__main__":
    asyncio.run(seed())
