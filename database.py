"""
database.py — підключення до PostgreSQL
Використовує asyncpg (асинхронний драйвер) через SQLAlchemy async engine.
"""

import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()  # завантажує змінні з файлу .env

# ─── Параметри підключення ─────────────────────────────────────────────────────
# Можна задати через .env файл або напряму тут
DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = os.getenv("DB_PORT",     "5432")
DB_NAME     = os.getenv("DB_NAME",     "booking_db")
DB_USER     = os.getenv("DB_USER",     "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# asyncpg вимагає префікс postgresql+asyncpg://
DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}"
    f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ─── Async Engine ──────────────────────────────────────────────────────────────
# echo=True — виводить SQL-запити в консоль (зручно для дебагу, вимкни в продакшні)
engine = create_async_engine(DATABASE_URL, echo=False)

# ─── Фабрика сесій ────────────────────────────────────────────────────────────
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ─── Dependency для FastAPI (використовується через Depends) ──────────────────
async def get_db() -> AsyncSession:
    """
    Генератор сесії БД.
    FastAPI автоматично закриває сесію після завершення запиту.

    Приклад використання в роутері:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise