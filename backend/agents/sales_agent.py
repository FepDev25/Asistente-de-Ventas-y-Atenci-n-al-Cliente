"""
Agente Vendedor - Persuasión y cierre de ventas con LLM.
"""
from typing import List
import asyncio
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.agents.base import BaseAgent
from backend.domain.agent_schemas import AgentState, AgentResponse
from backend.llm.provider import LLMProvider
from backend.services.rag_service import RAGService


class SalesAgent(BaseAgent):
    """
    Agente Vendedor "Alex" - Especializado en persuasión y cierre.

    Responsabilidades:
    - Persuasión sobre objeciones de precio
    - Cross-selling y upselling
    - Manejo de dudas del cliente
    - Crear urgencia (stock limitado)
    - Cierre de venta (transferir a Checkout)
    - Adaptar tono según estilo del usuario
    """

    def __init__(self, llm_provider: LLMProvider, rag_service: RAGService):
        super().__init__(agent_name="sales")
        self.llm_provider = llm_provider
        self.rag_service = rag_service

    def can_handle(self, state: AgentState) -> bool:
        """
        El SalesAgent maneja:
        - Objeciones de precio
        - Preguntas sobre productos
        - Solicitudes de recomendaciones
        - Dudas generales
        - Cualquier interacción que requiera persuasión
        """
        if state.detected_intent == "persuasion":
            return True

        # Palabras clave que indican necesidad de persuasión
        persuasion_keywords = [
            "caro",
            "precio",
            "barato",
            "descuento",
            "oferta",
            "mejor",
            "recomienda",
            "duda",
            "no sé",
            "diferencia",
            "vale la pena",
            "por qué",
        ]

        query_lower = state.user_query.lower()
        return any(keyword in query_lower for keyword in persuasion_keywords)

    async def process(self, state: AgentState) -> AgentResponse:
        """
        Procesa interacciones de venta con LLM con manejo robusto de errores.

        Flujo:
        1. Detecta estilo de usuario (si no está detectado)
        2. Construye system prompt personalizado
        3. Consulta RAG si es necesario para info adicional
        4. Genera respuesta persuasiva con LLM (con timeout y retry)
        5. Detecta si debe transferir a Checkout

        Error Handling:
        - Timeout del LLM (>10s) → Mensaje de disculpa
        - Error de conexión → Fallback gracioso
        - Respuesta vacía → Mensaje genérico
        """
        logger.info(f"SalesAgent procesando: {state.user_query}")

        try:
            # Construir system prompt adaptado al estilo del usuario
            system_prompt = self._build_system_prompt(state)

            # Construir contexto de la conversación
            messages = self._build_conversation_messages(state, system_prompt)

            # Llamar al LLM con timeout y retry
            assistant_message = await self._call_llm_with_retry(messages)

            # Validar respuesta
            if not assistant_message or len(assistant_message.strip()) == 0:
                logger.warning("LLM retornó respuesta vacía")
                assistant_message = self._get_fallback_message(state)

        except asyncio.TimeoutError:
            logger.error(
                "LLM timeout después de múltiples intentos",
                exc_info=True
            )
            assistant_message = self._get_timeout_message(state)

        except Exception as e:
            logger.error(
                f"Error inesperado en SalesAgent: {str(e)}",
                exc_info=True
            )
            assistant_message = self._get_error_message(state, e)

        # Actualizar historial (siempre, incluso con errores)
        state = self._add_to_history(state, "user", state.user_query)
        state = self._add_to_history(state, "assistant", assistant_message)

        # Detectar si hay intención de compra (solo si no es mensaje de error)
        should_transfer = False
        transfer_to = None

        if not self._is_error_message(assistant_message):
            try:
                should_transfer, transfer_to = self._detect_checkout_intent(
                    state.user_query, assistant_message
                )
            except Exception as e:
                logger.error(
                    f"Error detectando intención de checkout: {str(e)}"
                )
                # No transferir si hay error

        logger.info(
            f"SalesAgent completado - Transfer: {should_transfer} to {transfer_to}"
        )

        return self._create_response(
            message=assistant_message,
            state=state,
            should_transfer=should_transfer,
            transfer_to=transfer_to,
        )

    async def _call_llm_with_retry(
        self, messages: List, max_retries: int = 2, timeout: float = 10.0
    ) -> str:
        """
        Llama al LLM con retry logic y timeout.

        Args:
            messages: Mensajes para el LLM
            max_retries: Número máximo de reintentos
            timeout: Timeout en segundos por intento

        Returns:
            Respuesta del LLM

        Raises:
            asyncio.TimeoutError: Si todos los intentos fallan por timeout
            Exception: Si hay otro error después de reintentos
        """
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"Reintento {attempt}/{max_retries} de llamada LLM")
                    # Esperar antes de reintentar (exponential backoff)
                    await asyncio.sleep(2 ** attempt)

                # Llamar LLM con timeout
                response = await asyncio.wait_for(
                    self.llm_provider.model.ainvoke(messages),
                    timeout=timeout
                )

                # Extraer contenido
                content = response.content

                # Validar que no esté vacío
                if isinstance(content, str) and content.strip():
                    return content.strip()
                else:
                    logger.warning(f"LLM retornó contenido vacío en intento {attempt + 1}")
                    last_error = ValueError("Empty response from LLM")
                    continue

            except asyncio.TimeoutError as e:
                logger.warning(
                    f"LLM timeout en intento {attempt + 1}/{max_retries + 1} "
                    f"(timeout: {timeout}s)"
                )
                last_error = e
                continue

            except Exception as e:
                logger.warning(
                    f"Error en llamada LLM (intento {attempt + 1}/{max_retries + 1}): {str(e)}"
                )
                last_error = e
                continue

        # Si llegamos aquí, todos los intentos fallaron
        if isinstance(last_error, asyncio.TimeoutError):
            raise asyncio.TimeoutError(
                f"LLM no respondió después de {max_retries + 1} intentos"
            )
        else:
            raise last_error or Exception("LLM call failed after retries")

    def _get_fallback_message(self, state: AgentState) -> str:
        """Mensaje de fallback cuando LLM falla pero no es timeout."""
        style = state.user_style or "neutral"

        messages = {
            "cuencano": (
                "Ayayay, disculpa ve, tuve un problemita técnico. "
                "¿Puedes repetir tu pregunta?"
            ),
            "juvenil": (
                "Uh, perdón bro, tuve un error técnico. "
                "¿Podés repetir?"
            ),
            "formal": (
                "Disculpe, he tenido un inconveniente técnico. "
                "¿Podría reformular su consulta?"
            ),
            "neutral": (
                "Lo siento, tuve un problema técnico. "
                "¿Puedes intentar de nuevo?"
            ),
        }

        return messages.get(style, messages["neutral"])

    def _get_timeout_message(self, state: AgentState) -> str:
        """Mensaje cuando el LLM hace timeout."""
        style = state.user_style or "neutral"

        messages = {
            "cuencano": (
                "Ayayay, estoy un poco lento ahorita ve. "
                "¿Me repites la pregunta? Ahora te respondo más rápido."
            ),
            "juvenil": (
                "Che, perdón, estoy medio lento ahora. "
                "¿Repetís la pregunta? Ahora te contesto al toque."
            ),
            "formal": (
                "Disculpe la demora. Estoy experimentando lentitud en el sistema. "
                "¿Podría reformular su consulta?"
            ),
            "neutral": (
                "Disculpa la demora. El sistema está un poco lento. "
                "¿Puedes repetir tu pregunta?"
            ),
        }

        return messages.get(style, messages["neutral"])

    def _get_error_message(self, state: AgentState, error: Exception) -> str:
        """Mensaje genérico de error."""
        style = state.user_style or "neutral"

        # Loggear el error pero no exponerlo al usuario
        error_type = type(error).__name__

        messages = {
            "cuencano": (
                "Ayayay, tuve un problemita ve. "
                "¿Puedo ayudarte con algo más?"
            ),
            "juvenil": (
                "Uh, hubo un error bro. "
                "¿Querés que te ayude con otra cosa?"
            ),
            "formal": (
                "Lamento informarle que ha ocurrido un error técnico. "
                "¿Puedo asistirle con algo más?"
            ),
            "neutral": (
                "Lo siento, ocurrió un error. "
                "¿Puedo ayudarte con algo más?"
            ),
        }

        logger.debug(f"Error type for user message: {error_type}")
        return messages.get(style, messages["neutral"])

    def _is_error_message(self, message: str) -> bool:
        """Detecta si un mensaje es un mensaje de error/fallback."""
        error_indicators = [
            "problema técnico",
            "problemita",
            "error técnico",
            "inconveniente técnico",
            "demora",
            "lentitud",
            "un poco lento",
        ]

        message_lower = message.lower()
        return any(indicator in message_lower for indicator in error_indicators)

    def _build_system_prompt(self, state: AgentState) -> str:
        """
        Construye el system prompt adaptado al estilo del usuario.
        """
        style = state.user_style or "neutral"

        # Base común para todos los estilos
        base_prompt = """Eres Alex, un vendedor experto de calzado deportivo de alta gama.

**TU OBJETIVO:** Cerrar ventas siendo persuasivo pero genuino.

**TÉCNICAS DE VENTA:**
1. **Manejo de Objeciones de Precio:**
   - Justifica el precio con calidad, durabilidad, tecnología
   - Compara con productos económicos (a la larga ahorran más)
   - Menciona garantías y soporte post-venta

2. **Crear Urgencia:**
   - "Solo quedan X unidades en tu talla"
   - "Esta promoción termina pronto"
   - "Es uno de nuestros modelos más vendidos"

3. **Cross-Selling:**
   - Sugiere complementos: calcetines técnicos, limpiadores, protectores
   - "Con estos zapatos, te recomiendo también..."

4. **Cierre Activo:**
   - Termina SIEMPRE con llamado a la acción
   - "¿Te los envío?", "¿Confirmamos el pedido?", "¿Procedemos?"

5. **Información Precisa:**
   - NUNCA inventes productos o stock
   - Si no sabes algo, admítelo y ofrece averiguar"""

        # Adaptaciones según estilo
        style_adaptations = {
            "cuencano": """

**ESTILO DE COMUNICACIÓN: CUENCANO**
- Usa modismos: "ayayay", "ve", "full", "chevere", "lindo"
- Tono cercano y amigable, como un amigo
- Ejemplos:
  * "Ayayay, estos están de lujo ve"
  * "Full buenos estos, te van a durar full"
  * "Qué lindo se te verían"
""",
            "juvenil": """

**ESTILO DE COMUNICACIÓN: JUVENIL**
- Tono casual y energético
- Usa: "che", "bro", "tipo", "re", "mal"
- Emojis moderados
- Ejemplos:
  * "Che, estos están re copados"
  * "Son tipo, los mejores para correr"
  * "Re duraderos, bro"
""",
            "formal": """

**ESTILO DE COMUNICACIÓN: FORMAL**
- Trato de usted
- Lenguaje profesional y educado
- Sin modismos ni jerga
- Ejemplos:
  * "Estos modelos le ofrecen excelente durabilidad"
  * "Le recomendaría considerar..."
  * "¿Desea que proceda con el pedido?"
""",
            "neutral": """

**ESTILO DE COMUNICACIÓN: NEUTRAL**
- Tono amigable pero profesional
- Lenguaje claro y directo
- Tuteo estándar
- Ejemplos:
  * "Estos zapatos tienen muy buena relación calidad-precio"
  * "Te recomiendo estos por su durabilidad"
  * "¿Quieres que confirmemos el pedido?"
""",
        }

        style_addition = style_adaptations.get(
            style, style_adaptations["neutral"]
        )

        # Agregar contexto de productos si hay búsqueda reciente
        products_context = ""
        if state.search_results:
            products_context = f"""

**PRODUCTOS DISPONIBLES:**
{self._format_products_for_context(state.search_results[:5])}

Usa esta información para hacer recomendaciones específicas y precisas.
"""

        return base_prompt + style_addition + products_context

    def _build_conversation_messages(
        self, state: AgentState, system_prompt: str
    ) -> List:
        """Construye la lista de mensajes para el LLM."""
        messages = [SystemMessage(content=system_prompt)]

        # Agregar historial reciente (últimos 10 mensajes)
        recent_history = state.conversation_history[-10:]
        for msg in recent_history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))

        # Agregar mensaje actual
        messages.append(HumanMessage(content=state.user_query))

        return messages

    def _format_products_for_context(self, products: List[dict]) -> str:
        """Formatea productos para incluir en el system prompt."""
        lines = []
        for p in products:
            lines.append(
                f"- {p['name']}: ${p['price']:,.2f} (Stock: {p['stock']})"
            )
        return "\n".join(lines)

    def _detect_checkout_intent(
        self, user_query: str, assistant_response: str
    ) -> tuple[bool, str | None]:
        """
        Detecta si el usuario está listo para comprar.

        Patrones de compra:
        - "dámelos", "los quiero", "cómpralo", "envíamelos"
        - "sí", "ok", "dale" (después de oferta)
        - "procede", "confirma"
        """
        checkout_keywords = [
            "dámelos",
            "dámelo",
            "los quiero",
            "lo quiero",
            "cómprame",
            "envíame",
            "envía",
            "comprar",
            "quiero comprar",
            "procede",
            "confirma",
            "ok",
            "dale",
            "sí",
            "si",
            "bueno",
        ]

        query_lower = user_query.lower().strip()

        # Verificar patrones de confirmación
        for keyword in checkout_keywords:
            if keyword in query_lower:
                # Confirmar que hay productos en contexto
                logger.info(
                    f"Checkout intent detectado con keyword: {keyword}"
                )
                return True, "checkout"

        # Verificar si el asistente preguntó por confirmación
        confirmation_phrases = [
            "¿te los envío?",
            "¿confirmamos?",
            "¿procedemos?",
            "¿te lo mando?",
            "¿hacemos el pedido?",
        ]

        assistant_lower = assistant_response.lower()
        for phrase in confirmation_phrases:
            if phrase in assistant_lower and len(query_lower) < 20:
                # Si el asistente preguntó y el usuario dio respuesta corta afirmativa
                affirmative_words = ["sí", "si", "ok", "dale", "bueno", "ya"]
                if any(word in query_lower for word in affirmative_words):
                    logger.info(
                        f"Checkout intent por confirmación: {query_lower}"
                    )
                    return True, "checkout"

        return False, None
