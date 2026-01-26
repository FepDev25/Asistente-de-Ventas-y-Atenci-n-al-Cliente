"""
Servicio de Gestión de Productos (Inventario).
se conecta el Agente con la Base de Datos Real.
"""
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from backend.database.models import ProductStock

class ProductService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        # Inyectamos la fábrica de sesiones para conectar a la DB
        self.session_factory = session_factory

    async def search_by_name(self, name: str) -> list[ProductStock]:
        """
        Busca productos por nombre o palabras clave.
        Usado por la Tool: 'consultar_inventario'.
        """
        from loguru import logger
        from sqlalchemy import or_
        logger.info(f"🗃️ ProductService: Buscando en DB '{name}'")
        
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
            
            logger.info(f"🗃️ Palabras de búsqueda: {search_words}")
            result = await session.execute(query)
            products = list(result.scalars().all())
            logger.info(f"🗃️ ProductService: Encontrados {len(products)} productos en DB")
            
            return products

    async def process_order(self, product_name: str, quantity: int) -> str:
        """
        Procesa la venta: Valida stock y lo descuenta.
        Usado por la Tool: 'crear_pedido'.
        """
        async with self.session_factory() as session:
            # buscar el producto exacto (o el más parecido)
            query = select(ProductStock).where(
                ProductStock.product_name.ilike(f"%{product_name}%")
            )
            result = await session.execute(query)
            product = result.scalars().first()

            # Validación 1: existencia
            if not product:
                return f"Error: No encontré el producto '{product_name}'."

            # Validación 2: stock suficiente
            if product.quantity_available < quantity:
                return f"Stock insuficiente. Solo quedan {product.quantity_available} unidades de {product.product_name}."

            # 2. Ejecutar la transacción (descontar)
            product.quantity_available -= quantity
            
            await session.commit()

            total = product.unit_cost * quantity
            return (
                f"¡VENTA EXITOSA!\n"
                f"Producto: {product.product_name}\n"
                f"Cantidad: {quantity}\n"
                f"Total: ${total:.2f}\n"
                f"Stock restante: {product.quantity_available}"
            )