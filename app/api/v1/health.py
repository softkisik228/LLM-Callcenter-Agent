from fastapi import APIRouter, Depends

from app.dependencies import get_storage
from app.storage.memory import MemoryStorage

router = APIRouter()


@router.get("/")
async def health_check() -> dict[str, str]:
    """
    Проверка базового состояния сервиса.

    Returns
    -------
        dict: Статус сервиса.

    """
    return {"status": "healthy"}


@router.get("/detailed")
async def detailed_health_check(storage: MemoryStorage = Depends(get_storage)) -> dict[str, object]:
    """
    Подробная проверка состояния сервиса с метриками.

    Args:
    ----
        storage (MemoryStorage): Хранилище сессий (зависимость).

    Returns:
    -------
        dict: Статус, состояние сервисов и метрики.

    """
    active_sessions = await storage.get_active_sessions()

    return {
        "status": "healthy",
        "services": {"storage": "active", "llm": "active"},
        "metrics": {"active_sessions": len(active_sessions)},
    }
