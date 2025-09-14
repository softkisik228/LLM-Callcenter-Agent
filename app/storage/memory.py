import asyncio
from typing import Optional
from uuid import UUID

from app.models.dialogue import DialogueSession


class MemoryStorage:
    """
    Класс для хранения сессий диалога в памяти.

    Атрибуты:
        sessions (dict[UUID, DialogueSession]): Словарь сессий по UUID.
        _cleanup_task (Optional[asyncio.Task]): Фоновая задача очистки.
    """

    def __init__(self) -> None:
        """
        Инициализация хранилища и запуск фоновой задачи очистки.

        Returns
        -------
            None

        """
        self.sessions: dict[UUID, DialogueSession] = {}
        self._cleanup_task: Optional[asyncio.Task[None]] = None
        self._start_cleanup_task()

    async def store_session(self, session_id: UUID, session: DialogueSession) -> None:
        """
        Сохраняет сессию диалога по идентификатору.

        Args:
        ----
            session_id (UUID): Идентификатор сессии.
            session (DialogueSession): Объект сессии диалога.

        Returns:
        -------
            None

        """
        self.sessions[session_id] = session

    async def get_session(self, session_id: UUID) -> Optional[DialogueSession]:
        """
        Получает сессию диалога по идентификатору, если она не истекла.

        Args:
        ----
            session_id (UUID): Идентификатор сессии.

        Returns:
        -------
            Optional[DialogueSession]: Объект сессии или None, если не найдено или истек срок.

        """
        session = self.sessions.get(session_id)

        # Проверка на истечение срока действия
        if session and session.is_expired():
            await self.delete_session(session_id)
            return None

        return session

    async def delete_session(self, session_id: UUID) -> bool:
        """
        Удаляет сессию диалога по идентификатору.

        Args:
        ----
            session_id (UUID): Идентификатор сессии.

        Returns:
        -------
            bool: True, если сессия была удалена, иначе False.

        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    async def get_active_sessions(self) -> dict[UUID, DialogueSession]:
        """
        Возвращает все активные (не истекшие) сессии.

        Returns
        -------
            dict[UUID, DialogueSession]: Словарь активных сессий.

        """
        active = {}
        expired_ids = []

        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_ids.append(session_id)
            else:
                active[session_id] = session

        # Очистка истекших сессий
        for expired_id in expired_ids:
            await self.delete_session(expired_id)

        return active

    def _start_cleanup_task(self) -> None:
        """
        Запускает фоновую задачу очистки истекших сессий.

        Returns
        -------
            None

        """
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

    async def _cleanup_expired_sessions(self) -> None:
        """
        Фоновая задача для периодической очистки истекших сессий.

        Returns
        -------
            None

        """
        import logging

        while True:
            try:
                await asyncio.sleep(300)  # Очистка каждые 5 минут

                expired_ids = []
                for session_id, session in self.sessions.items():
                    if session.is_expired():
                        expired_ids.append(session_id)

                for expired_id in expired_ids:
                    await self.delete_session(expired_id)

                if expired_ids:
                    logging.warning(f"Cleaned up {len(expired_ids)} expired sessions")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logging.warning(f"Cleanup task error: {e}")

    async def close(self) -> None:
        """
        Завершает работу хранилища и отменяет фоновую задачу очистки.

        Returns
        -------
            None

        """
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
