from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from config import settings

_db_url = settings.async_database_url
_is_sqlite = "sqlite" in _db_url
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

# pool_pre_ping revalidates connections before use (handles PostgreSQL sleeping on Render free tier)
engine = create_async_engine(
    _db_url,
    echo=settings.DEBUG,
    connect_args=_connect_args,
    pool_pre_ping=True,
    **({} if _is_sqlite else {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_recycle": 1800,
    }),
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
