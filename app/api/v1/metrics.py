from fastapi import APIRouter

from app.core.metrics import metrics_collector
from app.models.metrics_response import MetricsResponse

router = APIRouter()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """Get system metrics and analytics"""
    analytics = metrics_collector.get_analytics()
    return MetricsResponse(
        total_sessions=analytics["total_sessions"],
        avg_response_time_ms=analytics["avg_response_time_ms"],
        total_tokens_used=analytics["total_tokens_used"],
        total_cost_usd=analytics["total_cost_usd"],
        avg_satisfaction=analytics["avg_satisfaction"] or 0.0,
        classification_accuracy=analytics["classification_accuracy"],
    )
