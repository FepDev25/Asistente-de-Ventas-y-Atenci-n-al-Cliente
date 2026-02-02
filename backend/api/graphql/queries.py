"""
Consultas GraphQL (Endpoints).
Aquí el Frontend pide cosas al Backend.
"""
import asyncio
from typing import Annotated
from uuid import UUID
import strawberry
from aioinject import Inject
from aioinject.ext.strawberry import inject
from loguru import logger

from backend.api.graphql.types import ProductStockType, SemanticSearchResponse
from backend.services.product_service import ProductService
from backend.services.search_service import SearchService

@strawberry.type
class BusinessQuery:
    """Raíz de todas las consultas."""

    @strawberry.field
    @inject
    async def list_products(
        self,
        product_service: Annotated[ProductService, Inject],
        limit: int = 20
    ) -> list[ProductStockType]:
        """
        Catálogo clásico: Devuelve lista de zapatos con manejo de errores.

        Query: { listProducts(limit: 10) { productName unitCost } }

        Error Handling:
        - Timeout de BD → Lista vacía con log
        - BD caída → Lista vacía con log
        - Error general → Lista vacía

        Returns:
            Lista de productos (vacía en caso de error)
        """
        logger.info(f"GraphQL: Listando {limit} productos")

        try:
            # Usamos servicio limpio de ProductService
            products = await product_service.search_by_name("")

            if not products:
                logger.warning("No se encontraron productos en BD")
                return []

            return [
                ProductStockType(
                    id=p.id,
                    product_name=p.product_name,
                    unit_cost=p.unit_cost,
                    quantity_available=p.quantity_available,
                    stock_status=p.stock_status,
                    warehouse_location=p.warehouse_location,
                    shelf_location=p.shelf_location,
                    batch_number=p.batch_number
                )
                for p in products[:limit]
            ]

        except Exception as e:
            logger.error(
                f"Error en list_products: {str(e)}",
                exc_info=True
            )
            # Retornar lista vacía en lugar de crash
            return []

    @strawberry.field
    @inject
    async def semantic_search(
        self,
        query: str,
        search_service: Annotated[SearchService, Inject],
        session_id: str | None = None
    ) -> SemanticSearchResponse:
        """
        Chat con Alex: El usuario pregunta, la IA responde con manejo robusto de errores.

        Query: { semanticSearch(query: "Quiero Nike baratos", sessionId: "user123") { answer error } }

        Args:
            query: Consulta del usuario
            session_id: ID de sesión para mantener contexto (opcional)

        Error Handling:
        - Timeout (>30s) → Mensaje de reintentar (error="timeout")
        - Servicio no disponible → Mensaje amigable (error="service_unavailable")
        - Error general → Mensaje técnico (error="internal_error")

        Returns:
            SemanticSearchResponse con answer (siempre) y error (opcional)
        """
        logger.info(f"GraphQL: Chat con Alex -> '{query}' (session: {session_id})")

        try:
            # Llamamos a SearchService con timeout
            result = await asyncio.wait_for(
                search_service.semantic_search(query, session_id=session_id),
                timeout=30.0  # 30 segundos máximo
            )

            return SemanticSearchResponse(
                answer=result.answer,
                query=query,
                error=None  # Sin error
            )

        except asyncio.TimeoutError:
            logger.error(
                f"⏱️ Timeout procesando query (>30s): '{query[:50]}...'",
                exc_info=False
            )
            return SemanticSearchResponse(
                answer=(
                    "Lo siento, estoy teniendo problemas para responder. "
                    "¿Puedes intentar de nuevo? Si el problema persiste, "
                    "intenta hacer una pregunta más simple."
                ),
                query=query,
                error="timeout"
            )

        except ConnectionError as e:
            logger.error(
                f"🚨 Servicio no disponible para query '{query[:50]}...': {str(e)}",
                exc_info=True
            )
            return SemanticSearchResponse(
                answer=(
                    "Disculpa, el servicio no está disponible en este momento. "
                    "Por favor intenta nuevamente en unos minutos."
                ),
                query=query,
                error="service_unavailable"
            )

        except Exception as e:
            logger.error(
                f"💥 Error inesperado en semantic_search: '{query[:50]}...': {str(e)}",
                exc_info=True
            )
            return SemanticSearchResponse(
                answer=(
                    "Disculpa, tuve un problema técnico. "
                    "Nuestro equipo ha sido notificado. "
                    "Por favor intenta nuevamente."
                ),
                query=query,
                error="internal_error"
            )