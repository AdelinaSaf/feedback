"""
Роутеры API — слой представления.
Принимают HTTP-запросы, делегируют логику сервисному слою.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import check_db_connection, get_db_session
from app.core.limiter import limiter
from app.repositories.contact_repo import ContactRepository
from app.schemas.contact import (
    ContactCreateRequest,
    ContactCreateResponse,
    HealthResponse,
    MetricsResponse,
)
from app.services.contact_service import ContactService

router = APIRouter(prefix="/api", tags=["Контактная форма"])


def get_contact_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ContactRepository:
    """DI: создаёт репозиторий с текущей сессией БД."""
    return ContactRepository(session)


def get_contact_service(
    repository: ContactRepository = Depends(get_contact_repository),
) -> ContactService:
    """DI: создаёт сервис с инжектированным репозиторием."""
    return ContactService(repository)


@router.post(
    "/contact",
    response_model=ContactCreateResponse,
    summary="Отправить обращение через контактную форму",
    status_code=200,
)
@limiter.limit("5/minute")
async def submit_contact(
    request: Request,
    data: ContactCreateRequest,
    background_tasks: BackgroundTasks,
    service: ContactService = Depends(get_contact_service),
) -> ContactCreateResponse:
    """
    Принимает обращение пользователя:
    - валидирует данные (Pydantic)
    - ограничивает частоту запросов (5/мин на IP)
    - анализирует тональность через AI
    - сохраняет в PostgreSQL
    - отправляет email в фоне
    """
    return await service.process_contact(data, background_tasks)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Проверка состояния сервиса",
)
async def health_check() -> HealthResponse:
    """Возвращает статус приложения и подключения к БД."""
    db_ok = await check_db_connection()
    return HealthResponse(
        status="healthy",
        db="connected" if db_ok else "disconnected",
    )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Метрики обращений",
)
async def get_metrics(
    repository: ContactRepository = Depends(get_contact_repository),
) -> MetricsResponse:
    """Возвращает общее количество обращений в базе данных."""
    total = await repository.count_all()
    return MetricsResponse(всего_обращений=total)
