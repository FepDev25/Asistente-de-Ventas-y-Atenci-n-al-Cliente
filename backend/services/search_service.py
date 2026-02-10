"""
El Cerebro del Agente (Search Service).
Ahora orquesta múltiples agentes especializados a través del AgentOrchestrator.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, TYPE_CHECKING
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from backend.domain.agent_schemas import AgentState

if TYPE_CHECKING:
    from backend.agents.orchestrator import AgentOrchestrator
    from backend.services.session_service import SessionService
    from backend.services.chat_history_service import ChatHistoryService


@dataclass
class SearchResult:
    answer: str
    agent_used: Optional[str] = None
    metadata: Optional[Dict] = None


class SearchService:
    """
    SearchService - Punto de entrada para búsquedas semánticas.

    Ahora delega al sistema multi-agente:
    - RetrieverAgent: Búsqueda SQL rápida
    - SalesAgent: Persuasión con LLM (Alex)

    Checkout se maneja vía GraphQL createOrder (frontend directo).
    Mantiene sesiones de usuario para conversaciones continuas usando Redis.
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        session_service: Optional[SessionService] = None,
        chat_history_service: Optional['ChatHistoryService'] = None,
        session_factory: Optional[object] = None,
    ):
        self.orchestrator = orchestrator
        self.session_service = session_service
        # Optional service used to persist chat messages to PostgreSQL
        self.chat_history_service = chat_history_service
        # Async session factory (async_sessionmaker) to create DB sessions
        self.session_factory = session_factory

        # Fallback a memoria si no hay SessionService (desarrollo/testing)
        if self.session_service is None:
            logger.warning(
                "⚠️ SessionService no configurado, usando memoria (NO usar en producción)"
            )
            self._fallback_sessions: Dict[str, AgentState] = {}

        logger.info(
            f"SearchService inicializado con AgentOrchestrator "
            f"(sesiones: {'Redis' if self.session_service else 'Memoria'}, "
            f"chat_history: {'enabled' if self.chat_history_service else 'disabled'})"
        )

    async def semantic_search(
        self, query: str, session_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> SearchResult:
        """
        Recibe el texto del usuario y devuelve la respuesta del agente apropiado.

        Args:
            query: Consulta del usuario
            session_id: ID de sesión para mantener contexto (opcional)
            user_id: ID del usuario autenticado (opcional pero necesario para checkout)

        Returns:
            SearchResult con la respuesta y metadata
        """
        logger.info(f"SearchService procesando query: {query[:50]}...")

        # Obtener o crear estado de sesión
        session_state = None
        if session_id:
            if self.session_service:
                # Usar Redis
                session_state = await self.session_service.get_session(session_id)
                if session_state:
                    logger.debug(f"Sesión recuperada de Redis: {session_id}")
                else:
                    logger.debug(f"Nueva sesión (Redis): {session_id}")
            else:
                # Fallback a memoria
                session_state = self._fallback_sessions.get(session_id)
                if session_state:
                    logger.debug(f"Sesión recuperada de memoria: {session_id}")
                else:
                    logger.debug(f"Nueva sesión (memoria): {session_id}")

        # Delegar al orquestador
        response = await self.orchestrator.process_query(query, session_state, user_id=user_id)

        # Guardar estado actualizado
        if session_id:
            if self.session_service:
                # Guardar en Redis con TTL
                await self.session_service.save_session(session_id, response.state)
            else:
                # Fallback a memoria
                self._fallback_sessions[session_id] = response.state

        # Convertir AgentResponse a SearchResult
        result = SearchResult(
            answer=response.message,
            agent_used=response.agent_name,
            metadata={
                "user_style": response.state.user_style,
                "intent": response.state.detected_intent,
                "products_found": (
                    len(response.state.search_results)
                    if response.state.search_results
                    else 0
                ),
                "in_checkout": response.state.checkout_stage is not None,
                **response.metadata,
            },
        )

        # Persistir mensajes en BD (usuario -> agente) si el servicio está disponible
        try:
            if self.chat_history_service and self.session_factory and session_id and user_id:
                # Crear sesión de DB y guardar ambos mensajes (user y agent)
                async with self.session_factory() as db_session:  # type: AsyncSession
                    # Guardar mensaje del usuario
                    await self.chat_history_service.add_message(
                        session=db_session,
                        session_id=session_id,
                        user_id=user_id,
                        role="USER",
                        message=query,
                        cache_only=False,
                    )

                    # Guardar respuesta del agente
                    await self.chat_history_service.add_message(
                        session=db_session,
                        session_id=session_id,
                        user_id=user_id,
                        role="AGENT",
                        message=response.message,
                        cache_only=False,
                    )
        except Exception as e:
            logger.error(f"Error persisting chat messages: {e}")

        logger.info(
            f"Respuesta generada por: {result.agent_used} "
            f"(estilo: {result.metadata['user_style']}, "
            f"intención: {result.metadata['intent']})"
        )

        return result

    async def clear_session(self, session_id: str) -> bool:
        """Limpia una sesión específica."""
        if self.session_service:
            return await self.session_service.delete_session(session_id)
        else:
            # Fallback a memoria
            if session_id in self._fallback_sessions:
                del self._fallback_sessions[session_id]
                logger.info(f"Sesión {session_id} eliminada (memoria)")
                return True
            return False

    async def get_session_count(self) -> int:
        """Retorna el número de sesiones activas."""
        if self.session_service:
            return await self.session_service.get_session_count()
        else:
            # Fallback a memoria
            return len(self._fallback_sessions)

    async def get_session_state(self, session_id: str) -> Optional[AgentState]:
        """Obtiene el estado de una sesión específica."""
        if self.session_service:
            return await self.session_service.get_session(session_id)
        else:
            # Fallback a memoria
            return self._fallback_sessions.get(session_id)