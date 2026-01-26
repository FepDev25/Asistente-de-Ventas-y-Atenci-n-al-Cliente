"""
Esquemas Pydantic para serializar respuestas de la API.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class ProductStockSchema(BaseModel):
    """Lo que el Frontend/Chat recibe."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    product_name: str
    
    # Datos de Venta
    quantity_available: int
    unit_cost: Decimal
    warehouse_location: str
    
    # Extras
    batch_number: str | None = None # Keywords
    shelf_location: str | None = None # Descripción
    
    is_active: bool