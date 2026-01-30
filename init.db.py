import asyncio
import dotenv
from sqlalchemy import text
from decimal import Decimal
from backend.database.connection import get_engine
from backend.database.models.product_stock import Base, ProductStock 
from backend.database.models.user_model import Base, User 
from backend.database.session import get_session_factory

from passlib.context import CryptContext
# Cargar explícitamente las variables de entorno
dotenv.load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

PRODUCTOS_INICIALES = [
    {
        "product_id": "NIKE-001",
        "product_name": "Nike Air Zoom Pegasus 40",
        "product_sku": "NIKE-PEGASUS-40",
        "supplier_id": "NIKE-DIST-001",
        "supplier_name": "Nike Distribuidor Ecuador",
        "quantity_available": 10,
        "unit_cost": 120.00,
        "stock_status": 1, # 1 = En Stock
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Zapatillas de running ideales para asfalto, amortiguación reactiva."
    },
    {
        "product_id": "ADIDAS-001", 
        "product_name": "Adidas Ultraboost Light",
        "product_sku": "ADIDAS-UB-LIGHT",
        "supplier_id": "ADIDAS-DIST-001",
        "supplier_name": "Adidas Distribuidor Ecuador",
        "quantity_available": 5,
        "unit_cost": 180.00,
        "stock_status": 1,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Máximo retorno de energía, tejido Primeknit transpirable."
    },
    {
        "product_id": "PUMA-001",
        "product_name": "Puma Velocity Nitro 2",
        "product_sku": "PUMA-VEL-NITRO2",
        "supplier_id": "PUMA-DIST-001", 
        "supplier_name": "Puma Distribuidor Ecuador",
        "quantity_available": 20,
        "unit_cost": 95.50,
        "stock_status": 1,
        "warehouse_location": "QUITO-NORTE",
        "description": "Opción calidad-precio para entrenamiento diario."
    },
    {
        "product_id": "NIKE-ACC-001",
        "product_name": "Calcetines Nike Crew (Pack x3)",
        "product_sku": "NIKE-CREW-3PACK",
        "supplier_id": "NIKE-DIST-001",
        "supplier_name": "Nike Distribuidor Ecuador", 
        "quantity_available": 50,
        "unit_cost": 15.00,
        "stock_status": 1,
        "warehouse_location": "CUENCA-CENTRO",
        "description": "Calcetines deportivos de algodón con refuerzo en talón."
    }
]

USUARIOS_INICIALES = [
    {
        "username": "admin",
        "email": "admin@ventas.com",
        "full_name": "Administrador General",
        "password": "admin123",
        "role": 1
    },
    {
        "username": "Cliente1",
        "email": "cliente1@cliente.com",
        "full_name": "Carlos Cliente",
        "password": "cliente123",
        "role": 2
    }
]

async def init_database():
    print("Iniciando configuración de Base de Datos...")
    
    # 1. Obtener el motor de conexión
    engine = get_engine()
    
    # 2. Crear las tablas
    async with engine.begin() as conn:
        # borrar tablas viejas para empezar limpio
        # await conn.run_sync(Base.metadata.drop_all) 
        
        print("Creando tablas en Postgres...")
        await conn.run_sync(Base.metadata.create_all)
    
    # 3. Insertar datos
    session_factory = get_session_factory()
    async with session_factory() as session:
        # Verificamos si ya hay datos
        result = await session.execute(text("SELECT count(*) FROM product_stocks"))
        count = result.scalar()
        
        if count == 0:
            print("Base de datos vacía. Insertando inventario inicial...")
            for prod in PRODUCTOS_INICIALES:
                nuevo_producto = ProductStock(
                    product_id=prod["product_id"],
                    product_name=prod["product_name"],
                    product_sku=prod["product_sku"],
                    supplier_id=prod["supplier_id"],
                    supplier_name=prod["supplier_name"], 
                    quantity_available=prod["quantity_available"],
                    unit_cost=Decimal(str(prod["unit_cost"])),
                    total_value=Decimal(str(prod["unit_cost"] * prod["quantity_available"])),
                    stock_status=prod["stock_status"],
                    warehouse_location=prod["warehouse_location"],
                    batch_number="LOTE-2026-A" 
                )
                session.add(nuevo_producto)
            
            await session.commit()
            print("Inventario cargado exitosamente.")
        else:
            print(f"La base de datos ya tiene {count} productos. No se insertó nada.")
    async with session_factory() as session:
        result = await session.execute(text("SELECT count(*) FROM users"))
        count = result.scalar()

        if count == 0:
            print("Insertando usuarios iniciales...")
            for usr in USUARIOS_INICIALES:
                nuevo_usuario = User(
                    username=usr["username"],
                    email=usr["email"],
                    full_name=usr["full_name"],
                    password_hash=hash_password(usr["password"]),
                    role=usr["role"],
                    is_active=True
                )
                session.add(nuevo_usuario)

            await session.commit()
            print("Usuarios creados exitosamente.")
        else:
            print(f"Ya existen {count} usuarios. No se insertó nada.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_database())