"""
database.py — підключення до Neon PostgreSQL
Читає змінні які Vercel+Neon створює автоматично (PGHOST, PGUSER і т.д.)
"""
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Vercel+Neon автоматично створює PGHOST, PGUSER, PGPASSWORD, PGDATABASE
# Залишаємо DB_* як fallback для локальної розробки
DB_HOST     = os.getenv("PGHOST")     or os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("PGPORT")     or os.getenv("DB_PORT",     "5432")
DB_NAME     = os.getenv("PGDATABASE") or os.getenv("DB_NAME",     "booking_db")
DB_USER     = os.getenv("PGUSER")     or os.getenv("DB_USER",     "postgres")
DB_PASSWORD = os.getenv("PGPASSWORD") or os.getenv("DB_PASSWORD", "postgres")

DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

is_neon = DB_HOST and "neon.tech" in DB_HOST
connect_args = {"ssl": "require"} if is_neon else {}

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise