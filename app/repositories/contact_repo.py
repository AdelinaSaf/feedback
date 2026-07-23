"""
Репозиторий для работы с обращениями в PostgreSQL.
Слой Repositories — только операции с базой данных, без бизнес-логики.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import Contact
from app.schemas.contact import ContactCreateRequest


class ContactRepository:
    """Async-репозиторий для CRUD-операций с таблицей contacts."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: ContactCreateRequest, sentiment: str) -> Contact:
        """
        Сохраняет новое обращение с результатом анализа тональности.
        """
        contact = Contact(
            name=data.name,
            phone=data.phone,
            email=str(data.email),
            comment=data.comment,
            sentiment=sentiment,
        )
        self._session.add(contact)
        await self._session.flush()
        await self._session.refresh(contact)
        return contact

    async def count_all(self) -> int:
        """Возвращает общее количество обращений в базе."""
        result = await self._session.execute(select(func.count()).select_from(Contact))
        return result.scalar_one()
