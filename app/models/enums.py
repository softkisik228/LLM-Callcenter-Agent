from enum import Enum


class RequestType(str, Enum):
    """
    Тип запроса пользователя.

    Значения:
        TECH_SUPPORT: Техническая поддержка.
        SALES: Продажи.
        COMPLAINT: Жалоба.
        GENERAL: Общий вопрос.
    """

    TECH_SUPPORT = "tech_support"
    SALES = "sales"
    COMPLAINT = "complaint"
    GENERAL = "general"


class DialogueStatus(str, Enum):
    """
    Статус сессии диалога.

    Значения:
        ACTIVE: Активна.
        COMPLETED: Завершена.
        ESCALATED: Эскалирована.
        TIMEOUT: Истекло время ожидания.
    """

    ACTIVE = "active"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    TIMEOUT = "timeout"


class MessageRole(str, Enum):
    """
    Роль участника диалога.

    Значения:
        USER: Пользователь.
        ASSISTANT: Ассистент.
        SYSTEM: Система.
    """

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Priority(str, Enum):
    """
    Приоритет обращения пользователя.

    Значения:
        LOW: Низкий.
        MEDIUM: Средний.
        HIGH: Высокий.
        URGENT: Срочный.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
