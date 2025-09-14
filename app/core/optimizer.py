import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional

from app.config import get_settings
from app.models.dialogue import DialogueSession, Message
from app.models.enums import RequestType

settings = get_settings()


class ResponseOptimizer:
    """
    Класс для оптимизации генерации ответов и управления кэшем.

    Атрибуты:
        response_cache (dict[str, tuple[str, datetime, int, float]]): Кэш ответов.
        model_costs (dict[str, dict[str, float]]): Стоимости моделей.
    """

    def __init__(self) -> None:
        """
        Инициализация оптимизатора ответов.

        Returns
        -------
            None

        """
        self.response_cache: dict[
            str, tuple[str, datetime, int, float]
        ] = {}  # hash -> (response, timestamp, tokens, cost)
        self.model_costs = {
            "gpt-4-1106-preview": {"input": 0.01, "output": 0.03},  # per 1K tokens
            "gpt-3.5-turbo-1106": {"input": 0.001, "output": 0.002},
        }

    def get_cache_key(self, messages: list[dict[str, str]], model: str, temperature: float) -> str:
        """
        Генерирует ключ кэша для запроса.

        Args:
        ----
            messages (list[dict]): Сообщения для генерации.
            model (str): Имя модели.
            temperature (float): Температура генерации.

        Returns:
        -------
            str: Ключ кэша.

        """
        cache_data = {
            "messages": messages[-3:],  # Last 3 messages for context
            "model": model,
            "temperature": temperature,
        }
        return hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()

    def get_cached_response(self, cache_key: str) -> Optional[tuple[str, int, float]]:
        """
        Получает кэшированный ответ, если он валиден.

        Args:
        ----
            cache_key (str): Ключ кэша.

        Returns:
        -------
            Optional[tuple[str, int, float]]: Кортеж (ответ, токены, стоимость) или None.

        """
        # Заглушки для отсутствующих настроек - используем разумные значения по умолчанию
        enable_caching = getattr(settings, "enable_caching", False)
        if not enable_caching:
            return None

        if cache_key in self.response_cache:
            response, timestamp, tokens, cost = self.response_cache[cache_key]
            cache_ttl = getattr(settings, "cache_ttl", 3600)  # 1 час по умолчанию
            if datetime.now() - timestamp < timedelta(seconds=cache_ttl):
                return response, tokens, cost
            else:
                del self.response_cache[cache_key]
        return None

    def cache_response(self, cache_key: str, response: str, tokens: int, cost: float) -> None:
        """
        Сохраняет ответ в кэш.

        Args:
        ----
            cache_key (str): Ключ кэша.
            response (str): Ответ.
            tokens (int): Количество токенов.
            cost (float): Стоимость.

        Returns:
        -------
            None

        """
        enable_caching = getattr(settings, "enable_caching", False)
        if enable_caching:
            self.response_cache[cache_key] = (response, datetime.now(), tokens, cost)

    def select_optimal_model(self, session: DialogueSession) -> str:
        """
        Выбирает оптимальную модель на основе сложности и стоимости.

        Args:
        ----
            session (DialogueSession): Сессия диалога.

        Returns:
        -------
            str: Имя выбранной модели.

        """
        cost_optimization = getattr(settings, "cost_optimization", False)
        if not cost_optimization:
            return settings.openai_model

        # Use faster/cheaper model for simple cases
        if session.context.request_type == RequestType.GENERAL:
            return getattr(settings, "openai_model_fast", settings.openai_model)

        # Use expensive model for complex cases
        if session.context.priority.value in ["high"] or len(session.messages) > 10:
            return settings.openai_model

        return getattr(settings, "openai_model_fast", settings.openai_model)

    def compress_context(self, messages: list[Message]) -> list[dict[str, str]]:
        """
        Сжимает контекст для уменьшения количества токенов.

        Args:
        ----
            messages (list[Message]): Сообщения диалога.

        Returns:
        -------
            list[dict]: Список сжатых сообщений.

        """
        compressed = []

        for msg in messages:
            if msg.role.value == "system":
                compressed.append({"role": msg.role.value, "content": msg.content})
                break

        # Include recent messages up to limit
        max_context_messages = getattr(settings, "max_context_messages", 10)
        recent_messages = messages[-max_context_messages:]
        for msg in recent_messages:
            if msg.role.value != "system":
                # Truncate very long messages
                content = msg.content[:500] + "..." if len(msg.content) > 500 else msg.content
                compressed.append({"role": msg.role.value, "content": content})

        return compressed

    def estimate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """
        Оценивает стоимость вызова API.

        Args:
        ----
            prompt_tokens (int): Токены в prompt.
            completion_tokens (int): Токены в completion.
            model (str): Имя модели.

        Returns:
        -------
            float: Оценочная стоимость.

        """
        if model not in self.model_costs:
            model = getattr(settings, "openai_model_fast", settings.openai_model)

        costs = self.model_costs[model]
        input_cost = (prompt_tokens / 1000) * costs["input"]
        output_cost = (completion_tokens / 1000) * costs["output"]

        return round(input_cost + output_cost, 6)


optimizer = ResponseOptimizer()
