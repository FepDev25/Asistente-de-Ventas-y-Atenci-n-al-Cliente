"""
Agente Vendedor - Persuasión y cierre de ventas con LLM.
Incluye integración con Agente 2 para reconocimiento de imágenes.
"""
from typing import List
import asyncio
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.agents.base import BaseAgent
from backend.domain.agent_schemas import AgentState, AgentResponse
from backend.llm.provider import LLMProvider
from backend.services.rag_service import RAGService
from backend.tools.agent2_recognition_client import ProductRecognitionClient


class SalesAgent(BaseAgent):
    """
    Agente Vendedor "Alex" - Especializado en persuasión y cierre.
    
    También maneja reconocimiento de productos por imagen usando el Agente 2.

    Responsabilidades:
    - Persuasión sobre objeciones de precio
    - Cross-selling y upselling
    - Manejo de dudas del cliente
    - Crear urgencia (stock limitado)
    - Cierre de venta (transferir a Checkout)
    - Adaptar tono según estilo del usuario
    - Reconocimiento de productos por imagen (Agente 2)
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
        - Imágenes de productos (reconocimiento visual)
        - Cualquier interacción que requiera persuasión
        """
        # Si hay una imagen subida, el SalesAgent debe manejarla
        if state.uploaded_image is not None:
            return True
        
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

    async def _process_image_query(self, state: AgentState) -> AgentResponse:
        """
        Procesa una consulta que incluye una imagen usando el Agente 2.
        
        Envía la imagen al servicio de reconocimiento SIFT y actualiza
        el estado con el producto detectado.
        
        Args:
            state: Estado del agente con uploaded_image
            
        Returns:
            AgentResponse con el resultado del reconocimiento
        """
        logger.info("SalesAgent procesando imagen con Agente 2")
        
        if not state.uploaded_image:
            return self._create_response(
                message="No pude procesar la imagen. ¿Puedes intentar de nuevo?",
                state=state
            )
        
        client = ProductRecognitionClient()
        try:
            result = await client.recognize_product(
                image_bytes=state.uploaded_image,
                filename=state.uploaded_image_filename or "image.jpg"
            )
            
            if result["success"] and result["product_name"]:
                # Producto detectado exitosamente
                product_name = result["product_name"]
                confidence = result["confidence"]
                matches = result["matches"]
                
                # Actualizar estado
                state.detected_product_from_image = product_name
                state.image_recognition_confidence = confidence
                
                # Agregar al historial
                state = self._add_to_history(
                    state, 
                    "user", 
                    f"[Imagen: {product_name}]"
                )
                
                # Construir mensaje según confianza
                style = state.user_style or "neutral"
                
                if confidence >= 0.8:
                    # Alta confianza
                    messages = {
                        "cuencano": (
                            f"¡Veo que tienes unos **{product_name}**! "
                            f"Son de lujo ve. ¿Quieres que te busque detalles o los agregamos al carrito?"
                        ),
                        "juvenil": (
                            f"Che, reconocí esos **{product_name}** al toque. "
                            f"Son re buenos. ¿Los querés ver o los agregamos?"
                        ),
                        "formal": (
                            f"He identificado los **{product_name}** en su imagen. "
                            f"¿Desea que le muestre los detalles o procedemos con la compra?"
                        ),
                        "neutral": (
                            f"Reconocí los **{product_name}** en tu imagen. "
                            f"¿Quieres ver los detalles o agregarlos al carrito?"
                        ),
                    }
                elif confidence >= 0.5:
                    # Confianza media
                    messages = {
                        "cuencano": (
                            f"Creo que son unos **{product_name}** (no estoy 100% seguro). "
                            f"¿Es correcto ve?"
                        ),
                        "juvenil": (
                            f"Parecen ser **{product_name}**, pero no estoy tan seguro. "
                            f"¿Es eso che?"
                        ),
                        "formal": (
                            f"Parecen ser **{product_name}**, aunque no estoy completamente seguro. "
                            f"¿Es correcto?"
                        ),
                        "neutral": (
                            f"Parecen ser **{product_name}** (confianza media). "
                            f"¿Es correcto?"
                        ),
                    }
                else:
                    # Baja confianza
                    messages = {
                        "cuencano": (
                            f"No estoy muy seguro, pero podrían ser **{product_name}**. "
                            f"¿Me puedes confirmar ve?"
                        ),
                        "juvenil": (
                            f"No estoy seguro bro, ¿son **{product_name}**? "
                            f"¿Me confirmás?"
                        ),
                        "formal": (
                            f"No estoy completamente seguro, pero podrían ser **{product_name}**. "
                            f"¿Podría confirmarlo?"
                        ),
                        "neutral": (
                            f"No estoy muy seguro, pero podrían ser **{product_name}**. "
                            f"¿Puedes confirmarlo?"
                        ),
                    }
                
                message = messages.get(style, messages["neutral"])
                
                # Actualizar query para búsqueda semántica
                state.user_query = f"Quiero información sobre {product_name}"
                
                return self._create_response(
                    message=message,
                    state=state
                )
                
            else:
                # No se pudo reconocer el producto
                logger.warning(f"Agent 2 no reconoció el producto: {result.get('error')}")
                
                state = self._add_to_history(
                    state, 
                    "user", 
                    "[Imagen: no reconocida]"
                )
                
                style = state.user_style or "neutral"
                messages = {
                    "cuencano": (
                        "No pude identificar ese producto en la imagen ve. "
                        "¿Puedes describirme qué es? ¿Marca, modelo, color?"
                    ),
                    "juvenil": (
                        "No reconocí ese producto en la foto che. "
                        "¿Me describís qué es? ¿Marca y modelo?"
                    ),
                    "formal": (
                        "No he podido identificar el producto en la imagen. "
                        "¿Podría describirlo? Marca, modelo, color..."
                    ),
                    "neutral": (
                        "No pude identificar el producto en la imagen. "
                        "¿Puedes describirlo? Marca, modelo, color..."
                    ),
                }
                
                return self._create_response(
                    message=messages.get(style, messages["neutral"]),
                    state=state
                )
                
        except Exception as e:
            logger.error(f"Error procesando imagen: {e}", exc_info=True)
            return self._create_response(
                message="Tuve un problema procesando la imagen. ¿Puedes describir el producto?",
                state=state
            )
        finally:
            await client.close()
    
    async def process(self, state: AgentState) -> AgentResponse:
        """
        Procesa interacciones de venta con LLM con manejo robusto de errores.

        Flujo:
        1. Si hay imagen, procesar con Agente 2 primero
        2. Detecta estilo de usuario (si no está detectado)
        3. Construye system prompt personalizado
        4. Consulta RAG si es necesario para info adicional
        5. Genera respuesta persuasiva con LLM (con timeout y retry)
        6. Detecta si debe transferir a Checkout

        Error Handling:
        - Timeout del LLM (>10s) → Mensaje de disculpa
        - Error de conexión → Fallback gracioso
        - Respuesta vacía → Mensaje genérico
        - Agente 2 no disponible → Mensaje de error amigable
        """
        logger.info(f"SalesAgent procesando: {state.user_query}")
        
        # Si hay una imagen subida, procesarla primero con Agente 2
        if state.uploaded_image is not None:
            return await self._process_image_query(state)

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

        # Extraer y actualizar slots de conversación
        self._update_conversation_slots(state)

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

**REGLA CRÍTICA DE CONCISIÓN:**
- MÁXIMO 40-50 palabras por respuesta
- Móvil/WhatsApp = mensajes cortos
- Una pregunta a la vez, NUNCA 4 preguntas juntas
- Ejemplo CORRECTO (35 palabras): "¡Excelente! ¿Para correr en asfalto o montaña?"
- Ejemplo INCORRECTO (200 palabras): "Excelente elección... [párrafo largo]... ¿Corres en asfalto o pista? ¿Qué distancias? ¿Qué amortiguación?..."

**REGLA ANTI-ALUCINACIÓN:**
- SOLO menciona productos que aparecen en "PRODUCTOS DISPONIBLES"
- NUNCA inventes nombres de modelos
- Si no hay productos en la lista, di "No tengo ese modelo en stock"
- Temperatura = 0 para nombres de productos

**REGLA DE CONTEXTO (Slot Filling):**
- Revisa "INFORMACIÓN YA OBTENIDA" antes de preguntar
- NUNCA pidas talla/modelo/color si ya lo sabes
- Si el usuario ya te dijo algo, úsalo directamente

**REGLA DE SALIDA ELEGANTE (Stop Intent):**
- Si detectas: "mejor no", "chao", "luego veo", "está muy caro gracias"
- Responde: "Entendido, aquí estaré si cambias de opinión. ¡Buen día!"
- NO insistas ni sigas vendiendo

**REGLA DE BESTSELLERS (Fallback):**
- Si el usuario es vago 2 veces, NO preguntes más
- Recomienda los 3 productos más caros de la lista como "bestsellers"
- Ejemplo: "Te recomiendo nuestros top 3: [Modelo A $X], [Modelo B $Y], [Modelo C $Z]"

**REGLA VISUAL:**
- Usa negritas (**) SOLO para precios y nombres de modelos
- NO uses texto narrativo: "(Pausa simulada...)", "(Verificando stock...)"
- Ve directo al grano

**TÉCNICAS DE VENTA:**
1. **Manejo de Objeciones:** Justifica precio en 1 línea (calidad + durabilidad)
2. **Urgencia:** "Solo quedan X" (máximo 5 palabras)
3. **Cierre:** Termina con pregunta de acción corta
4. **Especificaciones:** Máximo 1 línea por característica técnica"""

        # Adaptaciones según estilo
        style_adaptations = {
            "cuencano": """

**ESTILO DE COMUNICACIÓN: CUENCANO**
- Usa modismos: "ve", "full", "chevere", "lindo" (con moderación)
- Reduce "ayayay" - úsalo solo 1 vez por conversación
- Tono cercano pero NO exagerado (menos intensidad emocional)
- Ejemplos cortos:
  * "Estos están de lujo ve. ¿Cuál te gusta?" (10 palabras)
  * "Full buenos, te duran años. ¿Los separamos?" (8 palabras)
  * "Tengo talla 42 en Negro y Azul. ¿Cuál?" (9 palabras)
""",
            "juvenil": """

**ESTILO DE COMUNICACIÓN: JUVENIL**
- Tono casual: "che", "bro", "tipo", "re"
- Sin emojis (a menos que el usuario los use)
- Mantén mensajes ultra cortos
- Ejemplos:
  * "Che, estos son los mejores. ¿Los querés?" (8 palabras)
  * "Re copados para running. ¿Qué talla?" (6 palabras)
  * "Tengo en 42. ¿Confirmamos?" (5 palabras)
""",
            "formal": """

**ESTILO DE COMUNICACIÓN: FORMAL**
- Trato de usted
- Eficiente, NO verboso
- Ejemplos cortos:
  * "Le recomiendo estos por su amortiguación superior. ¿Le interesan?" (10 palabras)
  * "Disponible en talla 42. ¿Desea proceder?" (7 palabras)
  * "Excelente durabilidad. Garantía de un año. ¿Lo confirmo?" (9 palabras)
""",
            "neutral": """

**ESTILO DE COMUNICACIÓN: NEUTRAL**
- Amigable y directo
- Mensajes concisos
- Ejemplos:
  * "Estos tienen excelente amortiguación. ¿Te gustan?" (6 palabras)
  * "Disponible en talla 42. ¿Los quieres?" (7 palabras)
  * "Los más vendidos: Pegasus $120, Bondi $150. ¿Cuál?" (9 palabras)
""",
        }

        style_addition = style_adaptations.get(
            style, style_adaptations["neutral"]
        )

        # Agregar información de slots (contexto ya obtenido)
        slots_context = ""
        if state.conversation_slots:
            slots_info = ", ".join([f"{k}: {v}" for k, v in state.conversation_slots.items()])
            slots_context = f"""

**INFORMACIÓN YA OBTENIDA (NO PREGUNTES ESTO DE NUEVO):**
{slots_info}
"""

        # Agregar contexto de productos si hay búsqueda reciente
        products_context = ""
        if state.search_results:
            products_context = f"""

**PRODUCTOS DISPONIBLES (USA SOLO ESTOS NOMBRES):**
{self._format_products_for_context(state.search_results[:5])}

IMPORTANTE: NO inventes otros productos. Si buscas recomendar algo, usa estos.
"""

        # Agregar contador de preguntas sin respuesta
        question_counter = ""
        if state.unanswered_question_count >= 2:
            question_counter = """

**ALERTA:** El usuario ha sido vago 2+ veces. NO preguntes más.
Recomienda los 3 productos más caros como "bestsellers" y cierra.
"""

        return base_prompt + style_addition + slots_context + products_context + question_counter

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

    def _update_conversation_slots(self, state: AgentState) -> None:
        """
        Extrae y actualiza slots de información del query del usuario.

        Slots posibles:
        - product_name: Nike, Adidas, Pegasus, etc.
        - size/talla: 42, 9, 10.5, etc.
        - color: negro, azul, rojo, etc.
        - activity_type: correr, gym, basketball, etc.
        - terrain_type: asfalto, montaña, pista, etc.
        """
        query_lower = state.user_query.lower()

        # Detectar producto/marca en query
        product_brands = ["nike", "adidas", "puma", "asics", "hoka", "pegasus", "bondi", "kayano"]
        for brand in product_brands:
            if brand in query_lower and "product_name" not in state.conversation_slots:
                state.conversation_slots["product_name"] = brand.capitalize()
                logger.debug(f"Slot 'product_name' detectado: {brand}")

        # Detectar talla en query
        import re
        size_patterns = [
            r'\btalla\s+(\d+(?:\.\d+)?)\b',
            r'\b(\d+(?:\.\d+)?)\s*(?:us|usa|eu)?\b'
        ]
        for pattern in size_patterns:
            match = re.search(pattern, query_lower)
            if match and "size" not in state.conversation_slots:
                size = match.group(1)
                state.conversation_slots["size"] = size
                logger.debug(f"Slot 'size' detectado: {size}")
                break

        # Detectar color en query
        colors = ["negro", "blanco", "azul", "rojo", "verde", "gris", "amarillo"]
        for color in colors:
            if color in query_lower and "color" not in state.conversation_slots:
                state.conversation_slots["color"] = color
                logger.debug(f"Slot 'color' detectado: {color}")
                break

        # Detectar actividad
        activities = {
            "correr": ["correr", "running", "run", "carrera"],
            "gym": ["gym", "gimnasio", "entrenar", "entrenamiento"],
            "basketball": ["basket", "basketball", "baloncesto"],
        }
        for activity_name, keywords in activities.items():
            if any(kw in query_lower for kw in keywords) and "activity_type" not in state.conversation_slots:
                state.conversation_slots["activity_type"] = activity_name
                logger.debug(f"Slot 'activity_type' detectado: {activity_name}")
                break

        # Detectar si el usuario respondió con información adicional a una pregunta del asistente
        # Si la respuesta del usuario es muy corta (<10 palabras) y no contiene slots,
        # incrementar contador de respuestas vagas
        if len(state.user_query.split()) < 10 and not any([
            "product_name" in state.conversation_slots,
            "size" in state.conversation_slots,
            "activity_type" in state.conversation_slots
        ]):
            # Solo incrementar si el último mensaje del asistente fue una pregunta
            if state.conversation_history:
                last_assistant = [m for m in state.conversation_history if m["role"] == "assistant"]
                if last_assistant and "?" in last_assistant[-1]["content"]:
                    state.unanswered_question_count += 1
                    logger.debug(f"Contador de respuestas vagas: {state.unanswered_question_count}")
        else:
            # Resetear contador si el usuario dio información útil
            if state.unanswered_question_count > 0:
                state.unanswered_question_count = 0
                logger.debug("Contador de respuestas vagas reseteado")
