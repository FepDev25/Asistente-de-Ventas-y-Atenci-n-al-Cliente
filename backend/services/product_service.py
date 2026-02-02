"""
Servicio de Gestión de Productos (Inventario).
se conecta el Agente con la Base de Datos Real.
"""
import asyncio
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from loguru import logger
from backend.database.models import ProductStock

class ProductService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        # Inyectamos la fábrica de sesiones para conectar a la DB
        self.session_factory = session_factory

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

        logger.info(f"🗃️ ProductService: Buscando en DB '{name}'")

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

                logger.info(f"🗃️ Palabras de búsqueda: {search_words}")

                # Ejecutar query con timeout
                result = await asyncio.wait_for(
                    session.execute(query),
                    timeout=5.0  # 5 segundos máximo
                )

                products = list(result.scalars().all())
                logger.info(f"🗃️ ProductService: Encontrados {len(products)} productos en DB")

                return products

        except asyncio.TimeoutError:
            logger.error(
                f"⏱️ Timeout buscando productos (>5s): '{name}'",
                exc_info=False
            )
            return []

        except OperationalError as e:
            logger.error(
                f"🚨 Base de datos no disponible al buscar '{name}': {str(e)}",
                exc_info=True
            )
            return []

        except SQLAlchemyError as e:
            logger.error(
                f"❌ Error de BD al buscar '{name}': {str(e)}",
                exc_info=True
            )
            return []

        except Exception as e:
            logger.error(
                f"💥 Error inesperado buscando '{name}': {str(e)}",
                exc_info=True
            )
            return []

    async def process_order(self, product_name: str, quantity: int) -> str:
        """
        Procesa la venta: Valida stock y lo descuenta con manejo robusto de errores.

        Usado por la Tool: 'crear_pedido'.

        Error Handling:
        - Producto no encontrado → Mensaje claro
        - Stock insuficiente → Sugiere cantidad disponible
        - Timeout de BD → Mensaje de reintentar
        - Error de commit → Rollback automático

        Returns:
            Mensaje de éxito o error amigable para el usuario
        """
        try:
            async with self.session_factory() as session:
                # Buscar el producto exacto (o el más parecido)
                query = select(ProductStock).where(
                    ProductStock.product_name.ilike(f"%{product_name}%")
                )

                # Ejecutar query con timeout
                result = await asyncio.wait_for(
                    session.execute(query),
                    timeout=5.0
                )

                product = result.scalars().first()

                # Validación 1: existencia
                if not product:
                    logger.warning(f"Producto no encontrado: '{product_name}'")
                    return f"Error: No encontré el producto '{product_name}'."

                # Validación 2: stock suficiente
                if product.quantity_available < quantity:
                    logger.warning(
                        f"Stock insuficiente para '{product.product_name}': "
                        f"solicitado={quantity}, disponible={product.quantity_available}"
                    )
                    return (
                        f"Stock insuficiente. Solo quedan {product.quantity_available} "
                        f"unidades de {product.product_name}."
                    )

                # Ejecutar la transacción (descontar)
                product.quantity_available -= quantity

                # Commit con timeout
                await asyncio.wait_for(
                    session.commit(),
                    timeout=5.0
                )

                total = product.unit_cost * quantity

                logger.info(
                    f"✅ Orden procesada: {product.product_name} "
                    f"x{quantity} = ${total:.2f}"
                )

                return (
                    f"¡VENTA EXITOSA!\n"
                    f"Producto: {product.product_name}\n"
                    f"Cantidad: {quantity}\n"
                    f"Total: ${total:.2f}\n"
                    f"Stock restante: {product.quantity_available}"
                )

        except asyncio.TimeoutError:
            logger.error(
                f"⏱️ Timeout procesando orden (>5s): {product_name} x{quantity}",
                exc_info=False
            )
            return (
                "Error: La base de datos no responde. "
                "Por favor intenta nuevamente en unos momentos."
            )

        except OperationalError as e:
            logger.error(
                f"🚨 BD no disponible al procesar orden: {product_name} x{quantity}: {str(e)}",
                exc_info=True
            )
            # El rollback es automático si no se hace commit
            return (
                "Error: No pudimos procesar tu pedido porque la base de datos "
                "no está disponible. Intenta más tarde."
            )

        except SQLAlchemyError as e:
            logger.error(
                f"❌ Error de BD procesando orden {product_name} x{quantity}: {str(e)}",
                exc_info=True
            )
            # El rollback es automático
            return (
                "Error: No se pudo procesar tu pedido. "
                "Por favor contacta a soporte."
            )

        except Exception as e:
            logger.error(
                f"💥 Error inesperado procesando orden {product_name} x{quantity}: {str(e)}",
                exc_info=True
            )
            return (
                "Error: Ocurrió un problema inesperado. "
                "Nuestro equipo ha sido notificado."
            )