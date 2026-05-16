import sys
import os

# Ensure backend directory is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — every step wrapped so nothing can crash the server
    print("Mission Navigator starting up...")

    # 1. Init DB tables — retry until PostgreSQL wakes up (free tier sleeps too)
    import asyncio
    for attempt in range(1, 11):
        try:
            await init_db()
            print(f"DB tables ready (attempt {attempt})")
            break
        except Exception as e:
            print(f"DB not ready yet (attempt {attempt}/10): {e}")
            if attempt < 10:
                await asyncio.sleep(3)
            else:
                print("WARNING: DB init failed after 10 attempts — service may be degraded")

    print(f"Environment: {settings.ENVIRONMENT}")

    # 2. Schema migrations — add new columns safely
    try:
        from database import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            if "postgresql" in str(engine.url):
                await conn.execute(text(
                    "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS ip_address VARCHAR;"
                ))
            else:
                try:
                    await conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN ip_address VARCHAR;"))
                except Exception:
                    pass
        print("Schema migration OK")
    except Exception as e:
        print(f"Schema migration skipped (non-fatal): {e}")

    # 3. Auto-seed admin user — retry so PostgreSQL has time to wake up
    admin_seeded = False
    for attempt in range(1, 6):
        try:
            from database import async_session
            from sqlalchemy import select
            from models.user import StaffUser
            import bcrypt
            async with async_session() as db:
                result = await db.execute(select(StaffUser).where(StaffUser.username == settings.ADMIN_USERNAME))
                existing = result.scalar_one_or_none()
                if not existing:
                    hashed = bcrypt.hashpw(settings.ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
                    admin = StaffUser(
                        username=settings.ADMIN_USERNAME,
                        password_hash=hashed,
                        full_name="Administrator",
                        role="admin",
                    )
                    db.add(admin)
                    await db.commit()
                    print(f"Admin user created (attempt {attempt})")
                else:
                    print(f"Admin user exists (attempt {attempt})")
                admin_seeded = True
                break
        except Exception as e:
            print(f"Admin seed attempt {attempt}/5 failed: {e}")
            if attempt < 5:
                import asyncio
                await asyncio.sleep(3)
    if not admin_seeded:
        print("WARNING: Admin user could not be seeded — login may fail")

    # 4. Background tasks (demo seeding + ingestion) — never block startup
    import threading

    def _background_startup():
        import time
        time.sleep(5)  # Let the server fully start first

        # Seed demo data if needed
        if os.environ.get("SEED_DEMO_DATA") == "true":
            try:
                import asyncio, subprocess
                result = subprocess.run(
                    ["python3", "-c",
                     "import asyncio,sys; sys.path.insert(0,'.'); "
                     "from database import async_session; from sqlalchemy import select,func; "
                     "from models.analytics import QueryLog; "
                     "async def check(): \n"
                     "    async with async_session() as db:\n"
                     "        r = await db.execute(select(func.count(QueryLog.id)))\n"
                     "        return r.scalar() or 0\n"
                     "count = asyncio.run(check()); print(count)"],
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    capture_output=True, text=True, timeout=30,
                )
                log_count = int(result.stdout.strip() or "0")
                if log_count < 10:
                    subprocess.run(
                        ["python3", "scripts/seed_historical_data_internal.py"],
                        cwd=os.path.dirname(os.path.abspath(__file__)),
                        timeout=120,
                    )
                    print("Demo data seeded")
                else:
                    print(f"Demo data present ({log_count} logs)")
            except Exception as e:
                print(f"Background seed skipped: {e}")

        # Ingest knowledge base if empty
        try:
            from services.knowledge_service import knowledge_service
            if knowledge_service.get_collection_count() == 0 and settings.GEMINI_API_KEY:
                print("Knowledge base empty — ingesting in background...")
                subprocess2 = __import__("subprocess")
                subprocess2.run(
                    ["python3", "scripts/ingest_bridge_guide.py"],
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    timeout=300,
                )
                print("Knowledge base ingestion complete")
        except Exception as e:
            print(f"Background ingestion skipped: {e}")

    threading.Thread(target=_background_startup, daemon=True).start()
    print("Mission Navigator is ready ✓")

    yield

    print("Mission Navigator shutting down")


app = FastAPI(
    title="Mission Navigator API",
    description="AI-powered resource navigation for the Road Home Program - helping veterans and military families find mental health services",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
from routers.health import router as health_router
from routers.chat import router as chat_router
from routers.auth import router as auth_router
from routers.analytics import router as analytics_router
from routers.knowledge import router as knowledge_router
from routers.intake import router as intake_router

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(analytics_router)
app.include_router(knowledge_router)
app.include_router(intake_router)

# Serve frontend static files (production)
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.exists(frontend_dist):
    from fastapi.responses import FileResponse

    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    # SPA fallback: serve index.html for all non-API routes
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API or docs routes
        if full_path.startswith(("api/", "docs", "openapi.json", "health")):
            return None
        file_path = os.path.join(frontend_dist, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_dist, "index.html"))
else:
    @app.get("/")
    async def root():
        return {
            "service": "Mission Navigator",
            "description": "AI-powered resource navigation for the Road Home Program",
            "docs": "/docs",
            "health": "/health",
        }
