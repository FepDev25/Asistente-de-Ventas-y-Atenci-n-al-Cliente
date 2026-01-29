"""
Consultas GraphQL (Endpoints).
Aquí el Frontend pide cosas al Backend.
"""
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
        Catálogo clásico: Devuelve lista de zapatos.
        Query: { listProducts(limit: 10) { productName unitCost } }
        """
        logger.info(f"GraphQL: Listando {limit} productos")
        
        # Usamos servicio limpio de ProductService
        products = await product_service.search_by_name("") 
        
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

    @strawberry.field
    @inject
    async def semantic_search(
        self,
        query: str,
        search_service: Annotated[SearchService, Inject],
        session_id: str | None = None
    ) -> SemanticSearchResponse:
        """
        Chat con Alex: El usuario pregunta, la IA responde.
        Query: { semanticSearch(query: "Quiero Nike baratos", sessionId: "user123") { answer } }

        Args:
            query: Consulta del usuario
            session_id: ID de sesión para mantener contexto (opcional)
        """
        logger.info(f"GraphQL: Chat con Alex -> '{query}' (session: {session_id})")

        # Llamamos a SearchService (donde vive el orquestador multi-agente)
        result = await search_service.semantic_search(query, session_id=session_id)

        return SemanticSearchResponse(
            answer=result.answer,
            query=query
        )