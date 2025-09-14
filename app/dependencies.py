from fastapi import Depends, Request

from app.core.client import LLMClient
from app.core.manager import DialogueManager
from app.services.dialogue_service import DialogueService
from app.storage.memory import MemoryStorage


def get_llm_client(request: Request) -> LLMClient:
    """
    Получить LLM-клиент из состояния приложения.

    Args:
    ----
        request (Request): Объект запроса FastAPI.

    Returns:
    -------
        LLMClient: Экземпляр LLM-клиента.

    """
    llm_client = request.app.state.llm_client
    if not isinstance(llm_client, LLMClient):
        raise TypeError("llm_client in app state is not an instance of LLMClient")
    return llm_client


def get_storage(request: Request) -> MemoryStorage:
    """
    Получить хранилище из состояния приложения.

    Args:
    ----
        request (Request): Объект запроса FastAPI.

    Returns:
    -------
        MemoryStorage: Экземпляр хранилища.

    """
    storage = request.app.state.storage
    if not isinstance(storage, MemoryStorage):
        raise TypeError("storage in app state is not an instance of MemoryStorage")
    return storage


def get_dialogue_manager(storage: MemoryStorage = Depends(get_storage)) -> DialogueManager:
    """
    Получить менеджер диалогов.

    Args:
    ----
        storage (MemoryStorage): Экземпляр хранилища.

    Returns:
    -------
        DialogueManager: Экземпляр менеджера диалогов.

    """
    return DialogueManager(storage)


def get_dialogue_service(
    llm_client: LLMClient = Depends(get_llm_client),
    dialogue_manager: DialogueManager = Depends(get_dialogue_manager),
) -> DialogueService:
    """
    Получить сервис диалогов.

    Args:
    ----
        llm_client (LLMClient): Экземпляр LLM-клиента.
        dialogue_manager (DialogueManager): Экземпляр менеджера диалогов.

    Returns:
    -------
        DialogueService: Экземпляр сервиса диалогов.

    """
    return DialogueService(llm_client, dialogue_manager)
