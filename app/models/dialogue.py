from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from app.models.enums import DialogueStatus, MessageRole, Priority, RequestType


class Message(BaseModel):
    """
    Сообщение в диалоге.

    Атрибуты:
        id (UUID): Уникальный идентификатор сообщения.
        role (MessageRole): Роль отправителя (пользователь или ассистент).
        content (str): Текст сообщения.
        timestamp (datetime): Время отправки сообщения.
        metadata (dict[str, Any]): Дополнительные метаданные.
    """

    id: UUID = Field(default_factory=uuid4)
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DialogueContext(BaseModel):
    """
    Контекст диалога, включая информацию о клиенте, типе запроса и метриках.

    Атрибуты:
        customer_id (Optional[str]): Идентификатор клиента.
        customer_name (Optional[str]): Имя клиента.
        request_type (Optional[RequestType]): Тип запроса.
        priority (Priority): Приоритет обращения.
        session_data (dict[str, Any]): Дополнительные данные сессии.
        classification_confidence (float): Уверенность классификации.
        response_count (int): Количество ответов ассистента.
        satisfaction_score (Optional[float]): Оценка удовлетворенности.
        escalation_reason (Optional[str]): Причина эскалации.
    """

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    request_type: Optional[RequestType] = None
    priority: Priority = Priority.MEDIUM
    session_data: dict[str, Any] = Field(default_factory=dict)
    classification_confidence: float = 0.0

    # Метрики
    response_count: int = 0
    satisfaction_score: Optional[float] = None
    escalation_reason: Optional[str] = None


class DialogueSession(BaseModel):
    """
    Сессия диалога между пользователем и ассистентом.

    Атрибуты:
        session_id (UUID): Идентификатор сессии.
        status (DialogueStatus): Статус сессии.
        messages (list[Message]): Список сообщений в сессии.
        context (DialogueContext): Контекст сессии.
        created_at (datetime): Время создания сессии.
        updated_at (datetime): Время последнего обновления.
        expires_at (Optional[datetime]): Время истечения сессии.
    """

    session_id: UUID = Field(default_factory=uuid4)
    status: DialogueStatus = DialogueStatus.ACTIVE
    messages: list[Message] = Field(default_factory=list)
    context: DialogueContext = Field(default_factory=DialogueContext)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None

    def add_message(
        self, role: MessageRole, content: str, metadata: Optional[dict[str, Any]] = None
    ) -> None:
        """
        Добавляет сообщение в диалог.

        Args:
        ----
            role (MessageRole): Роль отправителя.
            content (str): Текст сообщения.
            metadata (Optional[dict[str, Any]]): Дополнительные метаданные.

        Returns:
        -------
            None

        """
        message = Message(role=role, content=content, metadata=metadata or {})
        self.messages.append(message)
        self.updated_at = datetime.now()

        if role == MessageRole.ASSISTANT:
            self.context.response_count += 1

    def get_recent_messages(self, limit: int = 10) -> list[Message]:
        """
        Возвращает последние сообщения для контекста.

        Args:
        ----
            limit (int): Количество сообщений.

        Returns:
        -------
            list[Message]: Список последних сообщений.

        """
        return self.messages[-limit:]

    def is_expired(self) -> bool:
        """
        Проверяет, истекла ли сессия.

        Returns
        -------
            bool: True, если сессия истекла, иначе False.

        """
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
