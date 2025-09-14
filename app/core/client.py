import asyncio
from typing import Any, Optional

import structlog
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import get_settings
from app.utils.exceptions import LLMError, LLMRateLimitError, LLMTimeoutError

logger = structlog.get_logger(__name__)
settings = get_settings()


class LLMClient:
    """
    Клиент для взаимодействия с языковой моделью OpenAI (асинхронный).

    Атрибуты:
        client (AsyncOpenAI): Асинхронный клиент OpenAI.
        model (str): Имя используемой модели.
        max_tokens (int): Максимальное количество токенов в ответе.
        temperature (float): Температура генерации.
    """

    def __init__(self) -> None:
        """
        Инициализация клиента LLM.

        Returns
        -------
            None

        """
        self.client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout)
        self.model = settings.openai_model
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10), reraise=True
    )
    async def generate_response(
        self,
        messages: list[dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Генерирует ответ с помощью OpenAI API.

        Args:
        ----
            messages (list[dict[str, str]]): Список сообщений для диалога.
            temperature (Optional[float]): Температура генерации.
            max_tokens (Optional[int]): Максимальное количество токенов.
            **kwargs: Дополнительные параметры для OpenAI API.

        Returns:
        -------
            dict[str, Any]: Результат генерации (контент, usage, модель, причина завершения).

        """
        try:
            logger.info(
                "Generating LLM response",
                model=self.model,
                message_count=len(messages),
                temperature=temperature or self.temperature,
            )

            # Преобразуем messages в правильный тип для OpenAI API
            api_messages: list[ChatCompletionMessageParam] = []
            for msg in messages:
                api_messages.append(
                    {"role": msg["role"], "content": msg["content"]}  # type: ignore
                )

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or self.max_tokens,
                **kwargs,
            )

            # Безопасно обращаемся к usage
            usage = response.usage
            if usage is None:
                logger.warning("No usage information in response")
                usage_dict = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            else:
                usage_dict = {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                }

            # Безопасно получаем content
            message_content = response.choices[0].message.content
            if message_content is None:
                logger.warning("No content in response")
                message_content = ""

            result = {
                "content": message_content,
                "usage": usage_dict,
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason,
            }

            logger.info(
                "LLM response generated",
                tokens_used=usage_dict["total_tokens"],
                finish_reason=result["finish_reason"],
            )

            return result

        except asyncio.TimeoutError as e:
            logger.error("LLM request timeout")
            raise LLMTimeoutError("LLM request timed out") from e

        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower():
                logger.warning("LLM rate limit hit", error=error_msg)
                raise LLMRateLimitError(f"Rate limit exceeded: {error_msg}") from e
            else:
                logger.error("LLM generation failed", error=error_msg)
                raise LLMError(f"LLM generation failed: {error_msg}") from e

    async def classify_request(self, message: str) -> dict[str, str | float]:
        """
        Классифицирует тип пользовательского запроса.

        Args:
        ----
            message (str): Сообщение пользователя.

        Returns:
        -------
            dict[str, Any]: Результат классификации (тип, уверенность, объяснение).

        """
        classification_prompt = [
            {
                "role": "system",
                "content": """Analyze the user message and classify it into one of these categories:
                - tech_support: Technical issues, bugs, how-to questions
                - sales: Product inquiries, pricing, purchase intent
                - complaint: Complaints, refunds, dissatisfaction
                - general: General questions, greetings, unclear intent

                Respond in JSON format: {\"type\": \"category\", \"confidence\": 0.0-1.0, \"reasoning\": \"explanation\"}""",
            },
            {"role": "user", "content": f"Classify this message: {message}"},
        ]

        response = await self.generate_response(
            classification_prompt, temperature=0.3, max_tokens=150
        )

        try:
            import json

            content = response["content"]
            if isinstance(content, str):
                classification_data = json.loads(content)
                # Убеждаемся, что возвращаем правильный тип
                return {
                    "type": str(classification_data.get("type", "general")),
                    "confidence": float(classification_data.get("confidence", 0.5)),
                    "reasoning": str(classification_data.get("reasoning", "Unknown")),
                }
            else:
                logger.warning("Response content is not a string")
                return {
                    "type": "general",
                    "confidence": 0.5,
                    "reasoning": "Invalid response format",
                }
        except (json.JSONDecodeError, ValueError, KeyError):
            logger.warning("Failed to parse classification response")
            return {"type": "general", "confidence": 0.5, "reasoning": "Classification failed"}

    async def close(self) -> None:
        """
        Закрывает клиент OpenAI.

        Returns
        -------
            None

        """
        await self.client.close()
