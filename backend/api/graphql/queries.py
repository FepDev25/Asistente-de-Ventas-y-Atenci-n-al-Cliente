"""
Consultas GraphQL (Endpoints).
Aqui el Frontend pide cosas al Backend.
"""
import asyncio
from typing import Annotated, Optional
from uuid import UUID
import strawberry
from aioinject import Inject
from aioinject.ext.strawberry import inject
from loguru import logger
from strawberry.types import Info

from backend.config.security import securityJWT

from backend.api.graphql.types import ProductStockType, SemanticSearchResponse
from backend.services.product_service import ProductService
from backend.services.search_service import SearchService


def extract_token_from_request(info: Info) -> Optional[str]:
    """
    Extrae el token JWT del header Authorization si existe.
    Retorna None si no hay token o está mal formado.
    """
    request = info.context.get("request")
    if request is None:
        return None
    
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    
    return auth_header.replace("Bearer ", "")


def get_current_user(info: Info) -> Optional[dict]:
    """
    Obtiene el usuario actual del token JWT si existe.
    Retorna None si no hay token o es inválido.
    """
    token = extract_token_from_request(info)
    if not token:
        return None
    
    try:
        return securityJWT.decode_and_validate_token(token)
    except Exception:
        return None


@strawberry.type
class BusinessQuery:
    """Raiz de todas las consultas."""

    @strawberry.field
    @inject
    async def list_products(
        self,
        info: Info,
        product_service: Annotated[ProductService, Inject],
        limit: int = 20
    ) -> list[ProductStockType]:
        """
        Catalogo clasico: Devuelve lista de zapatos.
        Opcional: Requiere header Authorization: Bearer <token> para identificar usuario

        Query: { listProducts(limit: 10) { productName unitCost } }

        Returns:
            Lista de productos (vacía en caso de error)
        """
        user = get_current_user(info)
        user_info = f"usuario={user.get('username', 'anon')}" if user else "sin auth"
        logger.info(f"GraphQL: Listando {limit} productos ({user_info})")

        try:
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
            return []

    @strawberry.field
    @inject
    async def semantic_search(
        self,
        query: str,
        search_service: Annotated[SearchService, Inject],
        info: Info,
        session_id: str | None = None
    ) -> SemanticSearchResponse:
        """
        Chat con Alex: El usuario pregunta, la IA responde.
        
        Requiere: header Authorization: Bearer <token>

        Query: { semanticSearch(query: "Quiero Nike baratos", sessionId: "user123") { answer error } }

        Args:
            query: Consulta del usuario
            session_id: ID de sesion para mantener contexto (opcional)

        Returns:
            SemanticSearchResponse con answer (siempre) y error (opcional)
        """
        # Verificar autenticacion
        user = get_current_user(info)
        if user is None:
            logger.warning("Intento de acceso sin autenticacion a semantic_search")
            return SemanticSearchResponse(
                answer="Debes iniciar sesion para usar el chat.",
                query=query,
                error="unauthorized"
            )
        
        logger.info(f"GraphQL: Chat con Alex -> '{query}' (session: {session_id}, usuario={user.get('username')})")

        try:
            result = await asyncio.wait_for(
                search_service.semantic_search(query, session_id=session_id),
                timeout=30.0
            )

            return SemanticSearchResponse(
                answer=result.answer,
                query=query,
                error=None
            )

        except asyncio.TimeoutError:
            logger.error(
                f"Timeout procesando query (>30s): '{query[:50]}...'",
                exc_info=False
            )
            return SemanticSearchResponse(
                answer=(
                    "Lo siento, estoy teniendo problemas para responder. "
                    "Puedes intentar de nuevo? Si el problema persiste, "
                    "intenta hacer una pregunta mas simple."
                ),
                query=query,
                error="timeout"
            )

        except ConnectionError as e:
            logger.error(
                f"Servicio no disponible para query '{query[:50]}...': {str(e)}",
                exc_info=True
            )
            return SemanticSearchResponse(
                answer=(
                    "Disculpa, el servicio no esta disponible en este momento. "
                    "Por favor intenta nuevamente en unos minutos."
                ),
                query=query,
                error="service_unavailable"
            )

        except Exception as e:
            logger.error(
                f"Error inesperado en semantic_search: '{query[:50]}...': {str(e)}",
                exc_info=True
            )
            return SemanticSearchResponse(
                answer=(
                    "Disculpa, tuve un problema tecnico. "
                    "Nuestro equipo ha sido notificado. "
                    "Por favor intenta nuevamente."
                ),
                query=query,
                error="internal_error"
            )
