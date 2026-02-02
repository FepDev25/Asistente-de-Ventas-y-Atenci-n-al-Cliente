"""
Orquestador de Agentes - Coordina el flujo entre múltiples agentes.
"""
from typing import Optional, Dict
import json
import asyncio
from loguru import logger
from langchain_core.messages import SystemMessage, HumanMessage

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
        use_llm_detection: bool = True,  # ✨ NUEVO: Usar LLM para detección
    ):
        self.agents: Dict[str, BaseAgent] = {
            "retriever": retriever_agent,
            "sales": sales_agent,
            "checkout": checkout_agent,
        }
        self.llm_provider = llm_provider
        self.use_llm_detection = use_llm_detection

        detection_method = "LLM Zero-shot" if use_llm_detection else "Keywords"
        logger.info(
            f"AgentOrchestrator inicializado con 3 agentes "
            f"(Detección: {detection_method})"
        )

    async def process_query(
        self, query: str, session_state: Optional[AgentState] = None
    ) -> AgentResponse:
        """
        Procesa un query del usuario coordinando entre agentes con manejo robusto de errores.

        Args:
            query: Consulta del usuario
            session_state: Estado de sesión existente (opcional)

        Returns:
            AgentResponse del agente seleccionado

        Error Handling:
        - Agente falla → Fallback a SalesAgent con mensaje de error
        - Transferencia inválida → Detiene transferencias
        - Loop detectado → Rompe ciclo
        - Error crítico → Respuesta de emergencia
        """
        try:
            # Inicializar o actualizar estado
            state = session_state or AgentState(user_query=query)
            state.user_query = query

            # DETECCIÓN DE STOP INTENT (ANTES de procesar con agentes)
            stop_intent_detected, stop_message = self._detect_stop_intent(state)
            if stop_intent_detected:
                logger.info(f"Stop intent detectado: {query}")
                return AgentResponse(
                    agent_name="orchestrator",
                    message=stop_message,
                    state=state,
                    should_transfer=False,
                    metadata={"stop_intent": True}
                )

            # Detectar estilo de usuario si no está definido
            if not state.user_style or state.user_style == "neutral":
                try:
                    # Usar detección LLM o Keywords según configuración
                    if self.use_llm_detection:
                        style_profile = await self._detect_user_style_llm(state)
                    else:
                        style_profile = await self._detect_user_style_keywords(state)

                    state.user_style = style_profile.style
                    logger.info(
                        f"Estilo detectado: {state.user_style} "
                        f"(confianza: {style_profile.confidence:.2f})"
                    )
                except Exception as e:
                    logger.error(f"Error detectando estilo, usando neutral: {e}")
                    state.user_style = "neutral"

            # Detectar intención si no está en checkout
            if state.checkout_stage is None:
                try:
                    # Usar detección LLM o Keywords según configuración
                    if self.use_llm_detection:
                        intent = await self._classify_intent_llm(state)
                    else:
                        intent = await self._classify_intent_keywords(state)

                    state.detected_intent = intent.intent
                    logger.info(
                        f"Intención detectada: {intent.intent} -> "
                        f"Agente: {intent.suggested_agent} "
                        f"(confianza: {intent.confidence:.2f})"
                    )
                    current_agent_name = intent.suggested_agent
                except Exception as e:
                    logger.error(f"Error detectando intención, usando sales: {e}")
                    current_agent_name = "sales"
                    state.detected_intent = "persuasion"
            else:
                # Si está en checkout, usar CheckoutAgent
                current_agent_name = "checkout"
                logger.info("En proceso de checkout, usando CheckoutAgent")

            # Validar que el agente existe
            if current_agent_name not in self.agents:
                logger.error(f"Agente '{current_agent_name}' no existe, usando sales")
                current_agent_name = "sales"

            # Seleccionar y ejecutar agente con try/except
            try:
                agent = self.agents[current_agent_name]
                response = await agent.process(state)
            except Exception as e:
                logger.error(
                    f"Error ejecutando agente '{current_agent_name}': {e}",
                    exc_info=True
                )
                # Respuesta de fallback
                response = AgentResponse(
                    agent_name=current_agent_name,
                    message=(
                        "Disculpa, tuve un problema técnico. "
                        "¿Puedes reformular tu pregunta?"
                    ),
                    state=state,
                    should_transfer=False,
                    metadata={"error": str(e)}
                )

            # Manejar transferencias entre agentes con detección de loops
            max_transfers = 3
            transfer_count = 0
            transfer_history = []  # Para detectar loops

            while response.should_transfer and transfer_count < max_transfers:
                transfer_count += 1

                # Crear clave de transferencia para detectar loops
                transfer_key = f"{current_agent_name}->{response.transfer_to}"

                # Detectar loop: misma transferencia 2+ veces
                if transfer_history.count(transfer_key) >= 2:
                    logger.warning(
                        f"❌ Loop detectado en transferencias: {transfer_history}"
                    )
                    break

                transfer_history.append(transfer_key)

                logger.info(
                    f"Transferencia #{transfer_count}: {transfer_key} "
                    f"(historial: {' -> '.join(transfer_history)})"
                )

                # Validar que el agente destino existe
                next_agent_name = response.transfer_to
                if next_agent_name not in self.agents:
                    logger.error(
                        f"Agente de transferencia '{next_agent_name}' no existe"
                    )
                    break

                next_agent = self.agents[next_agent_name]
                current_agent_name = next_agent_name

                # Procesar con nuevo agente con try/except
                try:
                    response = await next_agent.process(response.state)
                except Exception as e:
                    logger.error(
                        f"Error en transferencia a '{next_agent_name}': {e}",
                        exc_info=True
                    )
                    # Detener transferencias en caso de error
                    break

            # Logs finales
            if transfer_count >= max_transfers:
                logger.warning(
                    f"⚠️ Máximo de transferencias alcanzado ({max_transfers})"
                )

            if transfer_history:
                logger.info(
                    f"✅ Flujo de transferencias: "
                    f"{' -> '.join(transfer_history)} -> {response.agent_name}"
                )

            logger.info(
                f"Query procesado por agente final: {response.agent_name}"
            )

            return response

        except Exception as e:
            # Error crítico en orchestrator - respuesta de emergencia
            logger.error(
                f"💥 Error crítico en Orchestrator procesando '{query[:50]}...': {e}",
                exc_info=True
            )

            # Crear estado mínimo si no existe
            emergency_state = session_state or AgentState(user_query=query)
            emergency_state.user_query = query

            return AgentResponse(
                agent_name="orchestrator",
                message=(
                    "Disculpa, tuve un problema técnico. "
                    "¿Puedes intentar de nuevo con una pregunta diferente?"
                ),
                state=emergency_state,
                should_transfer=False,
                metadata={"error": "orchestrator_failure", "error_message": str(e)}
            )

    # DETECCIÓN INTELIGENTE CON LLM ZERO-SHOT

    async def _classify_intent_llm(
        self, state: AgentState
    ) -> IntentClassification:
        """
        Clasifica la intención del usuario usando LLM Zero-shot (Gemini).

        Ventajas sobre keywords:
        - Entiende contexto y negaciones
        - Maneja sinónimos automáticamente
        - Detecta intenciones complejas

        Fallback a keywords si LLM falla.
        """
        try:
            # Construir prompt para clasificación
            system_prompt = """Eres un clasificador de intenciones para un sistema de ventas de calzado deportivo.

Tu tarea es clasificar la intención del usuario en UNA de estas 4 categorías:

1. **search**: El usuario quiere buscar o explorar productos
   - Ejemplos: "busco Nike", "tienes Adidas?", "mostrame zapatillas", "hay talla 42?"

2. **persuasion**: El usuario tiene dudas, objeciones o necesita recomendaciones
   - Ejemplos: "están caros", "cual es mejor?", "no sé cual elegir", "vale la pena?"

3. **checkout**: El usuario quiere comprar o confirmar un pedido
   - Ejemplos: "los quiero", "dámelos", "envíamelos", "confirmo", "procede"

4. **info**: El usuario pide información general (horarios, políticas, ubicación)
   - Ejemplos: "que horarios tienen?", "hacen envíos?", "donde están?", "garantía?"

IMPORTANTE:
- Analiza el CONTEXTO completo, no solo palabras clave
- Si el usuario tiene productos previos vistos, favorece persuasion/checkout
- Si dice "NO busco X", NO es search
- Considera negaciones y el tono

Responde SOLO con un JSON válido en este formato:
{
  "intent": "search" | "persuasion" | "checkout" | "info",
  "confidence": 0.0 a 1.0,
  "reasoning": "Breve explicación de por qué elegiste esta intención"
}"""

            # Construir contexto
            context_parts = [f'Query del usuario: "{state.user_query}"']

            # Agregar contexto de búsquedas previas
            if state.search_results and len(state.search_results) > 0:
                context_parts.append(
                    f"\nCONTEXTO: El usuario ya vio {len(state.search_results)} productos."
                )

            # Agregar historial reciente
            if state.conversation_history:
                recent = state.conversation_history[-3:]
                history_text = "\n".join(
                    [
                        f"- {msg['role']}: {msg['content']}"
                        for msg in recent
                    ]
                )
                context_parts.append(
                    f"\nHISTORIAL RECIENTE:\n{history_text}"
                )

            user_prompt = "\n".join(context_parts)

            # Llamar a Gemini con timeout
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            logger.debug("Llamando a LLM para clasificar intención...")

            response = await asyncio.wait_for(
                self.llm_provider.model.ainvoke(messages),
                timeout=5.0,  # 5 segundos máximo
            )

            # Parsear respuesta JSON
            response_text = response.content.strip()

            # Limpiar markdown si existe
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1]
            if response_text.endswith("```"):
                response_text = response_text.rsplit("```", 1)[0]

            result = json.loads(response_text.strip())

            # Validar campos
            intent = result.get("intent", "persuasion")
            if intent not in ["search", "persuasion", "checkout", "info"]:
                logger.warning(f"Intención inválida del LLM: {intent}")
                intent = "persuasion"

            confidence = float(result.get("confidence", 0.8))
            reasoning = result.get("reasoning", "LLM classification")

            # Mapear intención a agente
            intent_to_agent = {
                "search": "retriever",
                "persuasion": "sales",
                "checkout": "checkout",
                "info": "sales",
            }

            logger.info(
                f"LLM clasificó como '{intent}' (confianza: {confidence:.2f}): {reasoning}"
            )

            return IntentClassification(
                intent=intent,
                confidence=confidence,
                suggested_agent=intent_to_agent[intent],
                reasoning=reasoning,
            )

        except asyncio.TimeoutError:
            logger.warning("LLM timeout en clasificación de intención, usando keywords")
            return await self._classify_intent_keywords(state)

        except json.JSONDecodeError as e:
            logger.warning(
                f"Error parseando JSON del LLM: {e}, usando keywords"
            )
            return await self._classify_intent_keywords(state)

        except Exception as e:
            logger.error(
                f"Error en clasificación LLM: {str(e)}, usando keywords",
                exc_info=True,
            )
            return await self._classify_intent_keywords(state)

    async def _detect_user_style_llm(
        self, state: AgentState
    ) -> UserStyleProfile:
        """
        Detecta el estilo de comunicación del usuario usando LLM Zero-shot.

        Ventajas sobre patterns:
        - Detecta tono sin palabras clave específicas
        - Analiza estructura de oraciones
        - Entiende formalidad contextual

        Fallback a patterns si LLM falla.
        """
        try:
            # Construir prompt para análisis de estilo
            system_prompt = """Eres un analista de estilo de comunicación para un sistema de ventas.

Tu tarea es identificar el estilo de comunicación del usuario analizando sus mensajes.

Los 4 estilos son:

1. **cuencano**: Modismos ecuatorianos, tono cercano y amigable
   - Indicadores: "ayayay", "ve", "full", "chevere", "lindo", "pana"
   - Ejemplo: "Ayayay que lindo ve, busco unos Nike full buenos"

2. **juvenil**: Lenguaje casual, energético, jerga argentina/latina
   - Indicadores: "che", "bro", "tipo", "re", "mal", "onda", "copado"
   - Ejemplo: "Che bro, mostrame algo copado tipo para correr"

3. **formal**: Lenguaje profesional, educado, trato de usted
   - Indicadores: "usted", "señor", "por favor", "disculpe", "quisiera", "agradezco"
   - Ejemplo: "Buenos días, quisiera consultar por zapatillas deportivas"

4. **neutral**: Lenguaje estándar, sin marcadores claros de estilo
   - Tuteo normal, sin modismos ni formalidad excesiva
   - Ejemplo: "Hola, busco zapatillas Nike para correr"

IMPORTANTE:
- Analiza el TONO general, no solo palabras clave
- Considera: vocabulario, nivel de formalidad, estructura de oraciones
- Un solo mensaje puede no ser suficiente, considera el contexto
- Si no hay señales claras, es "neutral"

Responde SOLO con un JSON válido en este formato:
{
  "style": "cuencano" | "juvenil" | "formal" | "neutral",
  "confidence": 0.0 a 1.0,
  "reasoning": "Explicación breve de los indicadores detectados"
}"""

            # Recopilar mensajes del usuario
            user_messages = [
                msg["content"]
                for msg in state.conversation_history[-5:]
                if msg["role"] == "user"
            ]
            user_messages.append(state.user_query)

            # Construir contexto
            messages_text = "\n".join(
                [f"{i+1}. \"{msg}\"" for i, msg in enumerate(user_messages)]
            )

            user_prompt = f"""Analiza el estilo de comunicación en estos mensajes del usuario:

{messages_text}

Determina el estilo predominante basándote en el tono, vocabulario y estructura."""

            # Llamar a Gemini con timeout
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            logger.debug("Llamando a LLM para detectar estilo...")

            response = await asyncio.wait_for(
                self.llm_provider.model.ainvoke(messages),
                timeout=5.0,
            )

            # Parsear respuesta JSON
            response_text = response.content.strip()

            # Limpiar markdown
            if response_text.startswith("```json"):
                response_text = response_text.split("```json")[1]
            if response_text.endswith("```"):
                response_text = response_text.rsplit("```", 1)[0]

            result = json.loads(response_text.strip())

            # Validar campos
            style = result.get("style", "neutral")
            if style not in ["cuencano", "juvenil", "formal", "neutral"]:
                logger.warning(f"Estilo inválido del LLM: {style}")
                style = "neutral"

            confidence = float(result.get("confidence", 0.8))
            reasoning = result.get("reasoning", "LLM analysis")

            logger.info(
                f"LLM detectó estilo '{style}' (confianza: {confidence:.2f}): {reasoning}"
            )

            return UserStyleProfile(
                style=style,
                confidence=confidence,
                detected_patterns=[reasoning],
                sample_messages=user_messages[-3:],
            )

        except asyncio.TimeoutError:
            logger.warning("LLM timeout en detección de estilo, usando patterns")
            return await self._detect_user_style_keywords(state)

        except json.JSONDecodeError as e:
            logger.warning(
                f"Error parseando JSON del LLM: {e}, usando patterns"
            )
            return await self._detect_user_style_keywords(state)

        except Exception as e:
            logger.error(
                f"Error en detección de estilo LLM: {str(e)}, usando patterns",
                exc_info=True,
            )
            return await self._detect_user_style_keywords(state)

    # DETECCIÓN DE STOP INTENT (CANCELACIÓN)

    def _detect_stop_intent(self, state: AgentState) -> tuple[bool, str]:
        """
        Detecta si el usuario quiere cancelar o salir de la conversación.

        Returns:
            (stop_detected: bool, farewell_message: str)
        """
        query_lower = state.user_query.lower().strip()

        # Patrones de cancelación/salida
        stop_patterns = [
            "mejor no",
            "mejor no gracias",
            "luego veo",
            "después veo",
            "chao",
            "adiós",
            "adios",
            "nos vemos",
            "hasta luego",
            "bye",
            "gracias igual",
            "gracias igualmente",
            "ya no",
            "no importa",
            "déjalo",
            "dejalo",
            "olvídalo",
            "olvidalo",
            "no gracias",
            "está muy caro gracias",
            "esta muy caro gracias",
            "muy caro gracias",
        ]

        # Detectar patrones
        for pattern in stop_patterns:
            if pattern in query_lower:
                # Generar mensaje de despedida según estilo
                style = state.user_style or "neutral"
                farewell_messages = {
                    "cuencano": "Entendido ve. Aquí estaré si cambias de opinión. ¡Buen día!",
                    "juvenil": "Ok bro, acá estoy por si cambias de idea. ¡Saludos!",
                    "formal": "Entendido. Quedo a su disposición. ¡Que tenga un buen día!",
                    "neutral": "Entendido. Aquí estaré si cambias de opinión. ¡Buen día!",
                }
                return True, farewell_messages.get(style, farewell_messages["neutral"])

        return False, ""

    # DETECCIÓN LEGACY CON KEYWORDS/PATTERNS (FALLBACK)

    async def _classify_intent_keywords(
        self, state: AgentState
    ) -> IntentClassification:
        """
        Clasifica la intención del usuario usando keywords (método legacy).

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

    async def _detect_user_style_keywords(
        self, state: AgentState
    ) -> UserStyleProfile:
        """
        Detecta el estilo de comunicación del usuario usando patterns (método legacy).

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
