"""Seed the initial admin user."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import select
from database import engine, async_session, init_db
from models.user import StaffUser
from core.security import hash_password
from config import settings


async def seed():
    await init_db()

    async with async_session() as db:
        # Check if admin exists
        result = await db.execute(
            select(StaffUser).where(StaffUser.username == settings.ADMIN_USERNAME)
        )
        existing = result.scalar_one_or_none()

        if existing:
            print(f"Admin user '{settings.ADMIN_USERNAME}' already exists")
            return

        admin = StaffUser(
            username=settings.ADMIN_USERNAME,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            full_name="Administrator",
            role="admin",
        )
        db.add(admin)
        await db.commit()
        print(f"Admin user '{settings.ADMIN_USERNAME}' created successfully")


if __name__ == "__main__":
    asyncio.run(seed())
