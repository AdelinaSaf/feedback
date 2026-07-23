"""
ORM-модель обращения через контактную форму.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Contact(Base):
    """Таблица contact_requests — хранит обращения пользователей."""

    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    # Тональность: позитивный, негативный, нейтральный, неизвестный
    sentiment: Mapped[str] = mapped_column(String(50), nullable=False, default="неизвестный")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
