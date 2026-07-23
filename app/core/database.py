"""
Модуль подключения к PostgreSQL через async SQLAlchemy.
Управляет жизненным циклом engine и сессий.
"""

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings
from app.core.logger import logger


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency Injection: предоставляет async-сессию БД для каждого запроса.
    Гарантирует commit/rollback и закрытие сессии.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Создаёт таблицы при старте приложения (если не существуют)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("База данных инициализирована, таблицы проверены/созданы")


async def close_db() -> None:
    """Корректно закрывает пул соединений при остановке приложения."""
    await engine.dispose()
    logger.info("Соединение с базой данных закрыто")


async def check_db_connection() -> bool:
    """Проверяет доступность PostgreSQL."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.error("Ошибка подключения к базе данных: %s", exc)
        return False
