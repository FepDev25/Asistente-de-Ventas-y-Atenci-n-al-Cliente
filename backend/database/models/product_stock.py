"""
Modelo de Base de Datos: ProductStock.
Modelo completo para la Demo de Ventas.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Numeric, SmallInteger, String, text, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class ProductStock(Base):
    __tablename__ = "product_stocks"
    __table_args__ = {"schema": "public"}

    # ID y Tiempos
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=text("now()"))
    
    # Información Clave del Producto
    product_id: Mapped[str] = mapped_column(String(255), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_sku: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Información del Proveedor
    supplier_id: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Campos útiles para el Vendedor (Descripción y Palabras Clave)
    batch_number: Mapped[str | None] = mapped_column(String(255), nullable=True) 
    
    # Descripción (Si no quieres agregar columna nueva, usa Text o reutiliza shelf_location)
    # Por ahora asumimos que shelf_location guarda la "Descripción corta"
    shelf_location: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Precios y Cantidades (Lo importante)
    quantity_available: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, server_default=text("0")
    )
    unit_cost: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default=text("0.0")
    )
    total_value: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, server_default=text("0.0")
    )

    # Ubicación (Para envíos)
    warehouse_location: Mapped[str] = mapped_column(
        String(255), nullable=False, server_default="'CUENCA-MAIN'"
    )
    
    # Estado (1=Activo, 0=Inactivo)
    stock_status: Mapped[int] = mapped_column(SmallInteger, server_default=text("1"))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default=text("true"))

    def __repr__(self) -> str:
        return f"<ProductStock(id={self.id}, name={self.product_name}, qty={self.quantity_available})>"