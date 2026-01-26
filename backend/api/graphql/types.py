"""
Tipos de datos GraphQL (Esquemas).
Define qué datos puede pedir el Frontend.
"""
from datetime import datetime
from decimal import Decimal
from uuid import UUID
import strawberry

@strawberry.type
class ProductStockType:
    """Lo que ve el cliente sobre un zapato."""
    id: UUID
    product_name: str
    
    # Precios y Stock
    unit_cost: Decimal
    quantity_available: int
    stock_status: int  # 1=Disponible, 0=Agotado
    
    # Ubicación (útil para envíos)
    warehouse_location: str
    
    # Extras (Descripción y Keywords)
    # Mapeamos 'shelf_location' a descripción para aprovechar el campo
    shelf_location: str | None 
    batch_number: str | None   # Keywords

@strawberry.type
class SemanticSearchResponse:
    """La respuesta de Alex (El Agente)."""
    answer: str
    # En versiones complejas aquí iría una lista de productos estructurada,
    # para la demo, Alex ya incluye los productos en el texto 'answer'.
    query: str