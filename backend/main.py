"""
Punto de Entrada de la Aplicación (Main).
Arranca el servidor web (FastAPI) y la API GraphQL.
"""
import os
import sys
from pathlib import Path

# Cargar dotenv primero para leer el .env
import dotenv

dotenv.load_dotenv(dotenv.find_dotenv())

import strawberry
import uvicorn
from aioinject.ext.strawberry import AioInjectExtension
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from loguru import logger
from strawberry.fastapi import GraphQLRouter

# Rate Limiting
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from backend.config import get_business_settings
from backend.config.rate_limit_config import limiter, RateLimitConfig
from backend.api.endPoints.auth.auth import router as auth_router
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
    
    # 2. Configurar Rate Limiting
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)
    
    # Handler personalizado para rate limit exceeded
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Has excedido el límite de requests. Por favor espera un momento.",
                "retry_after": "60 seconds"
            },
            headers={"Retry-After": "60"}
        )

    # 3. Iniciar el Contenedor de Servicios
    container = create_business_container()
    logger.info("Contenedor de servicios iniciado correctamente.")

    # 4. Configurar GraphQL
    schema = strawberry.Schema(
        query=BusinessQuery,
        extensions=[AioInjectExtension(container=container)],
    )

    # 5. Crear routers con rate limiting
    graphql_app = GraphQLRouter(schema)
    app.include_router(graphql_app, prefix="/graphql")
    app.include_router(auth_router)

    @app.get("/")
    @limiter.limit(RateLimitConfig.ROOT_ENDPOINT)
    async def root(request: Request):
        """Endpoint de bienvenida."""
        return {
            "mensaje": "Bienvenido al Backend del Agente de Ventas",
            "playground": "Ve a /graphql para probar el chat",
            "docs": "/docs",
            "rate_limits": {
                "graphql": RateLimitConfig.GRAPHQL_QUERY,
                "login": RateLimitConfig.LOGIN,
                "health": RateLimitConfig.HEALTH_CHECK
            }
        }
    
    @app.get("/health")
    @limiter.limit(RateLimitConfig.HEALTH_CHECK)
    async def health_check(request: Request):
        """Endpoint de health check."""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "rate_limiting": "enabled"
        }
    
    @app.get("/rate-limits")
    @limiter.limit(RateLimitConfig.ROOT_ENDPOINT)
    async def rate_limits_info(request: Request):
        """Información sobre los rate limits aplicados."""
        return {
            "endpoints": {
                "/graphql": {
                    "limit": RateLimitConfig.GRAPHQL_QUERY,
                    "description": "Queries y mutations GraphQL"
                },
                "/auth/login": {
                    "limit": RateLimitConfig.LOGIN,
                    "description": "Login de usuarios"
                },
                "/health": {
                    "limit": RateLimitConfig.HEALTH_CHECK,
                    "description": "Health check"
                }
            },
            "note": "Los límites son por IP o por usuario autenticado"
        }

    logger.info("✅ Rate limiting configurado")
    return app


# Crear instancia de la app para ASGI servers
app = create_app()

# Bloque de ejecución principal
if __name__ == "__main__":
    logger.info("Arrancando servidor en http://0.0.0.0:8000")
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend"],
    )
