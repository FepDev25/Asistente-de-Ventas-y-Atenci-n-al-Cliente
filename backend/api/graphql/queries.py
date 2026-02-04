"""
Consultas GraphQL (Endpoints).
Aqui el Frontend pide cosas al Backend.
"""
import asyncio
from typing import Annotated, List, Optional
from uuid import UUID
import strawberry
from aioinject import Inject
from aioinject.ext.strawberry import inject
from loguru import logger
from strawberry.types import Info

from backend.config.security import securityJWT

from backend.api.graphql.types import (
    ProductStockType, 
    SemanticSearchResponse,
    UserType,
    OrderType,
    OrderSummaryType
)
from backend.services.product_service import ProductService
from backend.services.order_service import OrderService
from backend.services.search_service import SearchService
from backend.services.user_service import UserService


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

    # ========================================================================
    # PRODUCTOS
    # ========================================================================

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
    async def get_product_by_id(
        self,
        id: UUID,
        info: Info,
        product_service: Annotated[ProductService, Inject]
    ) -> Optional[ProductStockType]:
        """
        Obtiene un producto específico por su ID.
        
        Query: { getProductById(id: "uuid-aqui") { productName unitCost quantityAvailable } }
        """
        logger.info(f"GraphQL: Obteniendo producto {id}")
        
        try:
            product = await product_service.get_product_by_id(id)
            
            if not product:
                return None
            
            return ProductStockType(
                id=product.id,
                product_name=product.product_name,
                unit_cost=product.unit_cost,
                quantity_available=product.quantity_available,
                stock_status=product.stock_status,
                warehouse_location=product.warehouse_location,
                shelf_location=product.shelf_location,
                batch_number=product.batch_number
            )
            
        except Exception as e:
            logger.error(f"Error en get_product_by_id: {e}")
            return None

    # ========================================================================
    # USUARIOS
    # ========================================================================

    @strawberry.field
    @inject
    async def get_current_user(
        self,
        info: Info,
        user_service: Annotated[UserService, Inject]
    ) -> Optional[UserType]:
        """
        Obtiene el perfil del usuario autenticado.
        
        Requiere: header Authorization: Bearer <token>
        
        Query: { getCurrentUser { id username email fullName } }
        """
        user_data = get_current_user(info)
        
        if not user_data:
            logger.warning("Intento de obtener usuario sin autenticacion")
            return None
        
        try:
            user = await user_service.get_user_by_id(UUID(user_data["id"]))
            
            if not user:
                return None
            
            return UserType(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at
            )
            
        except Exception as e:
            logger.error(f"Error en get_current_user: {e}")
            return None

    @strawberry.field
    @inject
    async def get_user_by_id(
        self,
        id: UUID,
        info: Info,
        user_service: Annotated[UserService, Inject]
    ) -> Optional[UserType]:
        """
        Obtiene un usuario por su ID.
        
        Nota: Solo admins deberian poder ver otros usuarios.
        """
        # Verificar autenticación
        current_user = get_current_user(info)
        if not current_user:
            logger.warning("Intento de obtener usuario sin autenticacion")
            return None
        
        # Solo permite ver el propio perfil o si es admin
        if str(id) != current_user["id"] and current_user.get("role") != 1:
            logger.warning(f"Usuario {current_user['id']} intento acceder a perfil de {id}")
            return None
        
        try:
            user = await user_service.get_user_by_id(id)
            
            if not user:
                return None
            
            return UserType(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at
            )
            
        except Exception as e:
            logger.error(f"Error en get_user_by_id: {e}")
            return None

    # ========================================================================
    # ORDENES/PEDIDOS
    # ========================================================================

    @strawberry.field
    @inject
    async def get_order_by_id(
        self,
        id: UUID,
        info: Info,
        order_service: Annotated[OrderService, Inject]
    ) -> Optional[OrderType]:
        """
        Obtiene un pedido específico por su ID.
        
        Requiere autenticación. Solo el dueño o admin puede ver el pedido.
        
        Query: { getOrderById(id: "uuid-aqui") { status totalAmount details { productName quantity } } }
        """
        current_user = get_current_user(info)
        
        if not current_user:
            logger.warning("Intento de obtener orden sin autenticacion")
            return None
        
        try:
            order = await order_service.get_order_by_id(id, include_details=True)
            
            if not order:
                return None
            
            # Verificar que el usuario sea el dueño o admin
            if str(order.user_id) != current_user["id"] and current_user.get("role") != 1:
                logger.warning(f"Usuario {current_user['id']} intento acceder a orden {id}")
                return None
            
            return OrderType(
                id=order.id,
                user_id=order.user_id,
                status=order.status,
                subtotal=order.subtotal,
                total_amount=order.total_amount,
                tax_amount=order.tax_amount,
                shipping_cost=order.shipping_cost,
                discount_amount=order.discount_amount,
                shipping_address=order.shipping_address,
                shipping_city=order.shipping_city,
                shipping_state=order.shipping_state,
                shipping_country=order.shipping_country,
                details=[
                    OrderDetailType(
                        id=d.id,
                        product_id=d.product_id,
                        product_name=d.product_name,
                        quantity=d.quantity,
                        unit_price=d.unit_price
                    )
                    for d in order.details
                ],
                notes=order.notes,
                session_id=order.session_id,
                created_at=order.created_at,
                updated_at=order.updated_at
            )
            
        except Exception as e:
            logger.error(f"Error en get_order_by_id: {e}")
            return None

    @strawberry.field
    @inject
    async def get_my_orders(
        self,
        info: Info,
        order_service: Annotated[OrderService, Inject],
        limit: int = 10,
        offset: int = 0
    ) -> List[OrderSummaryType]:
        """
        Obtiene los pedidos del usuario autenticado.
        
        Requiere: header Authorization: Bearer <token>
        
        Query: { getMyOrders(limit: 5) { id status totalAmount itemCount createdAt } }
        """
        current_user = get_current_user(info)
        
        if not current_user:
            logger.warning("Intento de obtener ordenes sin autenticacion")
            return []
        
        user_id = UUID(current_user["id"])
        
        try:
            orders = await order_service.get_orders_by_user(
                user_id=user_id,
                limit=limit,
                offset=offset
            )
            
            return [
                OrderSummaryType(
                    id=order.id,
                    status=order.status,
                    total_amount=order.total_amount,
                    item_count=sum(d.quantity for d in order.details) if order.details else 0,
                    created_at=order.created_at
                )
                for order in orders
            ]
            
        except Exception as e:
            logger.error(f"Error en get_my_orders: {e}")
            return []

    @strawberry.field
    @inject
    async def get_recent_orders(
        self,
        info: Info,
        order_service: Annotated[OrderService, Inject],
        limit: int = 20,
        status_filter: Optional[str] = None
    ) -> List[OrderSummaryType]:
        """
        Obtiene los pedidos recientes (solo para admins).
        
        Requiere: header Authorization: Bearer <token> con rol admin
        """
        current_user = get_current_user(info)
        
        if not current_user:
            logger.warning("Intento de obtener ordenes recientes sin autenticacion")
            return []
        
        # Verificar que sea admin
        if current_user.get("role") != 1:
            logger.warning(f"Usuario {current_user['id']} intento acceder a ordenes recientes")
            return []
        
        try:
            orders = await order_service.get_recent_orders(
                limit=limit,
                status_filter=status_filter
            )
            
            return [
                OrderSummaryType(
                    id=order.id,
                    status=order.status,
                    total_amount=order.total_amount,
                    item_count=sum(d.quantity for d in order.details) if order.details else 0,
                    created_at=order.created_at
                )
                for order in orders
            ]
            
        except Exception as e:
            logger.error(f"Error en get_recent_orders: {e}")
            return []

    # ========================================================================
    # CHAT/AGENTE
    # ========================================================================

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


# Importación tardía para evitar circular imports
from backend.api.graphql.types import OrderDetailType