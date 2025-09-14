import structlog

from app.core.client import LLMClient
from app.models.enums import RequestType

logger = structlog.get_logger(__name__)


class ClassificationService:
    """
    Сервис для классификации пользовательских сообщений с помощью LLM.

    Атрибуты:
        llm_client (LLMClient): Клиент для взаимодействия с языковой моделью.
        confidence_threshold (float): Порог уверенности для классификации.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Инициализация сервиса классификации.

        Args:
        ----
            llm_client (LLMClient): Клиент LLM для классификации.

        Returns:
        -------
            None

        """
        self.llm_client = llm_client
        self.confidence_threshold = 0.7

    async def classify_message(self, message: str) -> tuple[RequestType, float]:
        """
        Классифицирует пользовательское сообщение и возвращает тип запроса с уверенностью.

        Args:
        ----
            message (str): Текст пользовательского сообщения.

        Returns:
        -------
            tuple[RequestType, float]: Кортеж с типом запроса и значением уверенности.

        """
        try:
            result = await self.llm_client.classify_request(message)

            request_type_str = result.get("type", "general")
            confidence = float(result.get("confidence", 0.5))

            # Преобразование строки в enum
            try:
                request_type = RequestType(request_type_str)
            except ValueError:
                logger.warning(f"Unknown request type: {request_type_str}")
                request_type = RequestType.GENERAL
                confidence = 0.5

            logger.info(
                "Message classified",
                type=request_type.value,
                confidence=confidence,
                reasoning=result.get("reasoning", ""),
            )

            return request_type, confidence

        except Exception as e:
            logger.error("Classification failed", error=str(e))
            return RequestType.GENERAL, 0.5
