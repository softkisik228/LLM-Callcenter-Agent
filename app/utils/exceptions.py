from typing import Any, Optional


class AppException(Exception):
    """
    Базовое исключение приложения.

    Args:
    ----
        message (str): Сообщение об ошибке.
        code (str, optional): Код ошибки.
        details (dict, optional): Дополнительные детали.
        status_code (int, optional): HTTP статус-код.

    """

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        status_code: int = 500,
    ):
        """
        Инициализация базового исключения приложения.

        Args:
        ----
            message (str): Сообщение об ошибке.
            code (str, optional): Код ошибки.
            details (dict, optional): Дополнительные детали.
            status_code (int, optional): HTTP статус-код.

        """
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)


class SessionNotFoundError(AppException):
    """
    Исключение: сессия не найдена.

    Args:
    ----
        message (str, optional): Сообщение об ошибке.

    """

    def __init__(self, message: str = "Session not found"):
        """
        Инициализация исключения SessionNotFoundError.

        Args:
        ----
            message (str, optional): Сообщение об ошибке.

        """
        super().__init__(message, status_code=404)


class LLMError(AppException):
    """
    Исключение: ошибка сервиса LLM.

    Args:
    ----
        message (str, optional): Сообщение об ошибке.

    """

    def __init__(
        self,
        message: str = "LLM service error",
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Инициализация исключения LLMError.

        Args:
        ----
            message (str, optional): Сообщение об ошибке.
            status_code (int): Статус код.
            details (dict, optional): Дополнительные детали.

        """
        super().__init__(message, status_code=status_code, details=details)


class LLMRateLimitError(LLMError):
    """
    Исключение: превышен лимит запросов к LLM.

    Args:
    ----
        message (str, optional): Сообщение об ошибке.

    """

    def __init__(
        self, message: str = "LLM rate limit exceeded", details: Optional[dict[str, Any]] = None
    ):
        """
        Инициализация исключения LLMRateLimitError.

        Args:
        ----
            message (str, optional): Сообщение об ошибке.
            details (dict, optional): Дополнительные детали.

        """
        super().__init__(message, status_code=429, details=details)


class LLMTimeoutError(LLMError):
    """
    Исключение: превышено время ожидания ответа от LLM.

    Args:
    ----
        message (str, optional): Сообщение об ошибке.
        details (dict, optional): Дополнительные детали.

    """

    def __init__(
        self, message: str = "LLM request timeout", details: Optional[dict[str, Any]] = None
    ):
        """
        Инициализация исключения LLMTimeoutError.

        Args:
        ----
            message (str, optional): Сообщение об ошибке.
            details (dict, optional): Дополнительные детали.

        """
        super().__init__(message, status_code=504, details=details)


class ValidationError(AppException):
    """
    Исключение: ошибка валидации данных.

    Args:
    ----
        message (str, optional): Сообщение об ошибке.
        details (dict, optional): Детали ошибки.

    """

    def __init__(self, message: str = "Validation error", details: Optional[dict[str, Any]] = None):
        """
        Инициализация исключения ValidationError.

        Args:
        ----
            message (str, optional): Сообщение об ошибке.
            details (dict, optional): Детали ошибки.

        """
        super().__init__(message, details=details, status_code=400)
