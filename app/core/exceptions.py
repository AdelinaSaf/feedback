"""
Глобальные обработчики исключений.
Все JSON-ответы об ошибках возвращаются строго на русском языке.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import SQLAlchemyError

from app.core.logger import logger


# Маппинг типов ошибок Pydantic на русские сообщения
PYDANTIC_ERROR_MESSAGES: dict[str, str] = {
    "string_too_short": "Значение слишком короткое",
    "string_pattern_mismatch": "Некорректный формат телефона",
    "value_error": "Некорректное значение поля",
    "missing": "Обязательное поле отсутствует",
    "type_error": "Некорректный тип данных",
}


def _translate_validation_errors(errors: list[dict]) -> list[dict]:
    """
    Преобразует ошибки валидации Pydantic в читаемый формат на русском.
    Использует кастомные сообщения из ctx, если они заданы.
    """
    translated: list[dict] = []

    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []) if loc != "body")
        error_type = error.get("type", "")
        msg = error.get("msg", "")

        # Если валидатор уже вернул русское сообщение — используем его
        ctx = error.get("ctx", {})
        if "error" in ctx and isinstance(ctx["error"], str):
            message = ctx["error"]
        elif error_type == "string_pattern_mismatch" and "phone" in field:
            message = "Некорректный формат телефона"
        elif error_type == "string_too_short" and "name" in field:
            message = "Имя должно содержать минимум 2 символа"
        elif error_type == "string_too_short" and "comment" in field:
            message = "Комментарий должен содержать минимум 10 символов"
        elif error_type == "value_error" and msg:
            message = msg
        else:
            message = PYDANTIC_ERROR_MESSAGES.get(error_type, msg or "Ошибка валидации данных")

        translated.append({"поле": field or "тело запроса", "сообщение": message})

    return translated


def register_exception_handlers(app: FastAPI) -> None:
    """Регистрирует все глобальные обработчики ошибок в приложении FastAPI."""

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning("Ошибка валидации запроса %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "статус": "ошибка",
                "сообщение": "Ошибка валидации данных",
                "детали": _translate_validation_errors(exc.errors()),
            },
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_exception_handler(
        request: Request, exc: RateLimitExceeded
    ) -> JSONResponse:
        logger.warning("Превышен лимит запросов с IP: %s", request.client.host if request.client else "неизвестно")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "статус": "ошибка",
                "сообщение": "Превышен лимит запросов. Разрешено не более 5 обращений в минуту.",
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.error("Ошибка базы данных при обработке %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "статус": "ошибка",
                "сообщение": "Внутренняя ошибка сервера при работе с базой данных",
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Непредвиденная ошибка при обработке %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "статус": "ошибка",
                "сообщение": "Внутренняя ошибка сервера",
            },
        )
