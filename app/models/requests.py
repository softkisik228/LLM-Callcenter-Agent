from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import Priority, RequestType


class StartDialogueRequest(BaseModel):
    """
    Модель запроса на запуск новой сессии диалога.

    Атрибуты:
        customer_id (Optional[str]): Идентификатор клиента.
        customer_name (Optional[str]): Имя клиента.
        initial_message (str): Первое сообщение пользователя.
        priority (Priority): Приоритет обращения.
        metadata (Dict[str, Any]): Дополнительные метаданные.
    """

    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    initial_message: str = Field(..., min_length=1, max_length=2000)
    priority: Priority = Priority.MEDIUM
    metadata: dict[str, Any] = Field(default_factory=dict)


class SendMessageRequest(BaseModel):
    """
    Модель запроса на отправку сообщения в сессию диалога.

    Атрибуты:
        message (str): Текст сообщения.
        metadata (Dict[str, Any]): Дополнительные метаданные.
    """

    message: str = Field(..., min_length=1, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedbackRequest(BaseModel):
    """
    Модель запроса на добавление обратной связи пользователя.

    Атрибуты:
        satisfaction_score (float): Оценка удовлетворенности от 1 до 5.
    """

    satisfaction_score: float = Field(..., ge=1.0, le=5.0)


class DialogueResponse(BaseModel):
    """
    Модель ответа на сообщение пользователя в диалоге.

    Атрибуты:
        session_id (UUID): Идентификатор сессии.
        message (str): Ответ ассистента.
        request_type (Optional[RequestType]): Тип запроса.
        confidence (float): Уверенность классификации.
        response_time_ms (int): Время ответа в миллисекундах.
        suggestions (list[str]): Список подсказок.
    """

    session_id: UUID
    message: str
    request_type: Optional[RequestType] = None
    confidence: float
    response_time_ms: int
    suggestions: list[str] = Field(default_factory=list)


class SessionInfoResponse(BaseModel):
    """
    Модель ответа с информацией о сессии диалога.

    Атрибуты:
        session_id (UUID): Идентификатор сессии.
        status (str): Статус сессии.
        message_count (int): Количество сообщений в сессии.
        request_type (Optional[RequestType]): Тип запроса.
        created_at (str): Время создания сессии.
        updated_at (str): Время последнего обновления.
    """

    session_id: UUID
    status: str
    message_count: int
    request_type: Optional[RequestType] = None
    created_at: str
    updated_at: str
