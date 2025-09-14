import time
from typing import Any, Optional
from uuid import UUID

import structlog

from app.config import MODEL_COSTS
from app.core.client import LLMClient
from app.core.manager import DialogueManager
from app.core.metrics import metrics_collector
from app.core.prompts import PromptTemplate
from app.models.dialogue import DialogueSession
from app.models.enums import MessageRole, RequestType
from app.services.classification_service import ClassificationService

logger = structlog.get_logger(__name__)


class DialogueService:
    """
    Сервис для обработки диалоговых сообщений пользователя и генерации ответов.

    Атрибуты:
        llm_client (LLMClient): Клиент для взаимодействия с языковой моделью.
        dialogue_manager (DialogueManager): Менеджер сессий диалога.
        classification_service (ClassificationService): Сервис классификации сообщений.
    """

    def __init__(self, llm_client: LLMClient, dialogue_manager: DialogueManager):
        """
        Инициализация сервиса диалога.

        Args:
        ----
            llm_client (LLMClient): Клиент LLM для генерации ответов.
            dialogue_manager (DialogueManager): Менеджер сессий диалога.

        Returns:
        -------
            None

        """
        self.llm_client = llm_client
        self.dialogue_manager = dialogue_manager
        self.classification_service = ClassificationService(llm_client)

    async def process_message(
        self, session_id: UUID, user_message: str, metadata: Optional[dict[str, str]] = None
    ) -> tuple[str, RequestType, float, int]:
        """
        Обрабатывает пользовательское сообщение и генерирует ответ.

        Args:
        ----
            session_id (UUID): Идентификатор сессии.
            user_message (str): Сообщение пользователя.
            metadata (dict, optional): Дополнительные метаданные сообщения.

        Returns:
        -------
            tuple[str, RequestType, float, int]: Ответ ассистента, тип запроса, уверенность, время ответа (мс).

        """
        start_time = time.time()

        try:
            # Получить или обновить сессию
            session = await self.dialogue_manager.get_session(session_id)

            # Добавить сообщение пользователя
            session = await self.dialogue_manager.add_message(
                session_id, MessageRole.USER, user_message, metadata
            )

            # Классифицировать запрос, если не классифицирован
            if not session.context.request_type:
                request_type, confidence = await self.classification_service.classify_message(
                    user_message
                )
                session = await self.dialogue_manager.update_context(
                    session_id, request_type=request_type, confidence=confidence
                )

                # Отслеживать начало сессии
                metrics_collector.track_session_start(
                    str(session_id),
                    request_type.value if request_type else None,
                    confidence
                )
            else:
                request_type = session.context.request_type
                confidence = session.context.classification_confidence

            # Сгенерировать ответ
            response, llm_response_data = await self._generate_contextual_response(session)

            # Добавить ответ ассистента
            await self.dialogue_manager.add_message(session_id, MessageRole.ASSISTANT, response)

            response_time = int((time.time() - start_time) * 1000)

            # Get exact token usage data
            usage = llm_response_data.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)

            # Calculate exact cost based on model
            cost = self._calculate_cost(usage, llm_response_data.get("model", ""))

            metrics_collector.track_response(
                str(session_id),
                response_time,
                total_tokens,
                cost
            )

            logger.info(
                "Message processed",
                session_id=str(session_id),
                request_type=request_type.value if request_type else None,
                response_time_ms=response_time,
            )

            return response, request_type, confidence, response_time

        except Exception as e:
            logger.error("Failed to process message", error=str(e), session_id=str(session_id))
            raise

    async def _generate_contextual_response(self, session: DialogueSession) -> tuple[str, dict[str, Any]]:
        """
        Генерирует контекстно-зависимый ответ на основе истории диалога.

        Args:
        ----
            session (DialogueSession): Сессия диалога.

        Returns:
        -------
            tuple[str, dict[str, Any]]: Кортеж из сгенерированного ответа и метаданных (включая usage).

        """
        messages = []

        # Добавить системный промпт
        system_prompt = PromptTemplate.get_system_prompt(session.context.request_type)  # type: ignore

        # Добавить контекстную информацию
        context_prompt = PromptTemplate.build_context_prompt(
            customer_name=session.context.customer_name, context_data=session.context.session_data
        )

        messages.append({"role": "system", "content": system_prompt + context_prompt})

        # Добавить историю диалога (последние 10 сообщений)
        recent_messages = session.get_recent_messages(limit=10)
        for msg in recent_messages:
            messages.append({"role": msg.role.value, "content": msg.content})

        # Сгенерировать ответ
        response = await self.llm_client.generate_response(messages)
        return str(response["content"]), response

    @staticmethod
    def _calculate_cost(usage: dict[str, Any], model: str) -> float:
        """
        Рассчитывает точную стоимость запроса на основе использованных токенов.

        Args:
        ----
            usage (dict[str, Any]): Данные об использовании токенов.
            model (str): Название модели.

        Returns:
        -------
            float: Стоимость в USD.

        """
        costs = MODEL_COSTS.get(model, MODEL_COSTS["gpt-3.5-turbo"])

        prompt_tokens = int(usage.get("prompt_tokens", 0))
        completion_tokens = int(usage.get("completion_tokens", 0))

        # Рассчитываем стоимость
        prompt_cost = (prompt_tokens / 1000) * costs["input"]
        completion_cost = (completion_tokens / 1000) * costs["output"]

        total_cost = prompt_cost + completion_cost
        return round(total_cost, 6)
