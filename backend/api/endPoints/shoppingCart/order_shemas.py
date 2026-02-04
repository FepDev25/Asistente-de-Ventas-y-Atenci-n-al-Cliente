from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict




class OrderDetailResponse(BaseModel):
    """Schema para respuesta de detalle de pedido."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    product_id: UUID
    product_name: str
    product_sku: Optional[str] = None
    quantity: int
    unit_price: Decimal
    discount_amount: Decimal = Decimal("0.0")
    subtotal: Decimal
    total_without_discount: Decimal


class OrderResponse(BaseModel):
    """Schema para respuesta de pedido."""
    model_config = ConfigDict(from_attributes=True)
    
    id: UUID
    user_id: UUID
    status: str
    created_at: str
    updated_at: str
    
    # Información monetaria
    subtotal: Decimal
    tax_amount: Decimal
    shipping_cost: Decimal
    discount_amount: Decimal
    total_amount: Decimal
    
    # Información de envío
    shipping_address: str
    shipping_city: Optional[str] = None
    shipping_state: Optional[str] = None
    shipping_country: Optional[str] = None
    shipping_zip: Optional[str] = None
    
    # Información de contacto
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    # Información de pago
    payment_method: Optional[str] = None
    payment_status: str
    
    # Notas
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    
    # Detalles
    details: List[OrderDetailResponse] = []
    
    # Propiedades calculadas
    item_count: int
    is_editable: bool
    is_finalized: bool


class CreateOrderRequest(BaseModel):
    """Schema para crear un pedido."""
    shipping_address: str = Field(..., min_length=1, max_length=500)
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=100)
    shipping_country: str = Field(default="Ecuador", max_length=100)
    shipping_zip: Optional[str] = Field(None, max_length=20)
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = None
    session_id: Optional[str] = Field(None, max_length=255)


class AddItemRequest(BaseModel):
    """Schema para agregar un item al pedido."""
    product_id: UUID
    quantity: int = Field(..., gt=0)
    unit_price: Optional[Decimal] = Field(None, ge=0)


class UpdateQuantityRequest(BaseModel):
    """Schema para actualizar cantidad de un item."""
    quantity: int = Field(..., ge=0)


class UpdateShippingRequest(BaseModel):
    """Schema para actualizar información de envío."""
    shipping_address: Optional[str] = Field(None, min_length=1, max_length=500)
    shipping_city: Optional[str] = Field(None, max_length=100)
    shipping_state: Optional[str] = Field(None, max_length=100)
    shipping_country: Optional[str] = Field(None, max_length=100)
    shipping_zip: Optional[str] = Field(None, max_length=20)
    contact_name: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)
    contact_email: Optional[str] = Field(None, max_length=255)


class ApplyDiscountRequest(BaseModel):
    """Schema para aplicar descuento."""
    discount_amount: Decimal = Field(..., ge=0)


class SetShippingCostRequest(BaseModel):
    """Schema para establecer costo de envío."""
    shipping_cost: Decimal = Field(..., ge=0)


class SetTaxRequest(BaseModel):
    """Schema para establecer impuestos."""
    tax_amount: Decimal = Field(..., ge=0)


class ChangeStatusRequest(BaseModel):
    """Schema para cambiar estado del pedido."""
    new_status: str
    internal_notes: Optional[str] = None


class ProcessPaymentRequest(BaseModel):
    """Schema para procesar pago."""
    payment_method: str = Field(..., min_length=1, max_length=50)


class CancelOrderRequest(BaseModel):
    """Schema para cancelar pedido."""
    reason: Optional[str] = None


class SuccessResponse(BaseModel):
    """Schema para respuestas exitosas."""
    success: bool
    message: str
    data: Optional[dict] = None