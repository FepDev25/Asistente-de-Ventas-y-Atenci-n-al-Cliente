"""
Endpoints de Pedidos (Orders)
API REST para gestión de pedidos con autenticación JWT.
"""
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


from backend.config.security.dependencies import get_current_active_user
from backend.database.session import get_session
from backend.database.controllers.orders_controller import OrderController
from backend.api.endPoints.shoppingCart.order_shemas import *


# =========================================================================
# HELPER FUNCTION
# =========================================================================

async def verify_order_ownership(
    order_id: UUID,
    user_id: UUID,
    session: AsyncSession
) -> None:
    """
    Verifica que el pedido pertenezca al usuario.
    
    Args:
        order_id: ID del pedido
        user_id: ID del usuario
        session: Sesión de base de datos
        
    Raises:
        HTTPException: Si el pedido no existe o no pertenece al usuario
    """
    controller = OrderController(session)
    order = await controller.get_by_id(order_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pedido no encontrado"
        )
    
    if order.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para acceder a este pedido"
        )




router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    
)


# =========================================================================
# ENDPOINTS DE CONSULTA
# =========================================================================

@router.get("/", response_model=List[OrderResponse])
async def get_my_orders(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Obtiene los pedidos del usuario actual.
    
    Query params:
        - status: Filtro opcional por estado
        - limit: Cantidad máxima de resultados (default: 50)
        - offset: Desplazamiento para paginación (default: 0)
    """
    async with get_session() as session:
        controller = OrderController(session)
        user_id = UUID(current_user["id"])
        
        orders = await controller.get_user_orders(
            user_id=user_id,
            status=status,
            limit=limit,
            offset=offset
        )
        
        return [
            OrderResponse(
                **order.__dict__,
                created_at=order.created_at.isoformat(),
                updated_at=order.updated_at.isoformat(),
                item_count=order.item_count,
                is_editable=order.is_editable,
                is_finalized=order.is_finalized
            )
            for order in orders
        ]


@router.get("/cart", response_model=OrderResponse)
async def get_my_cart(
    current_user: dict = Depends(get_current_active_user)
):
    """
    Obtiene el carrito activo del usuario (pedido en estado DRAFT).
    Si no existe, lo crea automáticamente.
    """
    async with get_session() as session:
        controller = OrderController(session)
        user_id = UUID(current_user["id"])
        
        cart = await controller.get_or_create_cart(user_id)
        await session.commit()
        
        return OrderResponse(
            **cart.__dict__,
            created_at=cart.created_at.isoformat(),
            updated_at=cart.updated_at.isoformat(),
            item_count=cart.item_count,
            is_editable=cart.is_editable,
            is_finalized=cart.is_finalized
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_by_id(
    order_id: UUID,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Obtiene un pedido específico por su ID.
    Solo permite ver pedidos propios.
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        order = await controller.get_by_id(order_id)
        
        return OrderResponse(
            **order.__dict__,
            created_at=order.created_at.isoformat(),
            updated_at=order.updated_at.isoformat(),
            item_count=order.item_count,
            is_editable=order.is_editable,
            is_finalized=order.is_finalized
        )


# =========================================================================
# ENDPOINTS DE CREACIÓN
# =========================================================================

@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    request: CreateOrderRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Crea un nuevo pedido.
    """
    async with get_session() as session:
        controller = OrderController(session)
        user_id = UUID(current_user["id"])
        
        order = await controller.create_order(
            user_id=user_id,
            shipping_address=request.shipping_address,
            shipping_city=request.shipping_city,
            shipping_state=request.shipping_state,
            shipping_country=request.shipping_country,
            shipping_zip=request.shipping_zip,
            contact_name=request.contact_name,
            contact_phone=request.contact_phone,
            contact_email=request.contact_email,
            notes=request.notes,
            session_id=request.session_id
        )
        
        await session.commit()
        await session.refresh(order)
        
        return OrderResponse(
            **order.__dict__,
            created_at=order.created_at.isoformat(),
            updated_at=order.updated_at.isoformat(),
            item_count=order.item_count,
            is_editable=order.is_editable,
            is_finalized=order.is_finalized
        )


# =========================================================================
# ENDPOINTS DE GESTIÓN DE ITEMS
# =========================================================================

@router.post("/{order_id}/items", response_model=SuccessResponse)
async def add_item_to_order(
    order_id: UUID,
    request: AddItemRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Agrega un item al pedido.
    Si el producto ya existe en el pedido, incrementa la cantidad.
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message, detail = await controller.add_item(
            order_id=order_id,
            product_id=request.product_id,
            quantity=request.quantity,
            unit_price=request.unit_price
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(
            success=True,
            message=message,
            data={"detail_id": str(detail.id)} if detail else None
        )


@router.put("/{order_id}/items/{detail_id}", response_model=SuccessResponse)
async def update_item_quantity(
    order_id: UUID,
    detail_id: UUID,
    request: UpdateQuantityRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Actualiza la cantidad de un item en el pedido.
    Si la cantidad es 0, elimina el item.
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message = await controller.update_item_quantity(
            order_id=order_id,
            detail_id=detail_id,
            new_quantity=request.quantity
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(success=True, message=message)


@router.delete("/{order_id}/items/{detail_id}", response_model=SuccessResponse)
async def remove_item_from_order(
    order_id: UUID,
    detail_id: UUID,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Elimina un item del pedido.
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message = await controller.remove_item(
            order_id=order_id,
            detail_id=detail_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(success=True, message=message)


@router.delete("/{order_id}/items", response_model=SuccessResponse)
async def clear_order(
    order_id: UUID,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Elimina todos los items del pedido (vacía el carrito).
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message = await controller.clear_order(order_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(success=True, message=message)


# =========================================================================
# ENDPOINTS DE ACTUALIZACIÓN
# =========================================================================

@router.put("/{order_id}/shipping", response_model=SuccessResponse)
async def update_shipping_info(
    order_id: UUID,
    request: UpdateShippingRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Actualiza la información de envío del pedido.
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message = await controller.update_shipping_info(
            order_id=order_id,
            shipping_address=request.shipping_address,
            shipping_city=request.shipping_city,
            shipping_state=request.shipping_state,
            shipping_country=request.shipping_country,
            shipping_zip=request.shipping_zip,
            contact_name=request.contact_name,
            contact_phone=request.contact_phone,
            contact_email=request.contact_email
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(success=True, message=message)


@router.put("/{order_id}/discount", response_model=SuccessResponse)
async def apply_discount(
    order_id: UUID,
    request: ApplyDiscountRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Aplica un descuento al pedido.
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message = await controller.apply_discount(
            order_id=order_id,
            discount_amount=request.discount_amount
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(success=True, message=message)


@router.put("/{order_id}/shipping-cost", response_model=SuccessResponse)
async def set_shipping_cost(
    order_id: UUID,
    request: SetShippingCostRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Establece el costo de envío del pedido.
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message = await controller.set_shipping_cost(
            order_id=order_id,
            shipping_cost=request.shipping_cost
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(success=True, message=message)


@router.put("/{order_id}/tax", response_model=SuccessResponse)
async def set_tax_amount(
    order_id: UUID,
    request: SetTaxRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Establece el monto de impuestos del pedido.
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message = await controller.set_tax_amount(
            order_id=order_id,
            tax_amount=request.tax_amount
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(success=True, message=message)


# =========================================================================
# ENDPOINTS DE GESTIÓN DE ESTADO
# =========================================================================

@router.put("/{order_id}/status", response_model=SuccessResponse)
async def change_order_status(
    order_id: UUID,
    request: ChangeStatusRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Cambia el estado del pedido.
    Valida las transiciones permitidas.
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message = await controller.change_status(
            order_id=order_id,
            new_status=request.new_status,
            internal_notes=request.internal_notes
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(success=True, message=message)


@router.post("/{order_id}/confirm", response_model=SuccessResponse)
async def confirm_order(
    order_id: UUID,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Confirma el pedido (DRAFT → CONFIRMED).
    Valida que tenga items y dirección de envío.
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message = await controller.confirm_order(order_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(success=True, message=message)


@router.post("/{order_id}/cancel", response_model=SuccessResponse)
async def cancel_order(
    order_id: UUID,
    request: CancelOrderRequest = CancelOrderRequest(),
    current_user: dict = Depends(get_current_active_user)
):
    """
    Cancela el pedido.
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message = await controller.cancel_order(
            order_id=order_id,
            reason=request.reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(success=True, message=message)


@router.post("/{order_id}/payment", response_model=SuccessResponse)
async def process_payment(
    order_id: UUID,
    request: ProcessPaymentRequest,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Procesa el pago del pedido (CONFIRMED → PAID).
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message = await controller.process_payment(
            order_id=order_id,
            payment_method=request.payment_method
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(success=True, message=message)


# =========================================================================
# ENDPOINTS DE ELIMINACIÓN
# =========================================================================

@router.delete("/{order_id}", response_model=SuccessResponse)
async def delete_order(
    order_id: UUID,
    current_user: dict = Depends(get_current_active_user)
):
    """
    Elimina un pedido (solo si está en estado DRAFT).
    """
    async with get_session() as session:
        user_id = UUID(current_user["id"])
        await verify_order_ownership(order_id, user_id, session)
        
        controller = OrderController(session)
        success, message = await controller.delete_order(order_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        
        await session.commit()
        
        return SuccessResponse(success=True, message=message)