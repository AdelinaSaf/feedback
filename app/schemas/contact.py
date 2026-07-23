"""
Pydantic-схемы для контактной формы.
Все сообщения валидации — на русском языке.
"""

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

# Российский/международный формат телефона: +7..., 8..., или 10-15 цифр
PHONE_PATTERN = re.compile(r"^(\+?[1-9]\d{9,14}|8\d{10})$")


class ContactCreateRequest(BaseModel):
    """Тело запроса POST /api/contact."""

    name: str = Field(..., min_length=2, max_length=255, description="Имя отправителя")
    phone: str = Field(..., max_length=20, description="Номер телефона")
    email: EmailStr = Field(..., description="Email отправителя")
    comment: str = Field(..., min_length=10, max_length=5000, description="Текст обращения")

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "example": {
                "name": "Иван Петров",
                "phone": "+79991234567",
                "email": "ivan@example.com",
                "comment": "Хочу узнать подробности о вашем продукте и условиях сотрудничества.",
            }
        },
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if len(value) < 2:
            raise ValueError("Имя должно содержать минимум 2 символа")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        cleaned = re.sub(r"[\s\-()]", "", value)
        if not PHONE_PATTERN.match(cleaned):
            raise ValueError("Некорректный формат телефона")
        return cleaned

    @field_validator("comment")
    @classmethod
    def validate_comment(cls, value: str) -> str:
        if len(value) < 10:
            raise ValueError("Комментарий должен содержать минимум 10 символов")
        return value


class ContactCreateResponse(BaseModel):
    """Успешный ответ POST /api/contact."""

    статус: Literal["успех"] = "успех"
    сообщение: str = "Обращение успешно принято"
    тональность: str


class HealthResponse(BaseModel):
    """Ответ GET /api/health."""

    status: str
    db: str


class MetricsResponse(BaseModel):
    """Ответ GET /api/metrics."""

    статус: Literal["успех"] = "успех"
    всего_обращений: int
