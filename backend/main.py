"""
Punto de Entrada de la Aplicación (Main).
Arranca el servidor web (FastAPI) y la API GraphQL.
"""
import os
import sys
from pathlib import Path

# CRÍTICO: Establecer credenciales ANTES de cualquier import de Google
# Cargar dotenv primero para leer el .env
import dotenv

# Cargar .env desde backend/ (donde está el archivo)
env_path = Path(__file__).parent / ".env"
dotenv.load_dotenv(dotenv_path=env_path)

# Leer la ruta de credenciales del .env directamente
credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if credentials_path:
    # Establecer la variable de entorno para que google.auth.default() la encuentre
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
    print(f"✅ Credenciales configuradas: {credentials_path}", file=sys.stderr)
else:
    print(f"⚠️  GOOGLE_APPLICATION_CREDENTIALS no encontrado en {env_path}", file=sys.stderr)
    print(f"⚠️  Variables de entorno cargadas: {list(os.environ.keys())[:10]}", file=sys.stderr)

# Ahora sí podemos importar el resto
import strawberry
import uvicorn
from aioinject.ext.strawberry import AioInjectExtension
from fastapi import FastAPI
from loguru import logger
from strawberry.fastapi import GraphQLRouter
from backend.config import get_business_settings

# Importamos tu esquema limpio
from backend.api.graphql.queries import BusinessQuery
from backend.container import create_business_container

def create_app() -> FastAPI:
    """Crea y configura la aplicación FastAPI."""
    
    # 1. Configuración Básica
    app = FastAPI(
        title="Agente de Ventas API",
        description="API GraphQL para el Asistente de Ventas con IA (Alex).",
        version="1.0.0",
    )

    # 2. Iniciar el Contenedor de Servicios
    container = create_business_container()
    logger.info("Contenedor de servicios iniciado correctamente.")

    # 3. Configurar GraphQL
    # Creamos el esquema con tus Queries
    schema = strawberry.Schema(
        query=BusinessQuery,
        extensions=[AioInjectExtension(container=container)], # Conecta la inyección de dependencias
    )

    # Creamos la ruta /graphql
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")

    @app.get("/")
    async def root():
        """Endpoint de bienvenida."""
        return {
            "mensaje": "Bienvenido al Backend del Agente de Ventas",
            "playground": "Ve a /graphql para probar el chat",
            "docs": "/docs"
        }

    return app

# Bloque de ejecución principal
if __name__ == "__main__":
    logger.info("Arrancando servidor en http://0.0.0.0:8000")
    
    # Ejecuta uvicorn directamente
    uvicorn.run(
        "backend.main:create_app", # Apunta a la función factoría
        host="0.0.0.0",
        port=8000,
        reload=True, # Reload=True es vital para desarrollar (recarga si cambias código)
        factory=True 
    )