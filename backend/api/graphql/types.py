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
    """
    La respuesta de Alex (El Agente).

    El campo 'error' indica si hubo algún problema:
    - None: Respuesta exitosa
    - "timeout": LLM o BD tardó demasiado
    - "internal_error": Error técnico general
    - "service_unavailable": Servicio no disponible
    """
    answer: str
    query: str
    error: str | None = None  # Nuevo: indica tipo de error si existe