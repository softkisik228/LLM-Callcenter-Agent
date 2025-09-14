from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import UUID

import structlog

from app.models.dialogue import DialogueContext, DialogueSession
from app.models.enums import DialogueStatus, MessageRole, RequestType
from app.storage.memory import MemoryStorage
from app.utils.exceptions import SessionNotFoundError

logger = structlog.get_logger(__name__)


class DialogueManager:
    """
    Менеджер сессий диалога.

    Args:
    ----
        storage (MemoryStorage): Хранилище сессий в памяти.

    """

    def __init__(self, storage: MemoryStorage):
        """
        Инициализация менеджера диалогов.

        Args:
        ----
            storage (MemoryStorage): Хранилище сессий в памяти.

        """
        self.storage = storage
        self.default_ttl = 3600  # 1 час

    async def create_session(
        self,
        customer_id: Optional[str] = None,
        customer_name: Optional[str] = None,
        initial_message: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> DialogueSession:
        """
        Создать новую сессию диалога.

        Args:
        ----
            customer_id (Optional[str]): Идентификатор клиента.
            customer_name (Optional[str]): Имя клиента.
            initial_message (Optional[str]): Первое сообщение пользователя.
            metadata (Optional[dict[str, Any]]): Дополнительные метаданные.

        Returns:
        -------
            DialogueSession: Новая сессия диалога.

        """
        context = DialogueContext(
            customer_id=customer_id, customer_name=customer_name, session_data=metadata or {}
        )

        session = DialogueSession(
            context=context, expires_at=datetime.now() + timedelta(seconds=self.default_ttl)
        )

        if initial_message:
            session.add_message(MessageRole.USER, initial_message)

        await self.storage.store_session(session.session_id, session)

        logger.info(
            "Created new dialogue session",
            session_id=str(session.session_id),
            customer_id=customer_id,
        )

        return session

    async def get_session(self, session_id: UUID) -> DialogueSession:
        """
        Получить существующую сессию диалога.

        Args:
        ----
            session_id (UUID): Идентификатор сессии.

        Returns:
        -------
            DialogueSession: Сессия диалога.

        Raises:
        ------
            SessionNotFoundError: Если сессия не найдена или истекла.

        """
        session = await self.storage.get_session(session_id)

        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")

        if session.is_expired():
            await self.storage.delete_session(session_id)
            raise SessionNotFoundError(f"Session {session_id} has expired")

        return session

    async def update_session(self, session: DialogueSession) -> DialogueSession:
        """
        Обновить существующую сессию.

        Args:
        ----
            session (DialogueSession): Сессия для обновления.

        Returns:
        -------
            DialogueSession: Обновлённая сессия.

        """
        session.updated_at = datetime.now()
        await self.storage.store_session(session.session_id, session)
        return session

    async def add_message(
        self,
        session_id: UUID,
        role: MessageRole,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> DialogueSession:
        """
        Добавить сообщение в сессию.

        Args:
        ----
            session_id (UUID): Идентификатор сессии.
            role (MessageRole): Роль отправителя.
            content (str): Текст сообщения.
            metadata (Optional[dict[str, Any]]): Дополнительные метаданные.

        Returns:
        -------
            DialogueSession: Обновлённая сессия.

        """
        session = await self.get_session(session_id)
        session.add_message(role, content, metadata)
        return await self.update_session(session)

    async def update_context(
        self,
        session_id: UUID,
        request_type: Optional[RequestType] = None,
        confidence: Optional[float] = None,
        **context_updates: Any,
    ) -> DialogueSession:
        """
        Обновить контекст сессии.

        Args:
        ----
            session_id (UUID): Идентификатор сессии.
            request_type (RequestType, optional): Тип запроса.
            confidence (Optional[float]): Уверенность классификации.
            **context_updates: Дополнительные параметры контекста.

        Returns:
        -------
            DialogueSession: Обновлённая сессия.

        """
        session = await self.get_session(session_id)

        if request_type:
            session.context.request_type = request_type
        if confidence is not None:
            session.context.classification_confidence = confidence

        for key, value in context_updates.items():
            if hasattr(session.context, key):
                setattr(session.context, key, value)
            else:
                session.context.session_data[key] = value

        return await self.update_session(session)

    async def close_session(
        self, session_id: UUID, status: DialogueStatus = DialogueStatus.COMPLETED
    ) -> None:
        """
        Завершить сессию диалога.

        Args:
        ----
            session_id (UUID): Идентификатор сессии.
            status (DialogueStatus, optional): Новый статус сессии.

        Returns:
        -------
            None

        """
        session = await self.get_session(session_id)
        session.status = status
        await self.update_session(session)

        logger.info("Closed dialogue session", session_id=str(session_id), status=status.value)
