"""
Agente Buscador - Recuperación rápida de productos mediante SQL.
"""
from typing import List, Any
from loguru import logger

from backend.agents.base import BaseAgent
from backend.domain.agent_schemas import AgentState, AgentResponse
from backend.services.product_service import ProductService
from backend.services.rag_service import RAGService


class RetrieverAgent(BaseAgent):
    """
    Agente especializado en búsqueda rápida de productos.

    Responsabilidades:
    - Búsqueda SQL directa en inventario
    - Recuperación de candidatos de productos
    - Filtrado básico por disponibilidad
    - NO usa LLM (solo lógica y SQL)
    """

    def __init__(
        self, product_service: ProductService, rag_service: RAGService
    ):
        super().__init__(agent_name="retriever")
        self.product_service = product_service
        self.rag_service = rag_service

    def can_handle(self, state: AgentState) -> bool:
        """
        El RetrieverAgent maneja:
        - Consultas de búsqueda de productos
        - Preguntas sobre catálogo
        - Solicitudes de información de inventario
        """
        if state.detected_intent == "search":
            return True

        # Palabras clave que indican búsqueda
        search_keywords = [
            "buscar",
            "mostrar",
            "quiero ver",
            "tienes",
            "hay",
            "talla",
            "color",
            "marca",
            "precio",
            "catálogo",
            "modelos",
        ]

        query_lower = state.user_query.lower()
        return any(keyword in query_lower for keyword in search_keywords)

    async def process(self, state: AgentState) -> AgentResponse:
        """
        Procesa búsquedas de productos con manejo robusto de errores.

        Flujo:
        1. Extrae términos de búsqueda del query
        2. Busca en la BD usando ProductService (con error handling)
        3. Filtra resultados por disponibilidad
        4. Retorna candidatos al orquestador

        Error Handling:
        - Error de BD → Mensaje amigable
        - Timeout de BD → Mensaje de disculpa
        - Sin términos de búsqueda → Mensaje de ayuda
        """
        logger.info(f"RetrieverAgent procesando: {state.user_query}")

        try:
            # Extraer términos de búsqueda (palabras significativas)
            search_terms = self._extract_search_terms(state.user_query)
            logger.debug(f"Términos de búsqueda extraídos: {search_terms}")

            # Validar que hay términos
            if not search_terms:
                logger.warning("No se pudieron extraer términos de búsqueda")
                message = self._get_no_terms_message(state)
                return self._create_response(
                    message=message,
                    state=state,
                    should_transfer=True,
                    transfer_to="sales",
                    error="no_search_terms",
                )

            # Buscar productos con error handling
            products = []
            search_errors = []

            for term in search_terms:
                try:
                    found = await self.product_service.search_by_name(term)
                    products.extend(found)
                except Exception as e:
                    logger.error(
                        f"Error buscando término '{term}': {str(e)}",
                        exc_info=True
                    )
                    search_errors.append(term)
                    continue

            # Si todas las búsquedas fallaron
            if search_errors and not products:
                logger.error(
                    f"Todas las búsquedas fallaron: {search_errors}"
                )
                message = self._get_db_error_message(state)
                return self._create_response(
                    message=message,
                    state=state,
                    should_transfer=True,
                    transfer_to="sales",
                    error="database_error",
                )

            # Eliminar duplicados y filtrar por disponibilidad
            unique_products = self._deduplicate_products(products)
            available_products = [
                p for p in unique_products if p.quantity_available > 0
            ]

            logger.info(
                f"Productos encontrados: {len(available_products)} "
                f"(errores en {len(search_errors)} términos)"
            )

        except Exception as e:
            # Error inesperado en el proceso
            logger.error(
                f"Error inesperado en RetrieverAgent: {str(e)}",
                exc_info=True
            )
            message = self._get_unexpected_error_message(state)
            return self._create_response(
                message=message,
                state=state,
                should_transfer=True,
                transfer_to="sales",
                error="unexpected_error",
            )

        # Actualizar estado (siempre, incluso con búsqueda parcial)
        try:
            state.search_results = [
                {
                    "id": str(p.id),
                    "name": p.product_name,
                    "price": float(p.unit_cost),
                    "stock": p.quantity_available,
                    "sku": p.product_sku,
                    "location": p.warehouse_location,
                }
                for p in available_products
            ]
            state.detected_intent = "search"
        except Exception as e:
            logger.error(f"Error serializando productos: {str(e)}")
            # Continuar con lista vacía
            state.search_results = []

        # Crear mensaje de respuesta
        if not available_products:
            message = self._format_no_results_message(state)

            # Advertir si hubo errores de búsqueda
            if search_errors:
                message += f"\n\n_Nota: Algunos términos no pudieron buscarse._"

            # Transferir a SalesAgent para ofrecer alternativas
            return self._create_response(
                message=message,
                state=state,
                should_transfer=True,
                transfer_to="sales",
                products_found=0,
                partial_errors=len(search_errors),
            )

        # Formatear resultados
        try:
            message = self._format_search_results(available_products, state)

            # Advertir si hubo errores parciales
            if search_errors:
                message += f"\n\n_Nota: Algunos resultados pueden estar incompletos._"

        except Exception as e:
            logger.error(f"Error formateando resultados: {str(e)}")
            message = self._get_format_error_message(state, len(available_products))

        # Si hay pocos resultados (<=5), transferir a Sales para persuasión
        should_transfer = len(available_products) <= 5
        transfer_to = "sales" if should_transfer else None

        return self._create_response(
            message=message,
            state=state,
            should_transfer=should_transfer,
            transfer_to=transfer_to,
            products_found=len(available_products),
            partial_errors=len(search_errors),
        )

    def _get_no_terms_message(self, state: AgentState) -> str:
        """Mensaje cuando no se pueden extraer términos de búsqueda."""
        style = state.user_style or "neutral"

        messages = {
            "cuencano": (
                "Ayayay, no entendí bien qué estás buscando ve. "
                "¿Me dices qué marca o tipo de zapato quieres?"
            ),
            "juvenil": (
                "Che, no me quedó claro qué buscás. "
                "¿Qué tipo de zapatillas querés?"
            ),
            "formal": (
                "Disculpe, no logré identificar su búsqueda. "
                "¿Podría especificar qué tipo de calzado busca?"
            ),
            "neutral": (
                "No pude identificar qué buscas. "
                "¿Podrías especificar marca o tipo de zapato?"
            ),
        }

        return messages.get(style, messages["neutral"])

    def _get_db_error_message(self, state: AgentState) -> str:
        """Mensaje cuando la base de datos falla."""
        style = state.user_style or "neutral"

        messages = {
            "cuencano": (
                "Ayayay, tuve un problemita con la búsqueda ve. "
                "¿Intentamos de nuevo en un ratito?"
            ),
            "juvenil": (
                "Uh, hubo un error con la búsqueda bro. "
                "¿Probamos de nuevo?"
            ),
            "formal": (
                "Lamento informarle que hubo un problema técnico con la búsqueda. "
                "¿Podría intentar nuevamente?"
            ),
            "neutral": (
                "Hubo un problema con la búsqueda. "
                "¿Puedes intentar de nuevo?"
            ),
        }

        return messages.get(style, messages["neutral"])

    def _get_unexpected_error_message(self, state: AgentState) -> str:
        """Mensaje para errores inesperados."""
        style = state.user_style or "neutral"

        messages = {
            "cuencano": (
                "Ayayay, algo salió mal ve. "
                "¿Puedo ayudarte con otra cosa?"
            ),
            "juvenil": (
                "Uh, hubo un error inesperado bro. "
                "¿Te ayudo con algo más?"
            ),
            "formal": (
                "Disculpe, ha ocurrido un error inesperado. "
                "¿Puedo asistirle con algo más?"
            ),
            "neutral": (
                "Ocurrió un error inesperado. "
                "¿Puedo ayudarte con algo más?"
            ),
        }

        return messages.get(style, messages["neutral"])

    def _get_format_error_message(self, state: AgentState, product_count: int) -> str:
        """Mensaje cuando falla el formateo de resultados."""
        style = state.user_style or "neutral"

        messages = {
            "cuencano": (
                f"Ayayay, encontré {product_count} productos ve, "
                f"pero tuve un problemita mostrándolos. ¿Me dices cuál te interesa?"
            ),
            "juvenil": (
                f"Che, tengo {product_count} productos pero hubo un error mostrándolos. "
                f"¿Cuál querés ver?"
            ),
            "formal": (
                f"Disculpe, encontré {product_count} productos pero hubo un error "
                f"al mostrarlos. ¿Podría especificar cuál le interesa?"
            ),
            "neutral": (
                f"Encontré {product_count} productos pero hubo un error mostrándolos. "
                f"¿Cuál te interesa?"
            ),
        }

        return messages.get(style, messages["neutral"])

    def _extract_search_terms(self, query: str) -> List[str]:
        """
        Extrae términos significativos de búsqueda.
        Filtra stopwords y palabras cortas.
        """
        stopwords = {
            "el",
            "la",
            "de",
            "que",
            "y",
            "un",
            "una",
            "en",
            "a",
            "los",
            "las",
            "del",
            "por",
            "para",
            "con",
            "me",
            "mi",
            "tu",
            "hay",
            "tiene",
            "tienes",
            "quiero",
            "busco",
            "mostrar",
            "ver",
        }

        words = query.lower().split()
        significant_words = [
            word
            for word in words
            if len(word) > 2 and word not in stopwords
        ]

        # Si no hay palabras significativas, usar todas
        return significant_words if significant_words else [query]

    def _deduplicate_products(
        self, products: List[Any]
    ) -> List[Any]:
        """Elimina productos duplicados basándose en ID."""
        seen = set()
        unique = []
        for product in products:
            if product.id not in seen:
                seen.add(product.id)
                unique.append(product)
        return unique

    def _format_search_results(
        self, products: List[Any], state: AgentState
    ) -> str:
        """
        Formatea los resultados de búsqueda en un mensaje legible.
        Adapta el tono según el estilo del usuario.
        """
        style = state.user_style or "neutral"

        # Adaptar saludo según estilo
        greetings = {
            "cuencano": "Ayayay, mirá lo que tengo para vos:",
            "juvenil": "¡Che, mira lo que encontré!",
            "formal": "He encontrado los siguientes productos:",
            "neutral": "Encontré estos productos:",
        }

        greeting = greetings.get(style, greetings["neutral"])
        lines = [greeting, ""]

        for idx, product in enumerate(products[:10], 1):  # Max 10 resultados
            price = f"${product.unit_cost:,.2f}"
            stock_msg = (
                f"✅ {product.quantity_available} disponibles"
                if product.quantity_available > 5
                else f"⚠️ ¡Solo quedan {product.quantity_available}!"
            )

            lines.append(
                f"{idx}. **{product.product_name}** - {price} ({stock_msg})"
            )

        if len(products) > 10:
            lines.append(f"\n_...y {len(products) - 10} productos más_")

        return "\n".join(lines)

    def _format_no_results_message(self, state: AgentState) -> str:
        """Mensaje cuando no hay resultados."""
        style = state.user_style or "neutral"

        messages = {
            "cuencano": f"Ayayay, no tengo nada de '{state.user_query}' ahorita. ¿Buscamos otra cosa?",
            "juvenil": f"Uh, no tengo '{state.user_query}' en stock. ¿Algo más que te interese?",
            "formal": f"Lo siento, no encontré resultados para '{state.user_query}'. ¿Puedo ayudarle con otra búsqueda?",
            "neutral": f"No encontré productos para '{state.user_query}'. ¿Quieres buscar algo diferente?",
        }

        return messages.get(style, messages["neutral"])
