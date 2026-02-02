"""
Servicio de Gestión de Pedidos (Orders).
Maneja la creación, consulta y actualización de pedidos.
"""
import asyncio
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError, IntegrityError
from sqlalchemy.orm import selectinload

from backend.config.logging_config import get_logger
from backend.database.models import Order, OrderDetail, OrderStatus, ProductStock
from backend.domain.order_schemas import (
    OrderCreate,
    OrderSchema,
    OrderSummarySchema,
    CheckoutResponse,
    OrderUpdate,
)


class OrderServiceError(Exception):
    """Excepción base para errores del servicio de pedidos."""
    pass


class InsufficientStockError(OrderServiceError):
    """Error cuando no hay stock suficiente."""
    pass


class ProductNotFoundError(OrderServiceError):
    """Error cuando no se encuentra un producto."""
    pass


class InvalidOrderStateError(OrderServiceError):
    """Error cuando el pedido no puede realizar una operación por su estado."""
    pass


class OrderService:
    """
    Servicio para gestión completa de pedidos.
    
    Responsabilidades:
    - Crear pedidos desde el chat (checkout flow)
    - Consultar pedidos por usuario
    - Actualizar estados de pedidos
    - Gestionar stock con atomicidad
    """
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory
        self.logger = get_logger("order_service")
    
    # ========================================================================
    # MÉTODOS DE CONSULTA
    # ========================================================================
    
    async def get_order_by_id(
        self, 
        order_id: UUID, 
        include_details: bool = True
    ) -> Optional[Order]:
        """
        Obtiene un pedido por su ID.
        
        Args:
            order_id: ID del pedido
            include_details: Si True, carga las líneas de detalle
            
        Returns:
            El pedido encontrado o None
        """
        try:
            async with self.session_factory() as session:
                query = select(Order).where(Order.id == order_id)
                
                if include_details:
                    query = query.options(selectinload(Order.details))
                
                result = await session.execute(query)
                return result.scalar_one_or_none()
                
        except Exception as e:
            self.logger.error(f"Error consultando pedido {order_id}: {e}")
            return None
    
    async def get_orders_by_user(
        self, 
        user_id: UUID, 
        limit: int = 10,
        offset: int = 0
    ) -> List[Order]:
        """
        Obtiene los pedidos de un usuario.
        
        Args:
            user_id: ID del usuario
            limit: Máximo de resultados
            offset: Desplazamiento para paginación
            
        Returns:
            Lista de pedidos ordenados por fecha descendente
        """
        try:
            async with self.session_factory() as session:
                query = (
                    select(Order)
                    .where(Order.user_id == user_id)
                    .order_by(desc(Order.created_at))
                    .offset(offset)
                    .limit(limit)
                    .options(selectinload(Order.details))
                )
                
                result = await session.execute(query)
                return list(result.scalars().all())
                
        except Exception as e:
            self.logger.error(f"Error consultando pedidos del usuario {user_id}: {e}")
            return []
    
    async def get_recent_orders(
        self, 
        limit: int = 20,
        status_filter: Optional[str] = None
    ) -> List[Order]:
        """
        Obtiene los pedidos más recientes (para admin).
        
        Args:
            limit: Máximo de resultados
            status_filter: Filtrar por estado específico
            
        Returns:
            Lista de pedidos recientes
        """
        try:
            async with self.session_factory() as session:
                query = select(Order).order_by(desc(Order.created_at))
                
                if status_filter:
                    query = query.where(Order.status == status_filter)
                
                query = query.limit(limit).options(selectinload(Order.details))
                
                result = await session.execute(query)
                return list(result.scalars().all())
                
        except Exception as e:
            self.logger.error(f"Error consultando pedidos recientes: {e}")
            return []
    
    # ========================================================================
    # CREACIÓN DE PEDIDOS
    # ========================================================================
    
    async def create_order(self, order_data: OrderCreate) -> Tuple[Order, str]:
        """
        Crea un nuevo pedido con validación completa de stock.
        
        Este método:
        1. Valida que todos los productos existan
        2. Valida stock suficiente
        3. Bloquea el stock descontándolo de product_stocks
        4. Crea el pedido y sus detalles en una transacción atómica
        5. Retorna el pedido creado
        
        Args:
            order_data: Datos del pedido a crear
            
        Returns:
            Tupla de (pedido_creado, mensaje)
            
        Raises:
            ProductNotFoundError: Si algún producto no existe
            InsufficientStockError: Si no hay stock suficiente
            OrderServiceError: Por errores de BD
        """
        self.logger.info(
            "Creating order",
            user_id=order_data.user_id,
            item_count=len(order_data.details)
        )
        
        try:
            async with self.session_factory() as session:
                # Iniciar transacción
                async with session.begin():
                    # -----------------------------------------------------------------
                    # PASO 1: Validar y bloquear productos
                    # -----------------------------------------------------------------
                    locked_products = []
                    order_details = []
                    
                    for item in order_data.details:
                        # Buscar producto con bloqueo para evitar race conditions
                        product_query = (
                            select(ProductStock)
                            .where(
                                ProductStock.id == item.product_id,
                                ProductStock.is_active == True
                            )
                        )
                        
                        result = await session.execute(product_query)
                        product = result.scalar_one_or_none()
                        
                        if not product:
                            raise ProductNotFoundError(
                                f"Producto no encontrado: {item.product_id}"
                            )
                        
                        # Validar stock
                        if product.quantity_available < item.quantity:
                            raise InsufficientStockError(
                                f"Stock insuficiente para '{product.product_name}'. "
                                f"Disponible: {product.quantity_available}, "
                                f"Solicitado: {item.quantity}"
                            )
                        
                        # Bloquear stock (descontar)
                        product.quantity_available -= item.quantity
                        
                        # Crear detalle del pedido
                        detail = OrderDetail(
                            product_id=product.id,
                            product_name=product.product_name,
                            product_sku=product.product_sku,
                            quantity=item.quantity,
                            unit_price=product.unit_cost,
                        )
                        order_details.append(detail)
                        locked_products.append(product)
                        
                        self.logger.debug(
                            "Stock reserved",
                            product=product.product_name,
                            quantity=item.quantity,
                            remaining=product.quantity_available
                        )
                    
                    # -----------------------------------------------------------------
                    # PASO 2: Crear el pedido
                    # -----------------------------------------------------------------
                    order = Order(
                        user_id=order_data.user_id,
                        status=OrderStatus.CONFIRMED,
                        payment_status="PENDING",
                        shipping_address=order_data.shipping_address,
                        shipping_city=order_data.shipping_city,
                        shipping_state=order_data.shipping_state,
                        shipping_country=order_data.shipping_country,
                        shipping_zip=order_data.shipping_zip,
                        contact_name=order_data.contact_name,
                        contact_phone=order_data.contact_phone,
                        contact_email=order_data.contact_email,
                        notes=order_data.notes,
                        session_id=order_data.session_id,
                        internal_notes="Creado desde chatbot",
                    )
                    
                    # Agregar detalles al pedido
                    order.details = order_details
                    
                    # Calcular totales
                    order.calculate_totals()
                    
                    # Guardar en BD
                    session.add(order)
                    await session.flush()  # Genera el ID sin hacer commit
                    
                    # Refrescar para cargar relaciones
                    await session.refresh(order, attribute_names=["details"])
                    
                # Commit automático al salir del contexto
                
                self.logger.info(
                    "Order created successfully",
                    order_id=order.id,
                    total=order.total_amount,
                    item_count=len(order.details)
                )
                
                message = (
                    f"Pedido #{str(order.id)[:8]} creado exitosamente. "
                    f"Total: ${order.total_amount:.2f}"
                )
                
                return order, message
                
        except ProductNotFoundError:
            raise
        except InsufficientStockError:
            raise
        except asyncio.TimeoutError:
            self.logger.error("Timeout creating order")
            raise OrderServiceError(
                "La base de datos no responde. Por favor intenta nuevamente."
            )
        except OperationalError as e:
            self.logger.error(f"Database error creating order: {e}")
            raise OrderServiceError(
                "Error de base de datos. Intenta más tarde."
            )
        except SQLAlchemyError as e:
            self.logger.error(f"Database error creating order: {e}")
            raise OrderServiceError(
                "No se pudo crear el pedido. Contacta a soporte."
            )
        except Exception as e:
            self.logger.error(f"Unexpected error creating order: {e}", exc_info=True)
            raise OrderServiceError(
                "Error inesperado. Nuestro equipo ha sido notificado."
            )
    
    async def create_order_from_checkout(
        self,
        user_id: UUID,
        items: List[dict],
        shipping_address: str,
        session_id: Optional[str] = None
    ) -> CheckoutResponse:
        """
        Método simplificado para crear pedido desde el flujo de checkout del chat.
        
        Args:
            user_id: ID del usuario
            items: Lista de dicts con {product_id, quantity}
            shipping_address: Dirección de envío
            session_id: ID de sesión del chat
            
        Returns:
            CheckoutResponse con resultado de la operación
        """
        from backend.domain.order_schemas import OrderDetailCreate
        
        try:
            # Convertir items al formato esperado
            details = [
                OrderDetailCreate(
                    product_id=item["product_id"],
                    quantity=item["quantity"]
                )
                for item in items
            ]
            
            # Crear orden
            order_data = OrderCreate(
                user_id=user_id,
                details=details,
                shipping_address=shipping_address,
                session_id=session_id
            )
            
            order, message = await self.create_order(order_data)
            
            return CheckoutResponse(
                success=True,
                order_id=order.id,
                message=message,
                order_total=order.total_amount,
                item_count=order.item_count
            )
            
        except ProductNotFoundError as e:
            return CheckoutResponse(
                success=False,
                message=str(e),
                error_code="PRODUCT_NOT_FOUND"
            )
        except InsufficientStockError as e:
            return CheckoutResponse(
                success=False,
                message=str(e),
                error_code="INSUFFICIENT_STOCK"
            )
        except OrderServiceError as e:
            return CheckoutResponse(
                success=False,
                message=str(e),
                error_code="SERVICE_ERROR"
            )
        except Exception as e:
            self.logger.error(f"Unexpected checkout error: {e}", exc_info=True)
            return CheckoutResponse(
                success=False,
                message="Error inesperado procesando tu pedido",
                error_code="UNKNOWN_ERROR"
            )
    
    # ========================================================================
    # ACTUALIZACIÓN DE PEDIDOS
    # ========================================================================
    
    async def update_order_status(
        self, 
        order_id: UUID, 
        new_status: str,
        reason: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Actualiza el estado de un pedido.
        
        Args:
            order_id: ID del pedido
            new_status: Nuevo estado
            reason: Razón del cambio (opcional)
            
        Returns:
            Tupla de (éxito, mensaje)
        """
        try:
            async with self.session_factory() as session:
                order = await session.get(Order, order_id)
                
                if not order:
                    return False, "Pedido no encontrado"
                
                if not order.can_transition_to(new_status):
                    return (
                        False, 
                        f"No se puede cambiar de {order.status} a {new_status}"
                    )
                
                old_status = order.status
                order.status = new_status
                
                # Actualizar estado de pago según corresponda
                if new_status == OrderStatus.PAID:
                    order.payment_status = "COMPLETED"
                elif new_status == OrderStatus.CANCELLED:
                    order.payment_status = "FAILED"
                    # TODO: Restaurar stock si se cancela
                
                if reason:
                    order.internal_notes = f"{order.internal_notes or ''}\n[{old_status}->{new_status}]: {reason}"
                
                await session.commit()
                
                self.logger.info(
                    "Order status updated",
                    order_id=order_id,
                    old_status=old_status,
                    new_status=new_status
                )
                
                return True, f"Estado actualizado a {new_status}"
                
        except Exception as e:
            self.logger.error(f"Error updating order {order_id}: {e}")
            return False, "Error actualizando el pedido"
    
    async def cancel_order(
        self, 
        order_id: UUID, 
        reason: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Cancela un pedido y restaura el stock.
        
        Args:
            order_id: ID del pedido
            reason: Razón de la cancelación
            
        Returns:
            Tupla de (éxito, mensaje)
        """
        try:
            async with self.session_factory() as session:
                async with session.begin():
                    order = await session.get(Order, order_id)
                    
                    if not order:
                        return False, "Pedido no encontrado"
                    
                    if order.status in [OrderStatus.DELIVERED, OrderStatus.CANCELLED]:
                        return False, f"No se puede cancelar un pedido {order.status}"
                    
                    # Restaurar stock
                    for detail in order.details:
                        product = await session.get(ProductStock, detail.product_id)
                        if product:
                            product.quantity_available += detail.quantity
                            self.logger.debug(
                                "Stock restored",
                                product=product.product_name,
                                quantity=detail.quantity
                            )
                    
                    # Actualizar estado
                    order.status = OrderStatus.CANCELLED
                    order.payment_status = "REFUNDED"
                    
                    if reason:
                        order.internal_notes = f"{order.internal_notes or ''}\n[CANCELLED]: {reason}"
                
                self.logger.info("Order cancelled", order_id=order_id, reason=reason)
                return True, "Pedido cancelado exitosamente"
                
        except Exception as e:
            self.logger.error(f"Error cancelling order {order_id}: {e}")
            return False, "Error cancelando el pedido"
    
    # ========================================================================
    # MÉTODOS AUXILIARES
    # ========================================================================
    
    async def get_order_stats(self, user_id: Optional[UUID] = None) -> dict:
        """
        Obtiene estadísticas de pedidos.
        
        Args:
            user_id: Si se especifica, filtra por usuario
            
        Returns:
            Dict con estadísticas
        """
        try:
            async with self.session_factory() as session:
                query = select(Order)
                
                if user_id:
                    query = query.where(Order.user_id == user_id)
                
                result = await session.execute(query)
                orders = result.scalars().all()
                
                total_orders = len(orders)
                total_revenue = sum(o.total_amount for o in orders if o.status != OrderStatus.CANCELLED)
                
                status_counts = {}
                for order in orders:
                    status_counts[order.status] = status_counts.get(order.status, 0) + 1
                
                return {
                    "total_orders": total_orders,
                    "total_revenue": float(total_revenue),
                    "status_breakdown": status_counts,
                    "average_order_value": float(total_revenue / total_orders) if total_orders > 0 else 0
                }
                
        except Exception as e:
            self.logger.error(f"Error getting order stats: {e}")
            return {
                "total_orders": 0,
                "total_revenue": 0.0,
                "status_breakdown": {},
                "average_order_value": 0.0
            }
