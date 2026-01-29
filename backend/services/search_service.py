"""
El Cerebro del Agente (Search Service).
Ahora orquesta múltiples agentes especializados a través del AgentOrchestrator.
"""
from dataclasses import dataclass
from typing import Optional, Dict
from loguru import logger
from backend.agents.orchestrator import AgentOrchestrator
from backend.domain.agent_schemas import AgentState


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

    Mantiene sesiones de usuario para conversaciones continuas.
    """

    def __init__(self, orchestrator: AgentOrchestrator):
        self.orchestrator = orchestrator
        # Almacenamiento en memoria de sesiones (simple)
        # TODO: Migrar a Redis para persistencia
        self._sessions: Dict[str, AgentState] = {}
        logger.info("SearchService inicializado con AgentOrchestrator")

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
        if session_id and session_id in self._sessions:
            session_state = self._sessions[session_id]
            logger.debug(f"Sesión recuperada: {session_id}")
        else:
            session_state = None
            if session_id:
                logger.debug(f"Nueva sesión: {session_id}")

        # Delegar al orquestador
        response = await self.orchestrator.process_query(query, session_state)

        # Guardar estado actualizado
        if session_id:
            self._sessions[session_id] = response.state

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

    def clear_session(self, session_id: str) -> bool:
        """Limpia una sesión específica."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Sesión {session_id} eliminada")
            return True
        return False

    def get_session_count(self) -> int:
        """Retorna el número de sesiones activas."""
        return len(self._sessions)

    def get_session_state(self, session_id: str) -> Optional[AgentState]:
        """Obtiene el estado de una sesión específica."""
        return self._sessions.get(session_id)