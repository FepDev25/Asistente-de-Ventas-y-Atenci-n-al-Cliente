"""
Agente Cajero - Confirmación y cierre de pedidos (lógica dura).
"""
from typing import Optional
from loguru import logger

from backend.agents.base import BaseAgent
from backend.domain.agent_schemas import AgentState, AgentResponse
from backend.services.product_service import ProductService

# Agente Cajero - Procesa confirmaciones y cierra transacciones.
    # - Validar productos seleccionados
    # - Confirmar dirección de envío
    # - Procesar pedido en la BD
    # - Validar stock en tiempo real
    # - NO usa LLM (solo lógica transaccional)
class CheckoutAgent(BaseAgent):


    def __init__(self, product_service: ProductService):
        super().__init__(agent_name="checkout")
        self.product_service = product_service

    def can_handle(self, state: AgentState) -> bool:
        """
        El CheckoutAgent maneja:
        - Confirmaciones de compra
        - Procesamiento de pedidos
        - Validación de dirección
        """
        if state.detected_intent == "checkout":
            return True

        # Si está en etapa de checkout
        if state.checkout_stage is not None:
            return True

        # Palabras de confirmación directa
        checkout_keywords = [
            "confirmar",
            "comprar ahora",
            "proceder",
            "finalizar",
            "pagar",
        ]

        query_lower = state.user_query.lower()
        return any(keyword in query_lower for keyword in checkout_keywords)

    async def process(self, state: AgentState) -> AgentResponse:
        """
        Procesa el flujo de checkout con manejo robusto de errores.

        Flujo:
        1. Identificar producto a comprar (del contexto o query)
        2. Validar stock disponible
        3. Solicitar confirmación de dirección
        4. Procesar pedido (con transacción)
        5. Generar confirmación

        Error Handling:
        - Producto no encontrado → Mensaje claro + volver a Sales
        - Stock insuficiente → Sugerir cantidad disponible
        - Error de BD → Rollback automático + mensaje
        - Estado inválido → Reset seguro
        """
        logger.info(
            f"CheckoutAgent procesando: {state.user_query} "
            f"(stage: {state.checkout_stage})"
        )

        try:
            # Determinar etapa del checkout
            if state.checkout_stage is None:
                # Iniciar checkout
                return await self._initiate_checkout(state)
            elif state.checkout_stage == "confirm":
                # Confirmar producto
                return await self._confirm_product(state)
            elif state.checkout_stage == "address":
                # Procesar dirección
                return await self._process_address(state)
            elif state.checkout_stage == "payment":
                # Procesar pago
                return await self._process_payment(state)
            else:
                # Estado desconocido, reiniciar con warning
                logger.warning(
                    f"Estado de checkout desconocido: {state.checkout_stage}"
                )
                state.checkout_stage = None
                return await self._initiate_checkout(state)

        except Exception as e:
            # Error crítico en checkout - limpiar estado y notificar
            logger.error(
                f"Error crítico en CheckoutAgent: {str(e)}",
                exc_info=True
            )

            # Limpiar estado de checkout
            state.checkout_stage = None
            state.selected_products = []
            state.cart_items = []

            message = self._get_critical_error_message(state, e)

            return self._create_response(
                message=message,
                state=state,
                should_transfer=True,
                transfer_to="sales",
                error="critical_checkout_error",
            )

    async def _initiate_checkout(
        self, state: AgentState
    ) -> AgentResponse:
        """Inicia el proceso de checkout."""
        # Extraer producto del contexto
        product_info = self._extract_product_from_context(state)

        if not product_info:
            # No hay producto claro, pedir aclaración
            message = self._format_clarification_message(state)
            return self._create_response(
                message=message,
                state=state,
                should_transfer=True,
                transfer_to="sales",
                error="no_product_identified",
            )

        # Validar stock
        product_name = product_info["name"]
        quantity = product_info.get("quantity", 1)

        # Buscar producto en BD
        products = await self.product_service.search_by_name(product_name)

        if not products:
            message = f"Lo siento, no pude encontrar '{product_name}' en el sistema. ¿Quieres buscar otro producto?"
            return self._create_response(
                message=message,
                state=state,
                should_transfer=True,
                transfer_to="retriever",
                error="product_not_found",
            )

        product = products[0]  # Tomar el primero

        # Validar stock
        if product.quantity_available < quantity:
            message = self._format_insufficient_stock_message(
                product, quantity, state
            )
            return self._create_response(
                message=message,
                state=state,
                should_transfer=True,
                transfer_to="sales",
                error="insufficient_stock",
            )

        # Stock OK, solicitar confirmación
        state.selected_products = [
            {
                "id": str(product.id),
                "name": product.product_name,
                "price": float(product.unit_cost),
                "quantity": quantity,
                "subtotal": float(product.unit_cost) * quantity,
            }
        ]
        state.cart_total = float(product.unit_cost) * quantity
        state.checkout_stage = "confirm"

        message = self._format_confirmation_request(product, quantity, state)

        return self._create_response(
            message=message, state=state, should_transfer=False
        )

    async def _confirm_product(self, state: AgentState) -> AgentResponse:
        """Confirma el producto y solicita dirección."""
        query_lower = state.user_query.lower().strip()

        # Verificar confirmación
        affirmative = ["sí", "si", "ok", "dale", "bueno", "confirmo", "ya"]
        negative = ["no", "cancela", "mejor no", "espera"]

        if any(word in query_lower for word in negative):
            # Cancelar
            state.checkout_stage = None
            state.selected_products = []
            message = self._format_cancellation_message(state)
            return self._create_response(
                message=message,
                state=state,
                should_transfer=True,
                transfer_to="sales",
                cancelled=True,
            )

        if any(word in query_lower for word in affirmative):
            # Continuar a dirección
            state.checkout_stage = "address"
            message = self._format_address_request(state)
            return self._create_response(
                message=message, state=state, should_transfer=False
            )

        # No está claro, pedir confirmación nuevamente
        message = "No entendí. ¿Confirmas el pedido? (Responde sí o no)"
        return self._create_response(
            message=message, state=state, should_transfer=False
        )

    async def _process_address(self, state: AgentState) -> AgentResponse:
        """Procesa la dirección de envío."""
        # Por ahora, aceptar cualquier dirección
        # TODO: Validar formato de dirección
        address = state.user_query.strip()

        if len(address) < 10:
            # Dirección muy corta, pedir más detalles
            message = "La dirección parece incompleta. Por favor incluye calle, número y ciudad."
            return self._create_response(
                message=message, state=state, should_transfer=False
            )

        state.shipping_address = address
        state.checkout_stage = "payment"

        # Procesar el pedido
        return await self._process_payment(state)

    async def _process_payment(self, state: AgentState) -> AgentResponse:
        """
        Procesa el pago y finaliza el pedido con validaciones robustas.

        Error Handling:
        - Valida productos seleccionados
        - Verifica stock antes de procesar
        - Maneja errores de BD individualmente
        - Rollback automático en caso de fallo
        """
        # Validación 1: Hay productos seleccionados?
        if not state.selected_products:
            logger.error("Intento de checkout sin productos seleccionados")
            message = self._get_no_products_error(state)
            state.checkout_stage = None
            return self._create_response(
                message=message,
                state=state,
                should_transfer=True,
                transfer_to="sales",
                error="no_products",
            )

        # Validación 2: Hay dirección de envío?
        if not state.shipping_address:
            logger.warning("Checkout sin dirección de envío")
            state.checkout_stage = "address"
            message = self._format_address_request(state)
            return self._create_response(
                message=message,
                state=state,
                should_transfer=False,
                error="missing_address",
            )

        logger.info(
            f"Procesando {len(state.selected_products)} producto(s) "
            f"para envío a: {state.shipping_address}"
        )

        # Procesar cada producto con error handling
        success_items = []
        failed_items = []

        for item in state.selected_products:
            try:
                logger.debug(
                    f"Procesando item: {item['name']} x{item['quantity']}"
                )

                # Validar que el item tenga datos necesarios
                if not item.get("name") or not item.get("quantity"):
                    logger.error(f"Item inválido: {item}")
                    failed_items.append({
                        "item": item,
                        "error": "Datos de producto incompletos"
                    })
                    continue

                # Procesar orden en BD
                result = await self.product_service.process_order(
                    product_name=item["name"],
                    quantity=item["quantity"]
                )

                if result.get("success"):
                    success_items.append(item)
                    logger.info(
                        f"✓ Pedido procesado: {item['name']} x{item['quantity']}"
                    )
                else:
                    error_msg = result.get("error", "Error desconocido")
                    failed_items.append({
                        "item": item,
                        "error": error_msg
                    })
                    logger.warning(
                        f"✗ Pedido fallido: {item['name']} - {error_msg}"
                    )

            except ValueError as e:
                # Error de validación (ej: stock insuficiente)
                logger.warning(
                    f"Validación fallida para {item['name']}: {str(e)}"
                )
                failed_items.append({
                    "item": item,
                    "error": f"Validación: {str(e)}"
                })

            except Exception as e:
                # Error inesperado de BD u otro
                logger.error(
                    f"Error inesperado procesando {item['name']}: {str(e)}",
                    exc_info=True
                )
                failed_items.append({
                    "item": item,
                    "error": "Error de sistema"
                })

        # Generar mensaje final basado en resultados
        if success_items:
            message = self._format_order_confirmation(
                success_items, failed_items, state
            )
        elif failed_items:
            # Todos los items fallaron
            message = self._format_all_failed_message(failed_items, state)
        else:
            # Caso edge: sin éxitos ni fallos (no debería pasar)
            logger.error("Checkout completado sin resultados")
            message = self._get_unexpected_checkout_error(state)

        # Limpiar estado de checkout (siempre, incluso si hay fallos)
        state.checkout_stage = "complete"
        state.selected_products = []
        state.cart_items = []

        # Si hubo algún éxito, no transferir
        # Si todo falló, transferir a Sales para ayudar
        should_transfer = len(success_items) == 0
        transfer_to = "sales" if should_transfer else None

        return self._create_response(
            message=message,
            state=state,
            should_transfer=should_transfer,
            transfer_to=transfer_to,
            success_count=len(success_items),
            failed_count=len(failed_items),
        )

    def _get_no_products_error(self, state: AgentState) -> str:
        """Mensaje cuando no hay productos para checkout."""
        style = state.user_style or "neutral"

        messages = {
            "cuencano": (
                "Ayayay, no veo ningún producto para comprar ve. "
                "¿Buscamos algo primero?"
            ),
            "juvenil": (
                "Che, no hay productos en el carrito bro. "
                "¿Buscamos algo?"
            ),
            "formal": (
                "Disculpe, no hay productos seleccionados para procesar. "
                "¿Desea realizar una búsqueda?"
            ),
            "neutral": (
                "No hay productos seleccionados. "
                "¿Quieres buscar algo primero?"
            ),
        }

        return messages.get(style, messages["neutral"])

    def _get_critical_error_message(self, state: AgentState, error: Exception) -> str:
        """Mensaje para errores críticos en checkout."""
        style = state.user_style or "neutral"
        error_type = type(error).__name__

        logger.debug(f"Error crítico tipo: {error_type}")

        messages = {
            "cuencano": (
                "Ayayay, tuve un problema grave con el pedido ve. "
                "Lo siento mucho. ¿Intentamos de nuevo o buscas otra cosa?"
            ),
            "juvenil": (
                "Uh, hubo un error grave en el pedido bro. "
                "Perdón. ¿Probamos de nuevo?"
            ),
            "formal": (
                "Lamento informarle que ha ocurrido un error crítico al procesar su pedido. "
                "¿Desea intentar nuevamente?"
            ),
            "neutral": (
                "Hubo un error crítico procesando el pedido. "
                "Lo siento. ¿Quieres intentar de nuevo?"
            ),
        }

        return messages.get(style, messages["neutral"])

    def _get_unexpected_checkout_error(self, state: AgentState) -> str:
        """Mensaje para situaciones inesperadas en checkout."""
        style = state.user_style or "neutral"

        messages = {
            "cuencano": (
                "Ayayay, algo raro pasó con el pedido ve. "
                "¿Intentamos de nuevo?"
            ),
            "juvenil": (
                "Che, pasó algo raro con el pedido. "
                "¿Probamos otra vez?"
            ),
            "formal": (
                "Disculpe, ocurrió una situación inesperada. "
                "¿Desea intentar nuevamente?"
            ),
            "neutral": (
                "Ocurrió algo inesperado con el pedido. "
                "¿Intentamos de nuevo?"
            ),
        }

        return messages.get(style, messages["neutral"])

    def _format_all_failed_message(self, failed_items, state: AgentState) -> str:
        """Mensaje cuando todos los items del checkout fallaron."""
        style = state.user_style or "neutral"

        # Construir lista de errores
        error_details = []
        for failure in failed_items[:3]:  # Max 3 para no saturar
            item_name = failure["item"].get("name", "Producto")
            error = failure.get("error", "Error desconocido")
            error_details.append(f"- {item_name}: {error}")

        errors_text = "\n".join(error_details)

        if style == "cuencano":
            message = (
                f"Ayayay, ningún producto pudo procesarse ve. "
                f"Estos fueron los problemas:\n\n{errors_text}\n\n"
                f"¿Buscamos otra cosa o intentamos de nuevo?"
            )
        elif style == "juvenil":
            message = (
                f"Uh bro, ningún producto se pudo procesar. "
                f"Los problemas fueron:\n\n{errors_text}\n\n"
                f"¿Probamos de nuevo?"
            )
        elif style == "formal":
            message = (
                f"Lamento informarle que ningún producto pudo procesarse. "
                f"Detalles:\n\n{errors_text}\n\n"
                f"¿Desea intentar nuevamente?"
            )
        else:
            message = (
                f"No se pudo procesar ningún producto. "
                f"Errores:\n\n{errors_text}\n\n"
                f"¿Quieres intentar de nuevo?"
            )

        return message

    def _extract_product_from_context(
        self, state: AgentState
    ) -> Optional[dict]:
        """
        Extrae información del producto a comprar del contexto.
        """
        # Opción 1: Hay un solo resultado de búsqueda
        if (
            state.search_results
            and len(state.search_results) == 1
        ):
            return {
                "name": state.search_results[0]["name"],
                "quantity": 1,
            }

        # Opción 2: Usuario mencionó producto en el mensaje
        # Buscar en los últimos resultados de búsqueda
        if state.search_results:
            query_lower = state.user_query.lower()
            for result in state.search_results:
                # Buscar menciones del nombre del producto
                product_name_lower = result["name"].lower()
                # Extraer palabras clave del nombre
                product_keywords = [
                    word
                    for word in product_name_lower.split()
                    if len(word) > 3
                ]

                if any(keyword in query_lower for keyword in product_keywords):
                    return {"name": result["name"], "quantity": 1}

        # Opción 3: Tomar el primer resultado si hay búsqueda reciente
        if state.search_results and len(state.search_results) <= 3:
            return {
                "name": state.search_results[0]["name"],
                "quantity": 1,
            }

        return None

    def _format_confirmation_request(
        self, product, quantity: int, state: AgentState
    ) -> str:
        """Formatea mensaje de confirmación."""
        style = state.user_style or "neutral"

        total = float(product.unit_cost) * quantity
        product_line = f"**{product.product_name}** - ${product.unit_cost:,.2f}"
        if quantity > 1:
            product_line += f" x {quantity} = ${total:,.2f}"

        messages = {
            "cuencano": f"Ayayay, perfecto! Confirmame este pedido:\n\n{product_line}\n\n¿Está bien ve?",
            "juvenil": f"Dale! Vamos a confirmar:\n\n{product_line}\n\n¿Todo ok?",
            "formal": f"Muy bien, por favor confirme su pedido:\n\n{product_line}\n\n¿Desea proceder?",
            "neutral": f"Perfecto, confirmemos el pedido:\n\n{product_line}\n\n¿Está correcto?",
        }

        return messages.get(style, messages["neutral"])

    def _format_address_request(self, state: AgentState) -> str:
        """Formatea solicitud de dirección."""
        style = state.user_style or "neutral"

        messages = {
            "cuencano": "Chevere! ¿A qué dirección te lo mando ve?",
            "juvenil": "Genial! ¿Cuál es tu dirección de envío?",
            "formal": "Excelente. ¿Podría proporcionarme su dirección de envío?",
            "neutral": "Perfecto. ¿Cuál es tu dirección de envío?",
        }

        return messages.get(style, messages["neutral"])

    def _format_order_confirmation(
        self, success_items, failed_items, state: AgentState
    ) -> str:
        """Formatea confirmación final del pedido."""
        style = state.user_style or "neutral"

        if not success_items:
            return "Lo siento, no se pudo procesar ningún artículo. Por favor intenta nuevamente."

        lines = []

        # Encabezado según estilo
        headers = {
            "cuencano": "¡Ayayay, listo ve! Pedido confirmado:",
            "juvenil": "¡Listo bro! Tu pedido está confirmado:",
            "formal": "Pedido procesado exitosamente:",
            "neutral": "¡Pedido confirmado!",
        }
        lines.append(headers.get(style, headers["neutral"]))
        lines.append("")

        # Listar productos exitosos
        for item in success_items:
            lines.append(
                f"{item['name']} x{item['quantity']} - ${item['subtotal']:,.2f}"
            )

        # Total
        total = sum(item["subtotal"] for item in success_items)
        lines.append(f"\n**Total: ${total:,.2f}**")

        # Dirección
        if state.shipping_address:
            lines.append(f"\nEnvío a: {state.shipping_address}")

        # Mensaje de cierre
        closings = {
            "cuencano": "\n¡Gracias por tu compra ve! Te llega en 2-3 días.",
            "juvenil": "\n¡Gracias por tu compra! Te llega pronto.",
            "formal": "\n\nGracias por su compra.Recibirá su pedido en 2-3 días hábiles.",
            "neutral": "\n¡Gracias por tu compra! Recibirás tu pedido pronto.",
        }
        lines.append(closings.get(style, closings["neutral"]))

        # Advertir sobre items fallidos si los hay
        if failed_items:
            lines.append(
                f"\nNota: {len(failed_items)} artículo(s) no pudieron procesarse."
            )

        return "\n".join(lines)

    def _format_insufficient_stock_message(
        self, product, requested_qty: int, state: AgentState
    ) -> str:
        """Mensaje cuando no hay suficiente stock."""
        style = state.user_style or "neutral"
        available = product.quantity_available

        messages = {
            "cuencano": f"Ayayay, solo me quedan {available} de {product.product_name}. ¿Igual los quieres ve?",
            "juvenil": f"Uh, solo quedan {available} unidades de {product.product_name}. ¿Los llevas?",
            "formal": f"Lo siento, solo tenemos {available} unidades disponibles de {product.product_name}. ¿Desea ajustar la cantidad?",
            "neutral": f"Solo tenemos {available} unidades de {product.product_name} disponibles. ¿Quieres ajustar la cantidad?",
        }

        return messages.get(style, messages["neutral"])

    def _format_clarification_message(self, state: AgentState) -> str:
        """Mensaje cuando no está claro qué comprar."""
        style = state.user_style or "neutral"

        messages = {
            "cuencano": "Ayayay, no entendí qué producto quieres comprar ve. ¿Me dices cuál?",
            "juvenil": "No me quedó claro qué producto querías. ¿Cuál te interesa?",
            "formal": "Disculpe, no logré identificar el producto que desea adquirir. ¿Podría especificarlo?",
            "neutral": "No identifiqué qué producto quieres comprar. ¿Puedes especificar?",
        }

        return messages.get(style, messages["neutral"])

    def _format_cancellation_message(self, state: AgentState) -> str:
        """Mensaje de cancelación."""
        style = state.user_style or "neutral"

        messages = {
            "cuencano": "No hay problema ve! ¿Buscamos otra cosa?",
            "juvenil": "Dale, sin drama. ¿Algo más que te interese?",
            "formal": "Entendido. ¿Puedo ayudarle con algo más?",
            "neutral": "Ok, pedido cancelado. ¿Necesitas algo más?",
        }

        return messages.get(style, messages["neutral"])
