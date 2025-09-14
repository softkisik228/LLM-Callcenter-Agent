from fastapi import APIRouter

from app.api.v1 import dialogue, health, metrics

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(dialogue.router, prefix="/v1", tags=["dialogue"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
