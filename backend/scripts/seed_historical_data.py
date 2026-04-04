"""
Seed realistic 30-day historical data into the Mission Navigator PostgreSQL database.
Uses psycopg2 (sync) for simplicity. Run once to populate dashboard for MVP demo.
"""
import json
import random
import uuid
from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_values

DB_URL = (
    "host=dpg-d78coup4tr6s73c1l5tg-a.oregon-postgres.render.com "
    "port=5432 "
    "dbname=mission_navigator "
    "user=mission_nav_user "
    "password=fs5k7IKYLwJDP8ZLJ3nX5LUmbzkksL5h "
    "sslmode=require"
)

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
    "Can I get help even if I had a less than honorable discharge?",
    "How long does the treatment program last?",
    "Do you offer telehealth or virtual appointments?",
    "I'm a caregiver for a veteran, can I get support?",
    "My child is having problems since I came back from deployment",
    "What are the symptoms of PTSD?",
    "I don't want medication, do you have other treatment options?",
    "Is there a support group for veterans at Road Home?",
    "I'm active duty, can I still use your services?",
    "My husband won't admit he needs help, what can I do?",
    "Are services available for National Guard members?",
    "What is the Do You Love a Vet program?",
    "I need help with substance use and mental health at the same time",
    "How is Road Home different from the VA?",
    "Can you help with anxiety and depression from deployment?",
    "What happens at the first appointment?",
    "I served in Iraq and Afghanistan, do you specialize in combat-related trauma?",
    "How do I get a referral to Road Home?",
    "Can I bring a family member to my appointment?",
    "Does Road Home accept insurance?",
    "What is CPT therapy?",
]

ASSISTANT_RESPONSES = [
    "The Road Home Program offers a range of no-cost mental health services including the Accelerated Treatment Program (ATP), outpatient therapy, couples counseling, and caregiver support. Call (312) 942-8387 to get started.",
    "Scheduling is easy — just call (312) 942-8387 (VETS) or visit roadhomeprogram.org. The intake team will walk you through the process.",
    "All Road Home Program services are completely FREE, regardless of your discharge status or whether you're enrolled in VA care. This is one of the things that makes Road Home unique.",
    "Absolutely. Road Home serves veterans of ALL eras — Vietnam, Gulf War, post-9/11, and more. Your service matters, and so does your wellbeing.",
    "Yes, family support is a core part of what we do. Road Home offers couples counseling, family therapy, and the 'Do You Love a Vet' support group specifically for military families.",
    "The Accelerated Treatment Program (ATP) is an intensive outpatient program that compresses months of treatment into a focused 2-3 week period. It's designed for veterans who need intensive support.",
    "Yes, Road Home has experience treating MST survivors with trauma-informed, compassionate care. All services are confidential.",
    "What you're describing — sleep problems and nightmares — are common symptoms of PTSD. Road Home specializes in evidence-based treatments like CPT and EMDR that are very effective.",
    "EMDR (Eye Movement Desensitization and Reprocessing) is an evidence-based therapy for trauma. Yes, Road Home clinicians are trained in EMDR and use it as part of the ATP and outpatient care.",
    "Yes — Road Home serves veterans regardless of discharge status. You do not need an honorable discharge to receive care. All services are at no cost.",
    "The ATP is typically 2-3 weeks of intensive daily treatment. Outpatient therapy varies by individual need. The intake team will help determine the right level of care for you.",
    "Road Home offers both in-person and telehealth appointments. Call (312) 942-8387 to discuss what works best for your situation.",
    "Absolutely. Caregivers are heroes too. Road Home offers dedicated caregiver support groups and counseling for those caring for veterans.",
]

RESOURCES = [
    "Road Home Program",
    "Veterans Crisis Line",
    "TRICARE Mental Health",
    "Military OneSource",
    "VA Mental Health Services",
    "Do You Love a Vet Support Group",
    "Accelerated Treatment Program (ATP)",
    "Rush University Medical Center",
    "Warrior Care Network",
    "Cohen Veterans Network",
    "Give an Hour",
    "Headstrong Project",
    "SAMHSA Helpline",
    "Steven A. Cohen Military Family Clinic",
]

CRISIS_QUESTIONS = [
    "I don't want to be here anymore",
    "I've been thinking about hurting myself",
    "I feel like ending it all",
    "I can't take this pain anymore",
    "I have a plan to end my life",
]

CRISIS_RESPONSE = (
    "I hear you, and I want you to know that you are not alone. "
    "Please reach out to the Veterans Crisis Line right now: Call 988 (press 1), "
    "Text 838255, or Chat at veteranscrisisline.net. "
    "Road Home Program is also available at (312) 942-8387. "
    "You don't have to face this alone — trained counselors are available 24/7."
)


def sessions_for_day(base_date, days_back):
    weekday = base_date.weekday()
    progress = max(0.5, 1.0 - (days_back / 30) * 0.4)
    if weekday < 5:
        base = random.randint(5, 12)
    else:
        base = random.randint(2, 5)
    return max(1, int(base * progress))


def rand_time(base_date):
    h = random.randint(8, 20)
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return base_date.replace(hour=h, minute=m, second=s, microsecond=0)


def main():
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    # Create tables
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id VARCHAR PRIMARY KEY,
            started_at TIMESTAMP DEFAULT NOW(),
            last_activity TIMESTAMP DEFAULT NOW(),
            message_count INTEGER DEFAULT 0,
            crisis_flagged BOOLEAN DEFAULT FALSE,
            user_agent VARCHAR,
            source VARCHAR DEFAULT 'widget'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR REFERENCES chat_sessions(id),
            role VARCHAR NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            crisis_tier INTEGER,
            resources_cited TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS query_logs (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR,
            query_text TEXT NOT NULL,
            response_text TEXT,
            resources_cited TEXT,
            crisis_tier INTEGER,
            response_time_ms INTEGER,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS resource_clicks (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR,
            resource_name VARCHAR NOT NULL,
            resource_url VARCHAR,
            clicked_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()

    # Check if already seeded
    cur.execute("SELECT COUNT(*) FROM query_logs")
    count = cur.fetchone()[0]
    if count > 0:
        print(f"Already have {count} query logs — skipping seed.")
        conn.close()
        return

    print("Seeding 30 days of historical data...")
    now = datetime.utcnow()
    crisis_days = set(random.sample(range(2, 28), 6))

    sessions_data = []
    messages_data = []
    logs_data = []
    clicks_data = []

    total_sessions = 0

    for days_back in range(29, -1, -1):
        base_date = now - timedelta(days=days_back)
        base_date = base_date.replace(hour=0, minute=0, second=0, microsecond=0)
        num_sessions = sessions_for_day(base_date, days_back)

        for s_idx in range(num_sessions):
            session_id = str(uuid.uuid4())
            session_time = rand_time(base_date)
            is_crisis = (days_back in crisis_days and s_idx == 0)

            num_exchanges = 1 if is_crisis else random.randint(2, 6)
            msg_time = session_time
            session_resources = []

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
                messages_data.append((session_id, "user", user_q, msg_time, crisis_tier, None))
                msg_time += timedelta(seconds=random.randint(3, 20))
                messages_data.append((session_id, "assistant", asst_r, msg_time, crisis_tier,
                                       json.dumps(resources) if resources else None))
                logs_data.append((session_id, user_q, asst_r, json.dumps(resources),
                                   crisis_tier, random.randint(350, 2800), msg_time))

            last_activity = msg_time
            sessions_data.append((session_id, session_time, last_activity,
                                    num_exchanges * 2, is_crisis,
                                    random.choice(["widget", "widget", "intake"]),))

            # Resource clicks
            for res in set(session_resources):
                if random.random() < 0.65:
                    clicks_data.append((session_id, res, "https://roadhomeprogram.org",
                                         session_time + timedelta(minutes=random.randint(2, 15))))

            total_sessions += 1

    # Bulk insert
    print(f"Inserting {len(sessions_data)} sessions...")
    execute_values(cur,
        "INSERT INTO chat_sessions (id, started_at, last_activity, message_count, crisis_flagged, source) VALUES %s",
        sessions_data)

    print(f"Inserting {len(messages_data)} messages...")
    execute_values(cur,
        "INSERT INTO chat_messages (session_id, role, content, created_at, crisis_tier, resources_cited) VALUES %s",
        messages_data)

    print(f"Inserting {len(logs_data)} query logs...")
    execute_values(cur,
        "INSERT INTO query_logs (session_id, query_text, response_text, resources_cited, crisis_tier, response_time_ms, created_at) VALUES %s",
        logs_data)

    print(f"Inserting {len(clicks_data)} resource clicks...")
    execute_values(cur,
        "INSERT INTO resource_clicks (session_id, resource_name, resource_url, clicked_at) VALUES %s",
        clicks_data)

    conn.commit()
    cur.close()
    conn.close()

    print(f"\nDone! Seeded:")
    print(f"  {len(sessions_data)} sessions")
    print(f"  {len(messages_data)} messages")
    print(f"  {len(logs_data)} query logs")
    print(f"  {len(clicks_data)} resource clicks")
    print(f"  {len(crisis_days)} crisis events flagged")


if __name__ == "__main__":
    main()
