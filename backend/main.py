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
    # Startup
    await init_db()
    print(f"Mission Navigator started in {settings.ENVIRONMENT} mode")

    # Safe schema migrations (add new columns if missing)
    try:
        from database import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            # Add ip_address to chat_sessions if not exists
            if "postgresql" in str(engine.url):
                await conn.execute(text(
                    "ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS ip_address VARCHAR;"
                ))
            else:
                # SQLite doesn't support IF NOT EXISTS for columns
                try:
                    await conn.execute(text("ALTER TABLE chat_sessions ADD COLUMN ip_address VARCHAR;"))
                except Exception:
                    pass  # Column already exists
        print("Schema migration check complete")
    except Exception as e:
        print(f"Schema migration skipped: {e}")

    # Auto-seed admin user if not exists
    try:
        from database import async_session
        from sqlalchemy import select
        from models.user import StaffUser
        import bcrypt
        async with async_session() as db:
            result = await db.execute(select(StaffUser).where(StaffUser.username == settings.ADMIN_USERNAME))
            if not result.scalar_one_or_none():
                hashed = bcrypt.hashpw(settings.ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
                admin = StaffUser(username=settings.ADMIN_USERNAME, password_hash=hashed, full_name="Administrator", role="admin")
                db.add(admin)
                await db.commit()
                print(f"Admin user '{settings.ADMIN_USERNAME}' created")
    except Exception as e:
        print(f"Admin seed skipped: {e}")

    # Seed demo historical data if SEED_DEMO_DATA=true and DB is empty
    if os.environ.get("SEED_DEMO_DATA") == "true":
        try:
            from sqlalchemy import select, func
            from models.analytics import QueryLog
            from database import async_session as _async_session
            async with _async_session() as _db:
                result = await _db.execute(select(func.count(QueryLog.id)))
                log_count = result.scalar() or 0
            if log_count < 10:
                print("Seeding demo historical data...")
                import subprocess
                subprocess.run(
                    ["python3", "scripts/seed_historical_data_internal.py"],
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    check=True,
                )
                print("Demo data seeded successfully")
            else:
                print(f"Demo data already present ({log_count} logs) — skipping seed")
        except Exception as e:
            print(f"Demo data seed skipped: {e}")

    # Auto-ingest knowledge base if empty
    from services.knowledge_service import knowledge_service
    if knowledge_service.get_collection_count() == 0 and settings.GEMINI_API_KEY:
        print("Knowledge base empty - running auto-ingestion...")
        try:
            import subprocess
            subprocess.run(
                ["python3", "scripts/ingest_bridge_guide.py"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                check=True,
            )
            print(f"Ingestion complete: {knowledge_service.get_collection_count()} chunks")
        except Exception as e:
            print(f"Auto-ingestion failed: {e}")

    yield
    # Shutdown
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
