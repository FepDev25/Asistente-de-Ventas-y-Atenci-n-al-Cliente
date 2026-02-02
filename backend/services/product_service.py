"""
Servicio de Gestión de Productos (Inventario).
se conecta el Agente con la Base de Datos Real.
"""
import asyncio
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from backend.config.logging_config import get_logger
from backend.database.models import ProductStock


class ProductServiceError(Exception):
    """Excepción base para errores del servicio de productos."""
    pass


class ProductNotFoundError(ProductServiceError):
    """Error cuando no se encuentra un producto."""
    pass


class InsufficientStockError(ProductServiceError):
    """Error cuando no hay stock suficiente."""
    pass


class ProductService:
    """
    Servicio de Gestión de Productos e Inventario.
    
    Responsabilidades:
    - Búsqueda de productos
    - Consulta de stock
    - Actualización de inventario (usado por OrderService)
    
    Nota: La creación de pedidos ahora es responsabilidad de OrderService.
    Este servicio mantiene process_order() para compatibilidad hacia atrás,
    pero se recomienda usar OrderService.create_order() para nuevas implementaciones.
    """
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        # Inyectamos la fábrica de sesiones para conectar a la DB
        self.session_factory = session_factory
        self.logger = get_logger("product_service")

    async def search_by_name(self, name: str) -> list[ProductStock]:
        """
        Busca productos por nombre o palabras clave con manejo robusto de errores.

        Usado por la Tool: 'consultar_inventario'.

        Error Handling:
        - Timeout de BD (>5s) → Retorna lista vacía
        - BD caída → Retorna lista vacía con log
        - Error de query → Retorna lista vacía

        Returns:
            Lista de productos encontrados (vacía en caso de error)
        """
        from sqlalchemy import or_

        self.logger.info(
            "product_search_started",
            search_term=name,
            term_length=len(name)
        )

        try:
            async with self.session_factory() as session:
                # Búsqueda inteligente: dividir el término en palabras y buscar cada una
                search_words = name.lower().split()

                # Crear condiciones OR para cada palabra
                conditions = []
                for word in search_words:
                    # Buscar en product_name y product_sku
                    conditions.append(ProductStock.product_name.ilike(f"%{word}%"))
                    conditions.append(ProductStock.product_sku.ilike(f"%{word}%"))

                query = select(ProductStock).where(
                    or_(*conditions),
                    ProductStock.is_active == True
                ).limit(10)

                self.logger.info(f"🗃️ Palabras de búsqueda: {search_words}")

                # Ejecutar query con timeout
                result = await asyncio.wait_for(
                    session.execute(query),
                    timeout=5.0  # 5 segundos máximo
                )

                products = list(result.scalars().all())
                self.logger.info(f"🗃️ ProductService: Encontrados {len(products)} productos en DB")

                return products

        except asyncio.TimeoutError:
            self.logger.error(
                f"⏱️ Timeout buscando productos (>5s): '{name}'",
                exc_info=False
            )
            return []

        except OperationalError as e:
            self.logger.error(
                f"🚨 Base de datos no disponible al buscar '{name}': {str(e)}",
                exc_info=True
            )
            return []

        except SQLAlchemyError as e:
            self.logger.error(
                f"❌ Error de BD al buscar '{name}': {str(e)}",
                exc_info=True
            )
            return []

        except Exception as e:
            self.logger.error(
                f"💥 Error inesperado buscando '{name}': {str(e)}",
                exc_info=True
            )
            return []

    async def get_product_by_id(
        self, 
        product_id: UUID
    ) -> Optional[ProductStock]:
        """
        Obtiene un producto por su ID.
        
        Args:
            product_id: ID del producto
            
        Returns:
            El producto encontrado o None
        """
        try:
            async with self.session_factory() as session:
                return await session.get(ProductStock, product_id)
                
        except Exception as e:
            self.logger.error(f"Error consultando producto {product_id}: {e}")
            return None

    async def get_product_by_name(
        self, 
        product_name: str
    ) -> Optional[ProductStock]:
        """
        Obtiene un producto por nombre exacto o parcial.
        
        Args:
            product_name: Nombre del producto
            
        Returns:
            El primer producto encontrado o None
        """
        try:
            async with self.session_factory() as session:
                query = (
                    select(ProductStock)
                    .where(
                        ProductStock.product_name.ilike(f"%{product_name}%"),
                        ProductStock.is_active == True
                    )
                )
                result = await session.execute(query)
                return result.scalar_one_or_none()
                
        except Exception as e:
            self.logger.error(f"Error consultando producto '{product_name}': {e}")
            return None

    async def check_stock(
        self, 
        product_id: UUID, 
        quantity: int
    ) -> tuple[bool, int, str]:
        """
        Verifica si hay stock suficiente para un producto.
        
        Args:
            product_id: ID del producto
            quantity: Cantidad requerida
            
        Returns:
            Tupla de (hay_stock, stock_disponible, mensaje)
        """
        try:
            product = await self.get_product_by_id(product_id)
            
            if not product:
                return False, 0, "Producto no encontrado"
            
            if product.quantity_available < quantity:
                return (
                    False, 
                    product.quantity_available,
                    f"Stock insuficiente. Disponible: {product.quantity_available}"
                )
            
            return True, product.quantity_available, "Stock disponible"
            
        except Exception as e:
            self.logger.error(f"Error verificando stock: {e}")
            return False, 0, "Error verificando disponibilidad"

    async def process_order(
        self, 
        product_name: str, 
        quantity: int,
        create_order_record: bool = False,
        user_id: Optional[UUID] = None
    ) -> dict:
        """
        Procesa la venta: Valida stock y lo descuenta.
        
        DEPRECATED: Para nuevas implementaciones, usar OrderService.create_order()
        Este método se mantiene para compatibilidad con herramientas LLM existentes.

        Args:
            product_name: Nombre del producto a buscar
            quantity: Cantidad a comprar
            create_order_record: Si True, crea un registro en la tabla orders
            user_id: ID del usuario (requerido si create_order_record=True)

        Returns:
            Dict con resultado de la operación:
            {
                "success": bool,
                "message": str,
                "product_name": str,
                "quantity": int,
                "total": float,
                "remaining_stock": int,
                "order_id": UUID (solo si create_order_record=True)
            }
        """
        try:
            async with self.session_factory() as session:
                # Buscar el producto
                product = await self.get_product_by_name(product_name)

                if not product:
                    self.logger.warning(f"Producto no encontrado: '{product_name}'")
                    return {
                        "success": False,
                        "message": f"Error: No encontré el producto '{product_name}'.",
                        "product_name": product_name,
                        "quantity": quantity,
                        "total": 0.0,
                        "remaining_stock": 0
                    }

                # Validación de stock
                if product.quantity_available < quantity:
                    self.logger.warning(
                        f"Stock insuficiente para '{product.product_name}': "
                        f"solicitado={quantity}, disponible={product.quantity_available}"
                    )
                    return {
                        "success": False,
                        "message": (
                            f"Stock insuficiente. Solo quedan {product.quantity_available} "
                            f"unidades de {product.product_name}."
                        ),
                        "product_name": product.product_name,
                        "quantity": quantity,
                        "total": 0.0,
                        "remaining_stock": product.quantity_available
                    }

                # Ejecutar la transacción (descontar)
                product.quantity_available -= quantity
                await session.commit()

                total = product.unit_cost * quantity

                self.logger.info(
                    f"✅ Orden procesada: {product.product_name} "
                    f"x{quantity} = ${total:.2f}"
                )

                result = {
                    "success": True,
                    "message": (
                        f"¡VENTA EXITOSA!\n"
                        f"Producto: {product.product_name}\n"
                        f"Cantidad: {quantity}\n"
                        f"Total: ${total:.2f}\n"
                        f"Stock restante: {product.quantity_available}"
                    ),
                    "product_name": product.product_name,
                    "quantity": quantity,
                    "total": float(total),
                    "remaining_stock": product.quantity_available
                }

                # Si se solicita crear el registro en orders
                if create_order_record and user_id:
                    try:
                        from backend.services.order_service import OrderService
                        from backend.domain.order_schemas import OrderCreate, OrderDetailCreate
                        
                        order_service = OrderService(self.session_factory)
                        
                        order_data = OrderCreate(
                            user_id=user_id,
                            details=[
                                OrderDetailCreate(
                                    product_id=product.id,
                                    quantity=quantity
                                )
                            ],
                            shipping_address="Dirección no especificada (venta directa)",
                            notes=f"Venta directa desde chat: {product_name}"
                        )
                        
                        order, _ = await order_service.create_order(order_data)
                        result["order_id"] = order.id
                        result["message"] += f"\nPedido: #{str(order.id)[:8]}"
                        
                    except Exception as e:
                        self.logger.error(f"Error creando registro de orden: {e}")
                        # No fallamos la venta si no se puede crear el registro

                return result

        except asyncio.TimeoutError:
            self.logger.error(
                f"⏱️ Timeout procesando orden (>5s): {product_name} x{quantity}",
                exc_info=False
            )
            return {
                "success": False,
                "message": (
                    "Error: La base de datos no responde. "
                    "Por favor intenta nuevamente en unos momentos."
                ),
                "product_name": product_name,
                "quantity": quantity,
                "total": 0.0,
                "remaining_stock": 0
            }

        except OperationalError as e:
            self.logger.error(
                f"🚨 BD no disponible al procesar orden: {product_name} x{quantity}: {str(e)}",
                exc_info=True
            )
            return {
                "success": False,
                "message": (
                    "Error: No pudimos procesar tu pedido porque la base de datos "
                    "no está disponible. Intenta más tarde."
                ),
                "product_name": product_name,
                "quantity": quantity,
                "total": 0.0,
                "remaining_stock": 0
            }

        except SQLAlchemyError as e:
            self.logger.error(
                f"❌ Error de BD procesando orden {product_name} x{quantity}: {str(e)}",
                exc_info=True
            )
            return {
                "success": False,
                "message": (
                    "Error: No se pudo procesar tu pedido. "
                    "Por favor contacta a soporte."
                ),
                "product_name": product_name,
                "quantity": quantity,
                "total": 0.0,
                "remaining_stock": 0
            }

        except Exception as e:
            self.logger.error(
                f"💥 Error inesperado procesando orden {product_name} x{quantity}: {str(e)}",
                exc_info=True
            )
            return {
                "success": False,
                "message": (
                    "Error: Ocurrió un problema inesperado. "
                    "Nuestro equipo ha sido notificado."
                ),
                "product_name": product_name,
                "quantity": quantity,
                "total": 0.0,
                "remaining_stock": 0
            }

    async def restore_stock(
        self, 
        product_id: UUID, 
        quantity: int
    ) -> bool:
        """
        Restaura stock de un producto (útil para cancelaciones).
        
        Args:
            product_id: ID del producto
            quantity: Cantidad a restaurar
            
        Returns:
            True si se restauró exitosamente
        """
        try:
            async with self.session_factory() as session:
                product = await session.get(ProductStock, product_id)
                
                if not product:
                    self.logger.warning(f"Producto no encontrado para restaurar stock: {product_id}")
                    return False
                
                product.quantity_available += quantity
                await session.commit()
                
                self.logger.info(
                    f"Stock restaurado: {product.product_name} +{quantity} "
                    f"(nuevo total: {product.quantity_available})"
                )
                return True
                
        except Exception as e:
            self.logger.error(f"Error restaurando stock: {e}")
            return False

    async def update_stock(
        self, 
        product_id: UUID, 
        new_quantity: int
    ) -> bool:
        """
        Actualiza el stock de un producto a un valor específico.
        
        Args:
            product_id: ID del producto
            new_quantity: Nueva cantidad disponible
            
        Returns:
            True si se actualizó exitosamente
        """
        try:
            async with self.session_factory() as session:
                product = await session.get(ProductStock, product_id)
                
                if not product:
                    return False
                
                old_quantity = product.quantity_available
                product.quantity_available = new_quantity
                await session.commit()
                
                self.logger.info(
                    f"Stock actualizado: {product.product_name} "
                    f"{old_quantity} -> {new_quantity}"
                )
                return True
                
        except Exception as e:
            self.logger.error(f"Error actualizando stock: {e}")
            return False
