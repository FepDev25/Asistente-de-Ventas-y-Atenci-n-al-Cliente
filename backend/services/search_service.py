"""
El Cerebro del Agente (Search Service).
Ahora orquesta múltiples agentes especializados a través del AgentOrchestrator.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, TYPE_CHECKING
from loguru import logger

from backend.domain.agent_schemas import AgentState

if TYPE_CHECKING:
    from backend.agents.orchestrator import AgentOrchestrator
    from backend.services.session_service import SessionService


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
    - CheckoutAgent: Cierre de pedidos

    Mantiene sesiones de usuario para conversaciones continuas usando Redis.
    """

    def __init__(
        self,
        orchestrator: AgentOrchestrator,
        session_service: Optional[SessionService] = None,
    ):
        self.orchestrator = orchestrator
        self.session_service = session_service

        # Fallback a memoria si no hay SessionService (desarrollo/testing)
        if self.session_service is None:
            logger.warning(
                "⚠️ SessionService no configurado, usando memoria (NO usar en producción)"
            )
            self._fallback_sessions: Dict[str, AgentState] = {}

        logger.info(
            f"SearchService inicializado con AgentOrchestrator "
            f"(sesiones: {'Redis' if self.session_service else 'Memoria'})"
        )

    async def semantic_search(
        self, query: str, session_id: Optional[str] = None
    ) -> SearchResult:
        """
        Recibe el texto del usuario y devuelve la respuesta del agente apropiado.

        Args:
            query: Consulta del usuario
            session_id: ID de sesión para mantener contexto (opcional)

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
        response = await self.orchestrator.process_query(query, session_state)

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