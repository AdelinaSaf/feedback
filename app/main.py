"""
Точка входа FastAPI-приложения.
Настройка CORS, middleware, lifespan, exception handlers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.database import close_db, init_db
from app.core.exceptions import register_exception_handlers
from app.core.limiter import limiter
from app.core.logger import logger
from app.routers.contact import router as contact_router

# Импорт моделей для регистрации в metadata
import app.models.contact  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan: управление жизненным циклом приложения.
    При старте — инициализация БД, при остановке — закрытие соединений.
    """
    logger.info("Запуск приложения %s", settings.APP_NAME)
    await init_db()
    yield
    await close_db()
    logger.info("Приложение остановлено")


app = FastAPI(
    title=settings.APP_NAME,
    description="Production-ready API контактной формы с AI-анализом тональности",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiting middleware
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Глобальные обработчики исключений (русские сообщения)
register_exception_handlers(app)

# Роутеры
app.include_router(contact_router)


@app.get("/", include_in_schema=False)
async def root():
    """Корневой эндпоинт — информация об API."""
    return {
        "статус": "успех",
        "сообщение": "Contact Form API работает",
        "документация": "/docs",
    }
