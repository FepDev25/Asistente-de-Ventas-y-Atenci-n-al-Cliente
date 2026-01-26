"""
Proveedor de LLM (backend/llm/provider.py).
Usa ChatVertexAI como indicaste.
"""
from langchain_google_vertexai import ChatVertexAI
from backend.config import get_business_settings

class LLMProvider:
    # Wrapper para el modelo ChatVertexAI de Google.
    

    def __init__(self) -> None:
        settings = get_business_settings()

        # Usamos la clase que tú indicaste
        self.model = ChatVertexAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            project=settings.google_cloud_project, # Toma el ID de .env
            location=settings.google_location,      # us-central1
            convert_system_message_to_human=True    # Ayuda con la compatibilidad de roles
        )

    def bind_tools(self, tools: list):
        """
        Vincula las herramientas (consultar_inventario, crear_pedido) al modelo.
        Equivalente a: llm_con_herramientas = llm.bind_tools(tools)
        """
        return self.model.bind_tools(tools)

def create_llm_provider() -> LLMProvider | None:
    """Factory para crear el proveedor."""
    try:
        return LLMProvider()
    except Exception as e:
        print(f"Error al conectar con Vertex AI: {e}")
        return None