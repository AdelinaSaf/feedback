"""
Модуль конфигурации приложения.
Загружает настройки из переменных окружения (.env) через pydantic-settings.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Централизованные настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Основные параметры приложения
    APP_NAME: str = "Contact Form API"
    DEBUG: bool = False

    # PostgreSQL (async SQLAlchemy + asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/contact_db"

    # Groq API (совместим с OpenAI SDK)
    GROQ_API_KEY: str = ""
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    AI_TIMEOUT: float = 5.0

    # SMTP для отправки email
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_TLS: bool = True
    OWNER_EMAIL: str = ""

    # CORS — список разрешённых origin через запятую
    CORS_ORIGINS: str = "*"

    # Логирование
    LOG_FILE: str = "app.log"
    LOG_MAX_BYTES: int = 10 * 1024 * 1024
    LOG_BACKUP_COUNT: int = 5

    # Rate limiting (slowapi)
    RATE_LIMIT: str = "5/minute"

    @property
    def cors_origins_list(self) -> list[str]:
        """Преобразует строку CORS_ORIGINS в список."""
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
