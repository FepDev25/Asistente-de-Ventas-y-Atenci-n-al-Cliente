"""
Tipos de datos GraphQL (Esquemas).
Define qué datos puede pedir el Frontend.
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from uuid import UUID
import strawberry

# ============================================================================
# TIPOS DE PRODUCTOS
# ============================================================================

@strawberry.type
class ProductStockType:
    """Lo que ve el cliente sobre un producto."""
    id: UUID
    product_name: str
    
    # Precios y Stock
    unit_cost: Decimal
    quantity_available: int
    stock_status: int  # 1=Disponible, 0=Agotado
    
    # Ubicación (util para envios)
    warehouse_location: str
    
    # Extras (Descripción y Keywords)
    shelf_location: Optional[str] 
    batch_number: Optional[str]


# ============================================================================
# TIPOS DE USUARIO
# ============================================================================

@strawberry.type
class UserType:
    """Información pública de un usuario."""
    id: UUID
    username: str
    email: str
    full_name: str
    role: int  # 1=Admin, 2=Cliente
    is_active: bool
    created_at: Optional[datetime] = None


@strawberry.type
class UserWithOrdersType:
    """Usuario con sus pedidos."""
    id: UUID
    username: str
    email: str
    full_name: str
    role: int
    is_active: bool
    created_at: Optional[datetime] = None
    orders: List["OrderSummaryType"] = strawberry.field(default_factory=list)


# ============================================================================
# TIPOS DE ORDEN/PEDIDO
# ============================================================================

@strawberry.type
class OrderDetailType:
    """Linea de detalle de un pedido."""
    id: UUID
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Decimal
    
    @strawberry.field
    def subtotal(self) -> Decimal:
        """Calcula el subtotal de la linea."""
        return self.unit_price * Decimal(self.quantity)


@strawberry.type
class OrderType:
    """Pedido completo con todos los detalles."""
    id: UUID
    user_id: UUID
    status: str  # DRAFT, CONFIRMED, PAID, SHIPPED, DELIVERED, CANCELLED
    
    # Totales
    subtotal: Decimal
    total_amount: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    discount_amount: Decimal
    
    # Dirección de envío
    shipping_address: str
    shipping_city: Optional[str]
    shipping_state: Optional[str]
    shipping_country: Optional[str]
    
    # Detalles y metadata
    details: List[OrderDetailType] = strawberry.field(default_factory=list)
    notes: Optional[str]
    session_id: Optional[str]
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@strawberry.type
class OrderSummaryType:
    """Resumen de pedido (para listas)."""
    id: UUID
    status: str
    total_amount: Decimal
    item_count: int
    created_at: Optional[datetime] = None


# ============================================================================
# TIPOS DE RESPUESTA
# ============================================================================

@strawberry.type
class SemanticSearchResponse:
    """
    La respuesta de Alex (El Agente).

    El campo 'error' indica si hubo algún problema:
    - None: Respuesta exitosa
    - "timeout": LLM o BD tardó demasiado
    - "internal_error": Error técnico general
    - "service_unavailable": Servicio no disponible
    - "unauthorized": No autenticado
    """
    answer: str
    query: str
    error: Optional[str] = None


@strawberry.type
class ProductRecognitionResponse:
    """Respuesta del reconocimiento de producto por imagen."""
    success: bool
    product_name: Optional[str] = None
    matches: int = 0
    confidence: float = 0.0
    error: Optional[str] = None


@strawberry.type
class CreateOrderResponse:
    """Respuesta de creación de orden."""
    success: bool
    order: Optional[OrderType] = None
    message: str
    error: Optional[str] = None


@strawberry.type
class AuthResponse:
    """Respuesta de autenticación."""
    success: bool
    access_token: Optional[str] = None
    token_type: str = "bearer"
    user: Optional[UserType] = None
    error: Optional[str] = None


# ============================================================================
# INPUTS PARA MUTATIONS
# ============================================================================

@strawberry.input
class CreateUserInput:
    """Datos para crear un usuario."""
    username: str
    email: str
    password: str
    full_name: str
    role: int = 2  # 2 = Cliente por defecto


@strawberry.input
class UpdateUserInput:
    """Datos para actualizar un usuario."""
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


@strawberry.input
class ChangePasswordInput:
    """Datos para cambiar contraseña."""
    old_password: str
    new_password: str


@strawberry.input
class OrderDetailInput:
    """Linea de detalle para crear orden."""
    product_id: UUID
    quantity: int


@strawberry.input
class CreateOrderInput:
    """Datos para crear una orden."""
    details: List[OrderDetailInput]
    shipping_address: str
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_country: Optional[str] = "Ecuador"
    notes: Optional[str] = None
    session_id: Optional[str] = None


@strawberry.input
class UpdateOrderStatusInput:
    """Datos para actualizar estado de orden."""
    status: str  # CONFIRMED, PAID, SHIPPED, DELIVERED, CANCELLED
    reason: Optional[str] = None


@strawberry.input
class ProductFilterInput:
    """Filtros para buscar productos."""
    query: Optional[str] = None
    min_price: Optional[Decimal] = None
    max_price: Optional[Decimal] = None
    in_stock: Optional[bool] = None
    warehouse_location: Optional[str] = None
