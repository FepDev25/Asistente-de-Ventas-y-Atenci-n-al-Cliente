"""
Contenedor de Inyección de Dependencias.
Aquí es donde "fabricamos" y conectamos todos los servicios de la aplicación.
"""
import functools
import dotenv
from collections.abc import Iterable
from typing import Any

import aioinject
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

# Cargar variables de entorno al inicio del container
dotenv.load_dotenv()

from backend.database.session import get_session_factory
from backend.llm.provider import LLMProvider, create_llm_provider
from backend.services.product_service import ProductService
from backend.services.search_service import SearchService
from backend.services.tenant_data_service import TenantDataService
from backend.services.rag_service import RAGService


async def create_tenant_data_service() -> TenantDataService:
    """Fabrica el servicio de lectura de CSVs (RAG)."""
    return TenantDataService()

async def create_session_factory() -> async_sessionmaker[AsyncSession]:
    """Fabrica el creador de sesiones de base de datos."""
    return get_session_factory()

async def create_product_service(
    session_factory: async_sessionmaker[AsyncSession],
) -> ProductService:
    """Fabrica el servicio de inventario conectándolo a la DB."""
    return ProductService(session_factory)

async def create_llm_provider_instance() -> LLMProvider:
    """Fabrica el proveedor de IA (Gemini)."""
    return create_llm_provider()

async def create_rag_service() -> RAGService:
    """Fabrica el servicio RAG (búsqueda semántica)."""
    return RAGService()

async def create_search_service(
    llm_provider: LLMProvider,
    product_service: ProductService,
    rag_service: RAGService,
) -> SearchService:
    """
    Fabrica el 'Cerebro' (SearchService).
    Le inyecta el LLM (Alex), el acceso a Productos (Inventario) y el RAG.
    """
    return SearchService(llm_provider, product_service, rag_service)


def providers() -> Iterable[aioinject.Provider[Any]]:
    """Lista de instrucciones para crear todos los servicios."""
    providers_list: list[aioinject.Provider[Any]] = []

    # 1. Servicios de Datos
    providers_list.append(aioinject.Singleton(create_tenant_data_service))
    providers_list.append(aioinject.Singleton(create_session_factory))
    providers_list.append(aioinject.Singleton(create_product_service))

    # 2. Servicios de IA
    providers_list.append(aioinject.Singleton(create_llm_provider_instance))
    providers_list.append(aioinject.Singleton(create_rag_service))
    providers_list.append(aioinject.Singleton(create_search_service))

    return providers_list


def create_business_container() -> aioinject.Container:
    """Crea el contenedor final con todas las dependencias."""
    container = aioinject.Container()
    for provider in providers():
        container.register(provider)
    return container