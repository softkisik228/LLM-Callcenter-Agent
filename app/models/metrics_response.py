from pydantic import BaseModel


class MetricsResponse(BaseModel):
    """
    Модель ответа с метриками работы системы.

    Args:
    ----
        total_sessions (int): Общее количество сессий.
        avg_response_time_ms (float): Среднее время ответа (мс).
        total_tokens_used (int): Общее количество использованных токенов.
        total_cost_usd (float): Общая стоимость (USD).
        avg_satisfaction (float): Средний уровень удовлетворённости.
        classification_accuracy (float): Точность классификации.

    """

    total_sessions: int
    avg_response_time_ms: float
    total_tokens_used: int
    total_cost_usd: float
    avg_satisfaction: float
    classification_accuracy: float
