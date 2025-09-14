import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, TypedDict


class HourlyStats(TypedDict):
    """Структура почасовой статистики."""

    sessions: int
    total_tokens: int
    total_cost: float
    response_times: list[int]
    satisfactions: list[float]


class AnalyticsResult(TypedDict):
    """Результат аналитики."""

    total_sessions: int
    avg_response_time_ms: float
    total_tokens_used: int
    total_cost_usd: float
    avg_satisfaction: Optional[float]
    classification_accuracy: float
    hourly_breakdown: dict[str, HourlyStats]


@dataclass
class SessionMetrics:
    """
    Метрики одной сессии диалога.

    Атрибуты:
        session_id (str): Идентификатор сессии.
        request_type (Optional[str]): Тип запроса.
        response_times (list[int]): Времена ответа (мс).
        tokens_used (int): Количество использованных токенов.
        total_cost (float): Стоимость сессии.
        satisfaction_score (Optional[float]): Оценка удовлетворенности.
        classification_confidence (float): Уверенность классификации.
        created_at (datetime): Время создания сессии.
    """

    session_id: str
    request_type: Optional[str]
    response_times: list[int] = field(default_factory=list)
    tokens_used: int = 0
    total_cost: float = 0.0
    satisfaction_score: Optional[float] = None
    classification_confidence: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)


class MetricsCollector:
    """
    Класс для сбора и анализа метрик по сессиям диалога.

    Атрибуты:
        session_metrics (dict[str, SessionMetrics]): Метрики по сессиям.
        hourly_stats (defaultdict): Почасовая статистика.
    """

    def __init__(self) -> None:
        self.session_metrics: dict[str, SessionMetrics] = {}
        self.hourly_stats: defaultdict[str, HourlyStats] = defaultdict(
            lambda: {
                "sessions": 0,
                "total_tokens": 0,
                "total_cost": 0.0,
                "response_times": [],
                "satisfactions": [],
            }
        )

    def track_session_start(
        self, session_id: str, request_type: Optional[str], confidence: float
    ) -> None:
        """
        Отслеживает запуск новой сессии.

        Args:
        ----
            session_id (str): Идентификатор сессии.
            request_type (Optional[str]): Тип запроса.
            confidence (float): Уверенность классификации.

        Returns:
        -------
            None

        """
        self.session_metrics[session_id] = SessionMetrics(
            session_id=session_id, request_type=request_type, classification_confidence=confidence
        )

    def track_response(
        self, session_id: str, response_time_ms: int, tokens: int, cost: float
    ) -> None:
        """
        Отслеживает метрики ответа.

        Args:
        ----
            session_id (str): Идентификатор сессии.
            response_time_ms (int): Время ответа в мс.
            tokens (int): Количество токенов.
            cost (float): Стоимость ответа.

        Returns:
        -------
            None

        """
        if session_id in self.session_metrics:
            metrics = self.session_metrics[session_id]
            metrics.response_times.append(response_time_ms)
            metrics.tokens_used += tokens
            metrics.total_cost += cost

            hour_key = datetime.now().strftime("%Y-%m-%d-%H")
            self.hourly_stats[hour_key]["sessions"] += 1
            self.hourly_stats[hour_key]["total_tokens"] += tokens
            self.hourly_stats[hour_key]["total_cost"] += cost
            self.hourly_stats[hour_key]["response_times"].append(response_time_ms)

    def track_satisfaction(self, session_id: str, score: float) -> None:
        """
        Отслеживает оценку удовлетворенности пользователя.

        Args:
        ----
            session_id (str): Идентификатор сессии.
            score (float): Оценка удовлетворенности.

        Returns:
        -------
            None

        """
        if session_id in self.session_metrics:
            self.session_metrics[session_id].satisfaction_score = score

            hour_key = datetime.now().strftime("%Y-%m-%d-%H")
            self.hourly_stats[hour_key]["satisfactions"].append(score)

    def get_analytics(self) -> AnalyticsResult:
        """
        Возвращает агрегированную аналитику по сессиям за последние 24 часа.

        Returns
        -------
            AnalyticsResult: Словарь с аналитикой (количество сессий, среднее время ответа, токены, стоимость, удовлетворенность, точность классификации, почасовая разбивка).

        """
        now = datetime.now()
        recent_sessions = [
            m for m in self.session_metrics.values() if now - m.created_at < timedelta(hours=24)
        ]

        if not recent_sessions:
            return {
                "total_sessions": 0,
                "avg_response_time_ms": 0.0,
                "total_tokens_used": 0,
                "total_cost_usd": 0.0,
                "avg_satisfaction": None,
                "classification_accuracy": 0.0,
                "hourly_breakdown": {},
            }

        # Вычисляем метрики
        all_response_times = []
        all_satisfactions = []
        high_confidence_sessions = 0

        for session in recent_sessions:
            all_response_times.extend(session.response_times)
            if session.satisfaction_score:
                all_satisfactions.append(session.satisfaction_score)
            if session.classification_confidence > 0.8:
                high_confidence_sessions += 1

        return {
            "total_sessions": len(recent_sessions),
            "avg_response_time_ms": float(statistics.mean(all_response_times))
            if all_response_times
            else 0.0,
            "total_tokens_used": sum(s.tokens_used for s in recent_sessions),
            "total_cost_usd": round(sum(s.total_cost for s in recent_sessions), 4),
            "avg_satisfaction": statistics.mean(all_satisfactions) if all_satisfactions else None,
            "classification_accuracy": (high_confidence_sessions / len(recent_sessions))
            if recent_sessions
            else 0.0,
            "hourly_breakdown": dict(self.hourly_stats),
        }

    def cleanup_old_metrics(self) -> None:
        """
        Удаляет старые метрики для экономии памяти.

        Returns
        -------
            None

        """
        cutoff = datetime.now() - timedelta(hours=48)
        to_remove = [
            sid for sid, metrics in self.session_metrics.items() if metrics.created_at < cutoff
        ]
        for sid in to_remove:
            del self.session_metrics[sid]


metrics_collector = MetricsCollector()
