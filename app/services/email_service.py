"""
Сервис отправки email через SMTP.
Используется как фоновая задача FastAPI BackgroundTasks.
"""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings
from app.core.logger import logger
from app.schemas.contact import ContactCreateRequest


class EmailService:
    """Отправка уведомлений владельцу сайта и копии пользователю."""

    def _build_message(
        self,
        to_email: str,
        subject: str,
        body: str,
    ) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM or settings.SMTP_USER
        msg["To"] = to_email
        msg.attach(MIMEText(body, "plain", "utf-8"))
        return msg

    def _send_sync(self, to_email: str, subject: str, body: str) -> None:
        """Синхронная отправка через smtplib (вызывается в thread pool)."""
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.warning("SMTP не настроен — письмо на %s не отправлено", to_email)
            return

        message = self._build_message(to_email, subject, body)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            if settings.SMTP_TLS:
                server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(
                settings.SMTP_FROM or settings.SMTP_USER,
                to_email,
                message.as_string(),
            )

    async def send_email(self, to_email: str, subject: str, body: str) -> None:
        """Async-обёртка: smtplib выполняется в отдельном потоке."""
        try:
            await asyncio.to_thread(self._send_sync, to_email, subject, body)
            logger.info("Email успешно отправлен на %s", to_email)
        except Exception as exc:
            logger.error("Ошибка отправки email на %s: %s", to_email, exc)

    async def send_contact_notifications(
        self,
        data: ContactCreateRequest,
        sentiment: str,
    ) -> None:
        """
        Отправляет два письма:
        1) Владельцу сайта — полная информация об обращении.
        2) Пользователю — подтверждение получения обращения.
        """
        owner_body = (
            f"Новое обращение через контактную форму\n\n"
            f"Имя: {data.name}\n"
            f"Телефон: {data.phone}\n"
            f"Email: {data.email}\n"
            f"Тональность: {sentiment}\n\n"
            f"Комментарий:\n{data.comment}"
        )

        user_body = (
            f"Здравствуйте, {data.name}!\n\n"
            f"Мы получили ваше обращение и свяжемся с вами в ближайшее время.\n\n"
            f"Ваш комментарий:\n{data.comment}\n\n"
            f"С уважением,\nКоманда поддержки"
        )

        # Письмо владельцу
        if settings.OWNER_EMAIL:
            await self.send_email(
                to_email=settings.OWNER_EMAIL,
                subject=f"Новое обращение от {data.name}",
                body=owner_body,
            )
        else:
            logger.warning("OWNER_EMAIL не задан — уведомление владельцу не отправлено")

        # Копия пользователю
        await self.send_email(
            to_email=str(data.email),
            subject="Ваше обращение принято",
            body=user_body,
        )


email_service = EmailService()
