"""
Script para poblar la base de datos con MUCHOS productos de zapatos.
Versión SIN imágenes (se agregarán después cuando Felipe configure el bucket).
"""
import asyncio
import os
from pathlib import Path
from decimal import Decimal

import dotenv

# Cargar variables de entorno
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    dotenv.load_dotenv(dotenv_path=env_path, override=True)
    print(f"✓ Cargado .env desde: {env_path}")
else:
    dotenv.load_dotenv(override=True)
    print("✓ Cargado .env desde ruta por defecto")

# Configurar SECRET_KEY si no existe
if not os.getenv("SECRET_KEY"):
    print("⚠️  SECRET_KEY no encontrada, usando valor por defecto")
    os.environ["SECRET_KEY"] = "super-secret-key-for-dev-only-2026"
    os.environ["JWT_SECRET"] = "super-secret-key-for-dev-only-2026"

from sqlalchemy import text
from backend.database.connection import get_engine
from backend.database.models.product_stock import ProductStock
from backend.database.session import get_session_factory


# CATÁLOGO COMPLETO DE PRODUCTOS (30+ productos)
# Nota: Las imágenes se agregarán después cuando Felipe configure el bucket
PRODUCTOS_CATALOGO = [
    # NIKE (10 productos) 
    {
        "product_id": "NIKE-001",
        "product_name": "Nike Air Zoom Pegasus 40",
        "product_sku": "NIKE-PEGASUS-40-BLK",
        "supplier_id": "NIKE-DIST-EC",
        "supplier_name": "Nike Ecuador Distribuidor Oficial",
        "quantity_available": 15,
        "unit_cost": 120.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Zapatillas de running ideales para asfalto. Amortiguación Nike Air Zoom reactiva. Malla transpirable."
    },
    {
        "product_id": "NIKE-002",
        "product_name": "Nike Air Max 90",
        "product_sku": "NIKE-MAX-90-WHT",
        "supplier_id": "NIKE-DIST-EC",
        "supplier_name": "Nike Ecuador Distribuidor Oficial",
        "quantity_available": 20,
        "unit_cost": 130.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Estilo clásico con amortiguación Air Max visible. Diseño icónico para uso diario."
    },
    {
        "product_id": "NIKE-003",
        "product_name": "Nike React Infinity Run 4",
        "product_sku": "NIKE-REACT-INF4",
        "supplier_id": "NIKE-DIST-EC",
        "supplier_name": "Nike Ecuador Distribuidor Oficial",
        "quantity_available": 12,
        "unit_cost": 145.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Máxima amortiguación React para largas distancias. Reduce lesiones."
    },
    {
        "product_id": "NIKE-004",
        "product_name": "Nike ZoomX Vaporfly 3",
        "product_sku": "NIKE-VAPORFLY-3",
        "supplier_id": "NIKE-DIST-EC",
        "supplier_name": "Nike Ecuador Distribuidor Oficial",
        "quantity_available": 8,
        "unit_cost": 250.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Zapatillas de competición élite. ZoomX ultra ligero. Placa de carbono."
    },
    {
        "product_id": "NIKE-005",
        "product_name": "Nike Court Vision Low",
        "product_sku": "NIKE-COURT-LOW",
        "supplier_id": "NIKE-DIST-EC",
        "supplier_name": "Nike Ecuador Distribuidor Oficial",
        "quantity_available": 25,
        "unit_cost": 75.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Estilo basketball clásico para uso casual. Cuero sintético duradero."
    },
    {
        "product_id": "NIKE-006",
        "product_name": "Nike Air Force 1 '07",
        "product_sku": "NIKE-AF1-WHITE",
        "supplier_id": "NIKE-DIST-EC",
        "supplier_name": "Nike Ecuador Distribuidor Oficial",
        "quantity_available": 35,
        "unit_cost": 110.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Icono urbano. Diseño clásico de 1982. Cuero premium blanco."
    },
    {
        "product_id": "NIKE-007",
        "product_name": "Nike Revolution 7",
        "product_sku": "NIKE-REV-7",
        "supplier_id": "NIKE-DIST-EC",
        "supplier_name": "Nike Ecuador Distribuidor Oficial",
        "quantity_available": 30,
        "unit_cost": 65.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Running económico. Perfecto para iniciarse. Amortiguación básica."
    },
    {
        "product_id": "NIKE-008",
        "product_name": "Nike Downshifter 12",
        "product_sku": "NIKE-DOWN-12",
        "supplier_id": "NIKE-DIST-EC",
        "supplier_name": "Nike Ecuador Distribuidor Oficial",
        "quantity_available": 28,
        "unit_cost": 70.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Running para entrenamientos diarios. Comodidad y durabilidad."
    },
    {
        "product_id": "NIKE-009",
        "product_name": "Nike Metcon 9",
        "product_sku": "NIKE-METCON-9",
        "supplier_id": "NIKE-DIST-EC",
        "supplier_name": "Nike Ecuador Distribuidor Oficial",
        "quantity_available": 10,
        "unit_cost": 140.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Zapatillas de CrossFit y entrenamiento funcional. Estabilidad máxima."
    },
    {
        "product_id": "NIKE-010",
        "product_name": "Nike Blazer Mid '77",
        "product_sku": "NIKE-BLAZER-77",
        "supplier_id": "NIKE-DIST-EC",
        "supplier_name": "Nike Ecuador Distribuidor Oficial",
        "quantity_available": 18,
        "unit_cost": 105.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Estilo retro basketball. Diseño vintage. Perfecto para streetwear."
    },

    # ADIDAS (8 productos)
    {
        "product_id": "ADIDAS-001",
        "product_name": "Adidas Ultraboost Light",
        "product_sku": "ADIDAS-UB-LIGHT",
        "supplier_id": "ADIDAS-DIST-EC",
        "supplier_name": "Adidas Ecuador Distribuidor Oficial",
        "quantity_available": 18,
        "unit_cost": 180.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Máximo retorno de energía con Boost Light. Tejido Primeknit transpirable."
    },
    {
        "product_id": "ADIDAS-002",
        "product_name": "Adidas Supernova 3",
        "product_sku": "ADIDAS-SUPERNOVA-3",
        "supplier_id": "ADIDAS-DIST-EC",
        "supplier_name": "Adidas Ecuador Distribuidor Oficial",
        "quantity_available": 22,
        "unit_cost": 110.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Running de alta calidad para entrenamientos diarios. Amortiguación Dreamstrike+."
    },
    {
        "product_id": "ADIDAS-003",
        "product_name": "Adidas Stan Smith",
        "product_sku": "ADIDAS-STAN-SMITH",
        "supplier_id": "ADIDAS-DIST-EC",
        "supplier_name": "Adidas Ecuador Distribuidor Oficial",
        "quantity_available": 40,
        "unit_cost": 85.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Zapatillas icónicas de cuero blanco. Estilo minimalista atemporal."
    },
    {
        "product_id": "ADIDAS-004",
        "product_name": "Adidas Terrex Swift R3 GTX",
        "product_sku": "ADIDAS-TERREX-R3",
        "supplier_id": "ADIDAS-DIST-EC",
        "supplier_name": "Adidas Ecuador Distribuidor Oficial",
        "quantity_available": 12,
        "unit_cost": 160.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Zapatillas de trekking impermeables Gore-Tex. Tracción Continental."
    },
    {
        "product_id": "ADIDAS-005",
        "product_name": "Adidas Samba OG",
        "product_sku": "ADIDAS-SAMBA-OG",
        "supplier_id": "ADIDAS-DIST-EC",
        "supplier_name": "Adidas Ecuador Distribuidor Oficial",
        "quantity_available": 35,
        "unit_cost": 100.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Clásico retro de fútbol sala. Cuero suave premium. Suela de goma gum."
    },
    {
        "product_id": "ADIDAS-006",
        "product_name": "Adidas Forum Low",
        "product_sku": "ADIDAS-FORUM-LOW",
        "supplier_id": "ADIDAS-DIST-EC",
        "supplier_name": "Adidas Ecuador Distribuidor Oficial",
        "quantity_available": 20,
        "unit_cost": 95.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Basketball retro de los 80s. Estilo urbano streetwear."
    },
    {
        "product_id": "ADIDAS-007",
        "product_name": "Adidas Duramo SL",
        "product_sku": "ADIDAS-DURAMO-SL",
        "supplier_id": "ADIDAS-DIST-EC",
        "supplier_name": "Adidas Ecuador Distribuidor Oficial",
        "quantity_available": 25,
        "unit_cost": 60.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Running económico. Ideal para iniciarse. Comodidad básica."
    },
    {
        "product_id": "ADIDAS-008",
        "product_name": "Adidas Gazelle",
        "product_sku": "ADIDAS-GAZELLE",
        "supplier_id": "ADIDAS-DIST-EC",
        "supplier_name": "Adidas Ecuador Distribuidor Oficial",
        "quantity_available": 30,
        "unit_cost": 90.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Clásico de ante. Diseño retro icónico. Estilo casual elegante."
    },

    # PUMA (6 productos)
    {
        "product_id": "PUMA-001",
        "product_name": "Puma Velocity Nitro 2",
        "product_sku": "PUMA-VEL-NITRO2",
        "supplier_id": "PUMA-DIST-EC",
        "supplier_name": "Puma Ecuador Distribuidor Oficial",
        "quantity_available": 20,
        "unit_cost": 95.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Excelente relación calidad-precio para running. Nitro Foam reactivo."
    },
    {
        "product_id": "PUMA-002",
        "product_name": "Puma Deviate Nitro Elite 2",
        "product_sku": "PUMA-DEVIATE-E2",
        "supplier_id": "PUMA-DIST-EC",
        "supplier_name": "Puma Ecuador Distribuidor Oficial",
        "quantity_available": 7,
        "unit_cost": 220.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Zapatillas de competición élite. Placa de carbono PWRPLATE."
    },
    {
        "product_id": "PUMA-003",
        "product_name": "Puma Suede Classic XXI",
        "product_sku": "PUMA-SUEDE-XXI",
        "supplier_id": "PUMA-DIST-EC",
        "supplier_name": "Puma Ecuador Distribuidor Oficial",
        "quantity_available": 32,
        "unit_cost": 70.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Icono del streetwear. Ante premium suave. Diseño retro actualizado."
    },
    {
        "product_id": "PUMA-004",
        "product_name": "Puma RS-X Efekt",
        "product_sku": "PUMA-RSX-EFEKT",
        "supplier_id": "PUMA-DIST-EC",
        "supplier_name": "Puma Ecuador Distribuidor Oficial",
        "quantity_available": 15,
        "unit_cost": 115.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Estilo chunky retro-futurista. Colores vibrantes. Suela gruesa RS."
    },
    {
        "product_id": "PUMA-005",
        "product_name": "Puma Caven 2.0",
        "product_sku": "PUMA-CAVEN-2",
        "supplier_id": "PUMA-DIST-EC",
        "supplier_name": "Puma Ecuador Distribuidor Oficial",
        "quantity_available": 28,
        "unit_cost": 65.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Estilo casual urbano. Inspiración retro. Uso diario cómodo."
    },
    {
        "product_id": "PUMA-006",
        "product_name": "Puma Clyde All-Pro",
        "product_sku": "PUMA-CLYDE-PRO",
        "supplier_id": "PUMA-DIST-EC",
        "supplier_name": "Puma Ecuador Distribuidor Oficial",
        "quantity_available": 14,
        "unit_cost": 125.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Basketball performance. Diseño moderno. Tecnología ProFoam+."
    },

    # NEW BALANCE (4 productos)
    {
        "product_id": "NB-001",
        "product_name": "New Balance Fresh Foam X 1080v13",
        "product_sku": "NB-1080V13",
        "supplier_id": "NB-DIST-EC",
        "supplier_name": "New Balance Ecuador",
        "quantity_available": 14,
        "unit_cost": 160.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Máxima amortiguación Fresh Foam X. Perfectas para largas distancias."
    },
    {
        "product_id": "NB-002",
        "product_name": "New Balance 574 Core",
        "product_sku": "NB-574-CORE",
        "supplier_id": "NB-DIST-EC",
        "supplier_name": "New Balance Ecuador",
        "quantity_available": 45,
        "unit_cost": 80.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Clásico atemporal lifestyle. Ante y malla. Suela ENCAP duradera."
    },
    {
        "product_id": "NB-003",
        "product_name": "New Balance FuelCell SuperComp Elite v4",
        "product_sku": "NB-SCÉLITE-V4",
        "supplier_id": "NB-DIST-EC",
        "supplier_name": "New Balance Ecuador",
        "quantity_available": 5,
        "unit_cost": 275.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Zapatillas de competición profesional. Placa de carbono doble."
    },
    {
        "product_id": "NB-004",
        "product_name": "New Balance 327",
        "product_sku": "NB-327",
        "supplier_id": "NB-DIST-EC",
        "supplier_name": "New Balance Ecuador",
        "quantity_available": 38,
        "unit_cost": 95.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Diseño retro-moderno. Estilo años 70 actualizado. Casual elegante."
    },

    # ACCESORIOS (4 productos) 
    {
        "product_id": "ACC-001",
        "product_name": "Calcetines Nike Crew Performance (Pack x3)",
        "product_sku": "NIKE-CREW-3PACK",
        "supplier_id": "NIKE-DIST-EC",
        "supplier_name": "Nike Ecuador Distribuidor Oficial",
        "quantity_available": 60,
        "unit_cost": 15.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Calcetines deportivos Dri-FIT. Refuerzo en talón y punta. Pack de 3."
    },
    {
        "product_id": "ACC-002",
        "product_name": "Plantillas Ortopédicas Dr. Scholl's Sport",
        "product_sku": "DRSCHOLL-SPORT",
        "supplier_id": "DRSCHOLL-EC",
        "supplier_name": "Dr. Scholl's Ecuador",
        "quantity_available": 40,
        "unit_cost": 25.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Plantillas con soporte de arco. Amortiguación Shock Guard."
    },
    {
        "product_id": "ACC-003",
        "product_name": "Spray Impermeabilizante Crep Protect",
        "product_sku": "CREP-PROTECT-200ML",
        "supplier_id": "CREP-EC",
        "supplier_name": "Crep Protect Ecuador",
        "quantity_available": 50,
        "unit_cost": 18.00,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Protección contra agua y manchas. Extiende la vida útil."
    },
    {
        "product_id": "ACC-004",
        "product_name": "Cordones de Repuesto Premium (Pack x2)",
        "product_sku": "LACES-PREMIUM-2",
        "supplier_id": "GENERIC-EC",
        "supplier_name": "Accesorios Genéricos",
        "quantity_available": 80,
        "unit_cost": 8.00,
        "warehouse_location": "QUITO-NORTE",
        "description": "Cordones de alta calidad. Varios colores. Pack de 2 pares."
    },
]


async def poblar_catalogo():
    """Inserta todos los productos del catálogo en la base de datos."""
    print("\n Poblando catálogo con productos...")
    print("   (Las imágenes se agregarán después cuando Felipe configure el bucket)")
    
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        # Verificar cuántos productos hay
        result = await session.execute(text("SELECT COUNT(*) FROM product_stocks"))
        count_antes = result.scalar()
        print(f"   Productos actuales en BD: {count_antes}")
        
        productos_nuevos = 0
        
        for prod in PRODUCTOS_CATALOGO:
            # Verificar si el producto ya existe por product_id
            result = await session.execute(
                text("SELECT COUNT(*) FROM product_stocks WHERE product_id = :pid"),
                {"pid": prod["product_id"]}
            )
            existe = result.scalar() > 0
            
            if not existe:
                # Crear el producto usando el modelo ORM
                nuevo_producto = ProductStock(
                    product_id=prod["product_id"],
                    product_name=prod["product_name"],
                    product_sku=prod["product_sku"],
                    supplier_id=prod["supplier_id"],
                    supplier_name=prod["supplier_name"],
                    quantity_available=prod["quantity_available"],
                    unit_cost=Decimal(str(prod["unit_cost"])),
                    total_value=Decimal(str(prod["unit_cost"] * prod["quantity_available"])),
                    warehouse_location=prod["warehouse_location"],
                    stock_status=1,  # En stock
                    shelf_location=prod.get("description", ""),  # Usamos shelf_location para descripción
                    batch_number="LOTE-2026-B"
                )
                session.add(nuevo_producto)
                
                productos_nuevos += 1
                print(f"   ✓ {prod['product_name']}")
        
        await session.commit()
        
        # Verificar el total final
        result = await session.execute(text("SELECT COUNT(*) FROM product_stocks"))
        count_despues = result.scalar()
        
        print(f"\n Resumen:")
        print(f"   Productos antes: {count_antes}")
        print(f"   Productos agregados: {productos_nuevos}")
        print(f"   Total productos ahora: {count_despues}")


async def main():
    """Función principal."""
    print("=" * 70)
    print(" INICIALIZACIÓN DE CATÁLOGO COMPLETO DE PRODUCTOS")
    print("=" * 70)
    
    await poblar_catalogo()
    
    print("\n ¡Catálogo completo cargado exitosamente!")



if __name__ == "__main__":
    asyncio.run(main())
