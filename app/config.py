from functools import lru_cache
from typing import Any, Optional

from pydantic_settings import BaseSettings

MODEL_COSTS = {
    "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo-1106": {"input": 0.001, "output": 0.002},
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
}


class Settings(BaseSettings):
    """
    Класс для хранения всех настроек приложения.

    Атрибуты:
        app_name (str): Название приложения.
        app_version (str): Версия приложения.
        debug (bool): Включить режим отладки.
        log_level (str): Уровень логирования.
        host (str): Хост для запуска сервера.
        port (int): Порт для запуска сервера.
        workers (int): Количество воркеров.
        openai_api_key (str): Ключ OpenAI API.
        openai_model (str): Модель OpenAI.
        openai_max_tokens (int): Максимальное количество токенов.
        openai_temperature (float): Температура генерации.
        openai_timeout (int): Таймаут для OpenAI.
        redis_url (str): URL Redis.
        redis_ttl (int): Время жизни ключей Redis.
        database_url (Optional[str]): URL базы данных.
        rate_limit_requests (int): Лимит запросов.
        rate_limit_window (int): Окно лимита запросов.
        enable_metrics (bool): Включить метрики.
        metrics_port (int): Порт для метрик.
    """

    # Application
    app_name: str = "LLM Call Center Agent"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4-1106-preview"
    openai_max_tokens: int = 1000
    openai_temperature: float = 0.7
    openai_timeout: int = 30

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_ttl: int = 3600

    # Database
    database_url: Optional[str] = None

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    # Monitoring
    enable_metrics: bool = True
    metrics_port: int = 9090

    class Config:
        """
        Конфигурация pydantic для класса Settings.

        Атрибуты:
            env_file (str): Имя файла окружения.
            case_sensitive (bool): Чувствительность к регистру.
        """

        env_file = ".env"
        case_sensitive = False

    @staticmethod
    def _calculate_cost(usage: dict[str, Any], model: str) -> float:
        costs = MODEL_COSTS.get(model, MODEL_COSTS["gpt-3.5-turbo"])
        input_cost = float(costs["input"]) * float(usage.get("total_tokens", 0))
        output_cost = float(costs["output"]) * float(usage.get("completion_tokens", 0))
        return float(input_cost + output_cost)

@lru_cache
def get_settings() -> Settings:
    """
    Получить экземпляр настроек приложения с кэшированием.

    Returns
    -------
        Settings: Экземпляр настроек приложения.

    """
    return Settings()  # type: ignore
