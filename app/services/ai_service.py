"""
Сервис анализа тональности комментария через Groq API (OpenAI SDK).
При ошибке или таймауте возвращает «неизвестный» — запрос не падает.
"""

import asyncio
from typing import Final

from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError

from app.core.config import settings
from app.core.logger import logger

# Допустимые значения тональности на русском
VALID_SENTIMENTS: Final[set[str]] = {"позитивный", "негативный", "нейтральный", "неизвестный"}

# Маппер: английские ответы модели -> русский
SENTIMENT_MAPPER: Final[dict[str, str]] = {
    "positive": "позитивный",
    "negative": "негативный",
    "neutral": "нейтральный",
    "unknown": "неизвестный",
    "позитивный": "позитивный",
    "негативный": "негативный",
    "нейтральный": "нейтральный",
    "неизвестный": "неизвестный",
}

AI_PROMPT: Final[str] = (
    "Проанализируй тональность следующего текста обращения пользователя. "
    "Ответь ОДНИМ словом строго на русском языке: "
    "«позитивный», «негативный» или «нейтральный». "
    "Не добавляй пояснений, только одно слово.\n\n"
    "Текст: {comment}"
)


class AIService:
    """Интеграция с Groq через OpenAI-совместимый клиент."""

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        if settings.GROQ_API_KEY:
            self._client = AsyncOpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url=settings.GROQ_BASE_URL,
                timeout=settings.AI_TIMEOUT,
            )

    @staticmethod
    def normalize_sentiment(raw: str) -> str:
        """
        Нормализует ответ AI: переводит английские слова в русские,
        приводит к нижнему регистру и проверяет допустимость.
        """
        cleaned = raw.strip().lower().rstrip(".")
        mapped = SENTIMENT_MAPPER.get(cleaned)
        if mapped:
            return mapped
        # Поиск ключевых слов внутри ответа
        for key, value in SENTIMENT_MAPPER.items():
            if key in cleaned:
                return value
        return "неизвестный"

    async def analyze_sentiment(self, comment: str) -> str:
        """
        Анализирует тональность комментария.
        При любой ошибке API возвращает «неизвестный» и логирует проблему.
        """
        if not self._client:
            logger.warning("GROQ_API_KEY не задан — тональность установлена как «неизвестный»")
            return "неизвестный"

        prompt = AI_PROMPT.format(comment=comment)

        try:
            # Дополнительная защита от зависания — asyncio.wait_for
            response = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=settings.GROQ_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": "Ты анализатор тональности текста. Отвечай только одним словом на русском.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=10,
                    temperature=0,
                ),
                timeout=settings.AI_TIMEOUT,
            )

            raw_sentiment = response.choices[0].message.content or ""
            sentiment = self.normalize_sentiment(raw_sentiment)
            logger.info("AI определил тональность: %s (исходный ответ: %s)", sentiment, raw_sentiment.strip())
            return sentiment

        except asyncio.TimeoutError:
            logger.error("Таймаут AI-сервиса (%s сек) — тональность: неизвестный", settings.AI_TIMEOUT)
            return "неизвестный"
        except APITimeoutError as exc:
            logger.error("Таймаут запроса к Groq API: %s — тональность: неизвестный", exc)
            return "неизвестный"
        except RateLimitError as exc:
            logger.error("Превышен лимит Groq API: %s — тональность: неизвестный", exc)
            return "неизвестный"
        except APIError as exc:
            logger.error("Ошибка Groq API: %s — тональность: неизвестный", exc)
            return "неизвестный"
        except Exception as exc:
            logger.error("Непредвиденная ошибка AI-сервиса: %s — тональность: неизвестный", exc)
            return "неизвестный"


# Singleton для переиспользования клиента
ai_service = AIService()
