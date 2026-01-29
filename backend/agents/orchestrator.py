"""
Orquestador de Agentes - Coordina el flujo entre múltiples agentes.
"""
from typing import Optional, Dict
from loguru import logger

from backend.agents.base import BaseAgent
from backend.agents.retriever_agent import RetrieverAgent
from backend.agents.sales_agent import SalesAgent
from backend.agents.checkout_agent import CheckoutAgent
from backend.domain.agent_schemas import (
    AgentState,
    AgentResponse,
    IntentClassification,
    UserStyleProfile,
)
from backend.llm.provider import LLMProvider


class AgentOrchestrator:
    """
    Orquestador que coordina múltiples agentes especializados.

    Responsabilidades:
    - Detectar intención del usuario
    - Detectar estilo de comunicación del usuario
    - Seleccionar el agente apropiado
    - Gestionar transferencias entre agentes
    - Mantener estado de la conversación
    """

    def __init__(
        self,
        retriever_agent: RetrieverAgent,
        sales_agent: SalesAgent,
        checkout_agent: CheckoutAgent,
        llm_provider: LLMProvider,
    ):
        self.agents: Dict[str, BaseAgent] = {
            "retriever": retriever_agent,
            "sales": sales_agent,
            "checkout": checkout_agent,
        }
        self.llm_provider = llm_provider
        logger.info("AgentOrchestrator inicializado con 3 agentes")

    async def process_query(
        self, query: str, session_state: Optional[AgentState] = None
    ) -> AgentResponse:
        """
        Procesa un query del usuario coordinando entre agentes.

        Args:
            query: Consulta del usuario
            session_state: Estado de sesión existente (opcional)

        Returns:
            AgentResponse del agente seleccionado
        """
        # Inicializar o actualizar estado
        state = session_state or AgentState(user_query=query)
        state.user_query = query

        # Detectar estilo de usuario si no está definido
        if not state.user_style or state.user_style == "neutral":
            style_profile = await self._detect_user_style(state)
            state.user_style = style_profile.style
            logger.info(
                f"Estilo detectado: {state.user_style} (confianza: {style_profile.confidence})"
            )

        # Detectar intención si no está en checkout
        if state.checkout_stage is None:
            intent = await self._classify_intent(state)
            state.detected_intent = intent.intent
            logger.info(
                f"Intención detectada: {intent.intent} -> Agente: {intent.suggested_agent}"
            )
            current_agent_name = intent.suggested_agent
        else:
            # Si está en checkout, usar CheckoutAgent
            current_agent_name = "checkout"
            logger.info("En proceso de checkout, usando CheckoutAgent")

        # Seleccionar y ejecutar agente
        agent = self.agents[current_agent_name]
        response = await agent.process(state)

        # Manejar transferencias entre agentes
        max_transfers = 3  # Evitar loops infinitos
        transfer_count = 0

        while response.should_transfer and transfer_count < max_transfers:
            transfer_count += 1
            logger.info(
                f"Transferencia #{transfer_count}: {current_agent_name} -> {response.transfer_to}"
            )

            # Transferir a nuevo agente
            next_agent_name = response.transfer_to
            if next_agent_name not in self.agents:
                logger.error(
                    f"Agente de transferencia '{next_agent_name}' no existe"
                )
                break

            next_agent = self.agents[next_agent_name]
            current_agent_name = next_agent_name

            # Procesar con nuevo agente
            response = await next_agent.process(response.state)

        if transfer_count >= max_transfers:
            logger.warning(
                f"Máximo de transferencias alcanzado ({max_transfers})"
            )

        logger.info(
            f"Query procesado por agente final: {response.agent_name}"
        )
        return response

    async def _classify_intent(
        self, state: AgentState
    ) -> IntentClassification:
        """
        Clasifica la intención del usuario usando lógica de reglas.

        Intenciones:
        - search: Buscar productos
        - persuasion: Dudas, objeciones, preguntas
        - checkout: Comprar, confirmar pedido
        - info: Información general (políticas, horarios, etc.)
        """
        query_lower = state.user_query.lower()

        # Palabras clave por intención
        search_keywords = [
            "buscar",
            "busco",
            "mostrar",
            "muéstrame",
            "quiero ver",
            "tienes",
            "hay",
            "talla",
            "color",
            "marca",
            "modelo",
            "catálogo",
        ]

        checkout_keywords = [
            "comprar",
            "cómprame",
            "dámelos",
            "dámelo",
            "envíame",
            "envía",
            "quiero",
            "lo quiero",
            "los quiero",
            "confirma",
            "procede",
        ]

        info_keywords = [
            "horario",
            "hora",
            "ubicación",
            "dirección",
            "garantía",
            "devolución",
            "envío",
            "delivery",
            "pago",
            "tarjeta",
        ]

        persuasion_keywords = [
            "caro",
            "precio",
            "barato",
            "descuento",
            "oferta",
            "recomienda",
            "mejor",
            "diferencia",
            "vale la pena",
            "duda",
            "por qué",
        ]

        # Contar coincidencias
        search_score = sum(
            1 for kw in search_keywords if kw in query_lower
        )
        checkout_score = sum(
            1 for kw in checkout_keywords if kw in query_lower
        )
        info_score = sum(1 for kw in info_keywords if kw in query_lower)
        persuasion_score = sum(
            1 for kw in persuasion_keywords if kw in query_lower
        )

        # Determinar intención con mayor score
        scores = {
            "search": search_score,
            "checkout": checkout_score,
            "info": info_score,
            "persuasion": persuasion_score,
        }

        max_intent = max(scores, key=scores.get)
        max_score = scores[max_intent]

        # Si hay resultados de búsqueda previos, favorecer persuasion/checkout
        if state.search_results and len(state.search_results) > 0:
            if checkout_score > 0 or any(
                word in query_lower
                for word in ["sí", "si", "ok", "dale", "bueno"]
            ):
                max_intent = "checkout"
                max_score = 3
            elif persuasion_score > 0 or max_score == 0:
                max_intent = "persuasion"
                max_score = 2

        # Si no hay keywords claros, default a persuasion (sales agent)
        if max_score == 0:
            max_intent = "persuasion"
            max_score = 1

        # Mapear intención a agente
        intent_to_agent = {
            "search": "retriever",
            "persuasion": "sales",
            "checkout": "checkout",
            "info": "sales",  # Sales agent maneja info con RAG
        }

        confidence = min(max_score / 3.0, 1.0)  # Normalizar a 0-1

        return IntentClassification(
            intent=max_intent,
            confidence=confidence,
            suggested_agent=intent_to_agent[max_intent],
            reasoning=f"Keyword matches: {max_intent}={max_score}",
        )

    async def _detect_user_style(
        self, state: AgentState
    ) -> UserStyleProfile:
        """
        Detecta el estilo de comunicación del usuario.

        Estilos:
        - cuencano: Modismos ecuatorianos (ayayay, ve, full, lindo)
        - juvenil: Lenguaje casual (che, bro, tipo, re)
        - formal: Lenguaje profesional (usted, formal)
        - neutral: Estándar
        """
        # Analizar últimos 5 mensajes del usuario
        user_messages = [
            msg["content"]
            for msg in state.conversation_history[-5:]
            if msg["role"] == "user"
        ]
        user_messages.append(state.user_query)

        combined_text = " ".join(user_messages).lower()

        # Patrones por estilo
        cuencano_patterns = [
            "ayayay",
            " ve ",
            " ve,",
            " ve?",
            "full",
            "chevere",
            "lindo",
            "pana",
        ]
        juvenil_patterns = [
            "che",
            "bro",
            "tipo",
            " re ",
            "mal",
            "onda",
            "copado",
        ]
        formal_patterns = [
            "usted",
            "señor",
            "señora",
            "por favor",
            "disculpe",
            "agradezco",
        ]

        # Contar matches
        cuencano_count = sum(
            1 for pattern in cuencano_patterns if pattern in combined_text
        )
        juvenil_count = sum(
            1 for pattern in juvenil_patterns if pattern in combined_text
        )
        formal_count = sum(
            1 for pattern in formal_patterns if pattern in combined_text
        )

        # Determinar estilo dominante
        if cuencano_count >= 2:
            return UserStyleProfile(
                style="cuencano",
                confidence=min(cuencano_count / 3.0, 1.0),
                detected_patterns=cuencano_patterns[:cuencano_count],
                sample_messages=user_messages[-3:],
            )
        elif juvenil_count >= 2:
            return UserStyleProfile(
                style="juvenil",
                confidence=min(juvenil_count / 3.0, 1.0),
                detected_patterns=juvenil_patterns[:juvenil_count],
                sample_messages=user_messages[-3:],
            )
        elif formal_count >= 1:
            return UserStyleProfile(
                style="formal",
                confidence=min(formal_count / 2.0, 1.0),
                detected_patterns=formal_patterns[:formal_count],
                sample_messages=user_messages[-3:],
            )
        else:
            return UserStyleProfile(
                style="neutral",
                confidence=1.0,
                detected_patterns=[],
                sample_messages=user_messages[-3:],
            )

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Obtiene un agente por nombre."""
        return self.agents.get(agent_name)

    def list_agents(self) -> list[str]:
        """Lista todos los agentes disponibles."""
        return list(self.agents.keys())
