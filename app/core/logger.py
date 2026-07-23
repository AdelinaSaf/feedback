"""
Модуль настройки логирования.
Записывает логи в файл app.log с ротацией и дублирует в консоль.
"""

import logging
from logging.handlers import RotatingFileHandler

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Инициализирует логгер приложения.
    Все сообщения в лог-файле должны быть на русском языке.
    """
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    # Не добавлять обработчики повторно при повторном импорте
    if app_logger.handlers:
        return app_logger

    formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Ротация лог-файла при достижении максимального размера
    file_handler = RotatingFileHandler(
        filename=settings.LOG_FILE,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)

    app_logger.addHandler(file_handler)
    app_logger.addHandler(console_handler)

    return app_logger


logger = setup_logging()
