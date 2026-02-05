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
    Este servicio se mantiene para compatibilidad.
    """
    
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        # Inyectamos la fábrica de sesiones para conectar a la DB
        self.session_factory = session_factory
        self.logger = get_logger("product_service")

    async def get_all_products(self, limit: int = 50) -> list[ProductStock]:
        """
        Obtiene todos los productos activos.
        
        Args:
            limit: Número máximo de productos a retornar
            
        Returns:
            Lista de productos activos
        """
        try:
            async with self.session_factory() as session:
                query = (
                    select(ProductStock)
                    .where(ProductStock.is_active == True)
                    .limit(limit)
                )
                
                result = await asyncio.wait_for(
                    session.execute(query),
                    timeout=5.0
                )
                
                products = list(result.scalars().all())
                self.logger.info(f"🗃️ ProductService: Listados {len(products)} productos")
                return products
                
        except Exception as e:
            self.logger.error(f"Error listando productos: {e}")
            return []

    async def search_by_name(self, name: str) -> list[ProductStock]:
        """
        Busca productos por nombre o palabras clave con manejo robusto de errores.

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
        """
        try:
            async with self.session_factory() as session:
                return await session.get(ProductStock, product_id)
                
        except Exception as e:
            self.logger.error(f"Error consultando producto {product_id}: {e}")
            return None

    async def get_product_by_barcode(
        self, 
        barcode: str
    ) -> Optional[ProductStock]:
        """
        Obtiene un producto por su código de barras (EAN/UPC).
        
        Este método es CRÍTICO para la integración con el Agente 2.
        El Agente 2 envía códigos de barras que usamos para buscar productos.
        
        Args:
            barcode: Código de barras EAN/UPC
            
        Returns:
            El producto encontrado o None
        """
        try:
            async with self.session_factory() as session:
                query = (
                    select(ProductStock)
                    .where(
                        ProductStock.barcode == barcode,
                        ProductStock.is_active == True
                    )
                )
                result = await session.execute(query)
                product = result.scalar_one_or_none()
                
                if product:
                    self.logger.info(
                        f"✅ Producto encontrado por barcode {barcode}: {product.product_name}"
                    )
                else:
                    self.logger.warning(
                        f"❌ Producto no encontrado con barcode: {barcode}"
                    )
                
                return product
                
        except Exception as e:
            self.logger.error(f"Error consultando producto por barcode '{barcode}': {e}")
            return None

    async def get_products_by_barcodes(
        self, 
        barcodes: List[str]
    ) -> List[ProductStock]:
        """
        Obtiene múltiples productos por sus códigos de barras.
        
        Usado cuando el Agente 2 envía varios productos en el guión.
        
        Args:
            barcodes: Lista de códigos de barras
            
        Returns:
            Lista de productos encontrados (puede ser menor que la entrada)
        """
        if not barcodes:
            return []
        
        try:
            async with self.session_factory() as session:
                query = (
                    select(ProductStock)
                    .where(
                        ProductStock.barcode.in_(barcodes),
                        ProductStock.is_active == True
                    )
                )
                result = await session.execute(query)
                products = list(result.scalars().all())
                
                # Log de resultados
                found_barcodes = {p.barcode for p in products if p.barcode}
                missing_barcodes = set(barcodes) - found_barcodes
                
                self.logger.info(
                    f"🗃️ Búsqueda por barcodes: {len(products)}/{len(barcodes)} encontrados"
                )
                if missing_barcodes:
                    self.logger.warning(f"❌ No encontrados: {missing_barcodes}")
                
                return products
                
        except Exception as e:
            self.logger.error(f"Error consultando productos por barcodes: {e}")
            return []

    async def get_product_by_name(
        self, 
        product_name: str
    ) -> Optional[ProductStock]:
        """
        Obtiene un producto por nombre exacto o parcial.
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

    async def get_products_on_sale(
        self,
        limit: int = 20
    ) -> List[ProductStock]:
        """
        Obtiene productos en oferta/promoción.
        
        Args:
            limit: Máximo de resultados
            
        Returns:
            Lista de productos con descuentos activos
        """
        from datetime import date as dt_date
        
        try:
            async with self.session_factory() as session:
                query = (
                    select(ProductStock)
                    .where(
                        ProductStock.is_on_sale == True,
                        ProductStock.is_active == True
                    )
                    .limit(limit)
                )
                result = await session.execute(query)
                products = list(result.scalars().all())
                
                # Filtrar por fecha de validez
                valid_products = []
                for p in products:
                    if p.promotion_valid_until is None or p.promotion_valid_until >= dt_date.today():
                        valid_products.append(p)
                
                self.logger.info(f"🎉 Productos en oferta encontrados: {len(valid_products)}")
                return valid_products
                
        except Exception as e:
            self.logger.error(f"Error consultando productos en oferta: {e}")
            return []

    async def check_stock(
        self, 
        product_id: UUID, 
        quantity: int
    ) -> tuple[bool, int, str]:
        """
        Verifica si hay stock suficiente para un producto.
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

    async def restore_stock(
        self, 
        product_id: UUID, 
        quantity: int
    ) -> bool:
        """
        Restaura stock de un producto (útil para cancelaciones).
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
