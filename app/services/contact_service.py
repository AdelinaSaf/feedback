"""
Сервисный слой контактной формы.
Оркестрирует AI-анализ, сохранение в БД и фоновую отправку email.
"""

from fastapi import BackgroundTasks

from app.core.logger import logger
from app.repositories.contact_repo import ContactRepository
from app.schemas.contact import ContactCreateRequest, ContactCreateResponse
from app.services.ai_service import ai_service
from app.services.email_service import email_service


class ContactService:
    """
    Бизнес-логика обработки обращений.
    Routers -> Services -> Repositories
    """

    def __init__(self, repository: ContactRepository) -> None:
        self._repository = repository

    async def process_contact(
        self,
        data: ContactCreateRequest,
        background_tasks: BackgroundTasks,
    ) -> ContactCreateResponse:
        """
        Полный цикл обработки обращения:
        1) AI-анализ тональности (с graceful fallback)
        2) Сохранение в PostgreSQL
        3) Фоновая отправка email
        """
        # Шаг 1: анализ тональности — ошибка AI не прерывает запрос
        sentiment = await ai_service.analyze_sentiment(data.comment)

        # Шаг 2: сохранение в базу данных
        await self._repository.create(data, sentiment)

        logger.info(
            "Получен запрос от %s, тональность: %s",
            data.email,
            sentiment,
        )

        # Шаг 3: фоновая отправка писем (не блокирует ответ клиенту)
        background_tasks.add_task(
            email_service.send_contact_notifications,
            data,
            sentiment,
        )

        return ContactCreateResponse(тональность=sentiment)
