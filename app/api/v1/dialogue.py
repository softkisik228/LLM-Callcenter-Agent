from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.core.manager import DialogueManager
from app.core.metrics import metrics_collector
from app.dependencies import get_dialogue_manager, get_dialogue_service
from app.models.requests import (
    DialogueResponse,
    FeedbackRequest,
    SendMessageRequest,
    SessionInfoResponse,
    StartDialogueRequest,
)
from app.services.dialogue_service import DialogueService
from app.utils.exceptions import LLMError, SessionNotFoundError

router = APIRouter()
logger = structlog.get_logger(__name__)


@router.post("/dialogue/start", response_model=DialogueResponse)
async def start_dialogue(
    request: StartDialogueRequest,
    service: DialogueService = Depends(get_dialogue_service),
    manager: DialogueManager = Depends(get_dialogue_manager),
) -> DialogueResponse:
    """
    Запуск новой сессии диалога.

    Args:
    ----
        request (StartDialogueRequest): Данные для старта диалога.
        service (DialogueService): Сервис диалога (зависимость).
        manager (DialogueManager): Менеджер сессий (зависимость).

    Returns:
    -------
        DialogueResponse: Ответ с первым сообщением и метаданными.

    """
    try:
        # Create session
        session = await manager.create_session(
            customer_id=request.customer_id,
            customer_name=request.customer_name,
            initial_message=request.initial_message,
            metadata=request.metadata,
        )

        # Process initial message
        response, request_type, confidence, response_time = await service.process_message(
            session.session_id, request.initial_message
        )

        logger.info(
            "Dialogue started",
            session_id=str(session.session_id),
            customer_id=request.customer_id,
            request_type=request_type.value if request_type else None,
        )

        return DialogueResponse(
            session_id=session.session_id,
            message=response,
            request_type=request_type,
            confidence=confidence,
            response_time_ms=response_time,
            suggestions=[],  # TODO: Implement suggestions
        )

    except LLMError as e:
        logger.error("LLM error in dialogue start", error=str(e))
        raise HTTPException(status_code=e.status_code, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to start dialogue", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start dialogue") from e


@router.post("/dialogue/{session_id}/message", response_model=DialogueResponse)
async def send_message(
    session_id: UUID,
    request: SendMessageRequest,
    service: DialogueService = Depends(get_dialogue_service),
) -> DialogueResponse:
    """
    Отправка сообщения в существующую сессию диалога.

    Args:
    ----
        session_id (UUID): Идентификатор сессии.
        request (SendMessageRequest): Сообщение пользователя.
        service (DialogueService): Сервис диалога (зависимость).

    Returns:
    -------
        DialogueResponse: Ответ ассистента и метаданные.

    """
    try:
        response, request_type, confidence, response_time = await service.process_message(
            session_id, request.message, request.metadata
        )

        logger.info("Message sent", session_id=str(session_id), message_length=len(request.message))

        return DialogueResponse(
            session_id=session_id,
            message=response,
            request_type=request_type,
            confidence=confidence,
            response_time_ms=response_time,
            suggestions=[],
        )

    except SessionNotFoundError as e:
        logger.warning("Session not found", session_id=str(session_id))
        raise HTTPException(status_code=404, detail=str(e)) from e
    except LLMError as e:
        logger.error("LLM error in message processing", error=str(e))
        raise HTTPException(status_code=e.status_code, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to process message", error=str(e), session_id=str(session_id))
        raise HTTPException(status_code=500, detail="Failed to process message") from e


@router.post("/dialogue/{session_id}/feedback")
async def add_feedback(
    session_id: UUID,
    request: FeedbackRequest,
    manager: DialogueManager = Depends(get_dialogue_manager),
) -> dict[str, str]:
    """
    Добавление обратной связи пользователя (оценка удовлетворенности).

    Args:
    ----
        session_id (UUID): Идентификатор сессии.
        request (FeedbackRequest): Оценка удовлетворенности.
        manager (DialogueManager): Менеджер сессий (зависимость).

    Returns:
    -------
        dict: Сообщение об успешном сохранении.

    """
    try:
        # Получаем сессию и обновляем satisfaction_score
        session = await manager.get_session(session_id)
        session.context.satisfaction_score = request.satisfaction_score
        await manager.update_session(session)

        # Отслеживать satisfaction в метриках
        metrics_collector.track_satisfaction(str(session_id), request.satisfaction_score)

        logger.info("Feedback added", session_id=str(session_id), score=request.satisfaction_score)
        return {"message": "Feedback recorded successfully"}
    except Exception as e:
        logger.error("Failed to add feedback", error=str(e), session_id=str(session_id))
        raise HTTPException(status_code=500, detail="Failed to add feedback") from e


@router.get("/dialogue/{session_id}", response_model=SessionInfoResponse)
async def get_session_info(
    session_id: UUID, manager: DialogueManager = Depends(get_dialogue_manager)
) -> SessionInfoResponse:
    """
    Получение информации о сессии диалога.

    Args:
    ----
        session_id (UUID): Идентификатор сессии.
        manager (DialogueManager): Менеджер сессий (зависимость).

    Returns:
    -------
        SessionInfoResponse: Информация о сессии.

    """
    try:
        session = await manager.get_session(session_id)

        return SessionInfoResponse(
            session_id=session.session_id,
            status=session.status.value,
            message_count=len(session.messages),
            request_type=session.context.request_type,
            created_at=session.created_at.isoformat(),
            updated_at=session.updated_at.isoformat(),
        )

    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to get session info", error=str(e), session_id=str(session_id))
        raise HTTPException(status_code=500, detail="Failed to get session info") from e


@router.delete("/dialogue/{session_id}")
async def close_dialogue(
    session_id: UUID, manager: DialogueManager = Depends(get_dialogue_manager)
) -> dict[str, str]:
    """
    Завершение сессии диалога.

    Args:
    ----
        session_id (UUID): Идентификатор сессии.
        manager (DialogueManager): Менеджер сессий (зависимость).

    Returns:
    -------
        dict: Сообщение об успешном завершении.

    """
    try:
        await manager.close_session(session_id)
        logger.info("Dialogue closed", session_id=str(session_id))

        return {"message": "Dialogue session closed successfully"}

    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to close dialogue", error=str(e), session_id=str(session_id))
        raise HTTPException(status_code=500, detail="Failed to close dialogue") from e


@router.get("/dialogue/{session_id}/messages")
async def get_message_history(
    session_id: UUID, limit: int = 50, manager: DialogueManager = Depends(get_dialogue_manager)
) -> dict[str, object]:
    """
    Получение истории сообщений для сессии.

    Args:
    ----
        session_id (UUID): Идентификатор сессии.
        limit (int): Количество последних сообщений.
        manager (DialogueManager): Менеджер сессий (зависимость).

    Returns:
    -------
        dict: Список сообщений сессии.

    """
    try:
        session = await manager.get_session(session_id)
        messages = session.get_recent_messages(limit)

        return {
            "session_id": session_id,
            "messages": [
                {
                    "id": str(msg.id),
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata,
                }
                for msg in messages
            ],
        }

    except SessionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Failed to get message history", error=str(e), session_id=str(session_id))
        raise HTTPException(status_code=500, detail="Failed to get message history") from e
