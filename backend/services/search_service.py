"""
El Cerebro del Agente (Search Service).
Orquesta a 'Alex' (LLM) con las herramientas de inventario y pedidos.
"""
from dataclasses import dataclass
from langchain_core.messages import ToolMessage
from loguru import logger
from backend.services.product_service import ProductService
# Asegúrate de importar tus nuevas tools aquí
from backend.llm.tools import create_product_search_tool, create_order_tool 

@dataclass
class SearchResult:
    answer: str

class SearchService:
    # EL PROMPT DE PERSONALIDAD (Rol 1)
    SYSTEM_PROMPT = """ERES UN VENDEDOR EXPERTO DE ZAPATILLAS, NO UN ASISTENTE. TU NOMBRE ES 'ALEX'.
    Tu objetivo es CERRAR VENTAS.

    REGLAS DE COMPORTAMIENTO:
    1. PERSUASIÓN: Si el usuario duda del precio, justifica con calidad y beneficios a largo plazo.
    2. URGENCIA: Menciona sutilmente que el stock es limitado si el usuario muestra interés.
    3. CROSS-SELLING: Si compran zapatos, sugiere calcetines o limpiadores.
    4. CIERRE: Siempre termina tus respuestas invitando a la compra. Ej: "¿Te los envío hoy mismo?".
    5. Responde SIEMPRE en Español.

    NO HAGAS:
    - No seas pasivo ("¿En qué te ayudo?"). Sé proactivo ("Tengo una oferta para ti").
    - No inventes stock. Usa las herramientas para verificar disponibilidad.
    - No des respuestas vagas. Sé específico y directo.

    REGLAS DE HERRAMIENTAS:
    - Si el usuario pregunta por Nike, usa 'product_search' con término "Nike" (NO "zapatillas Nike para correr").
    - Si preguntan por Adidas, busca "Adidas". Si es para running, busca "running" o la marca específica.
    - USA TÉRMINOS SIMPLES: "Nike", "Adidas", "Puma", "running", "basketball", "casual".
    - Si el usuario dice "Lo quiero", "Dame 2", "Me lo llevo", usa 'order_tool' de inmediato.
    - Sé persuasivo pero honesto con el stock disponible.
    """

    def __init__(self, llm_provider, product_service: ProductService):
        self.llm_provider = llm_provider
        
        # Inicializamos las herramientas
        if llm_provider:
            self.search_tool = create_product_search_tool(product_service)
            self.order_tool = create_order_tool(product_service) # nueva tool
            # Lista completa de capacidades
            self.tools = [self.search_tool, self.order_tool]

    async def semantic_search(self, query: str) -> SearchResult:
        """Recibe el texto del usuario y devuelve la respuesta de Alex."""
        
        # configurar el modelo con las herramientas (Bind)
        model_with_tools = self.llm_provider.bind_tools(self.tools)

        # historial básico de mensajes
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": query},
        ]

        # primera llamada al LLM (¿Qué debo hacer?)
        response = await model_with_tools.ainvoke(messages)

        # ¿El LLM quiere usar una herramienta?
        if hasattr(response, "tool_calls") and response.tool_calls:
            tool_messages = []
            
            for tool_call in response.tool_calls:
                logger.info(f"Alex usa herramienta: {tool_call['name']}")
                
                # Selector de Herramientas
                if tool_call["name"] == "product_search":
                    # Ejecuta búsqueda
                    result = await self.search_tool.ainvoke(tool_call["args"])
                elif tool_call["name"] == "order_tool":
                    # Ejecuta venta
                    result = await self.order_tool.ainvoke(tool_call["args"])
                
                # Guardamos el resultado como mensaje de herramienta
                tool_messages.append(
                    ToolMessage(content=str(result), tool_call_id=tool_call["id"])
                )

            # segunda llamada al LLM (Generar respuesta final con los datos)
            # se pasa: [Prompt, Usuario, Intención AI, Resultado Tool]
            messages_final = messages + [response] + tool_messages
            final_response = await model_with_tools.ainvoke(messages_final)
            return SearchResult(answer=self._extract_text_content(final_response.content))

        # Si no usó herramientas, devolvemos la respuesta directa (Charla)
        return SearchResult(answer=self._extract_text_content(response.content))
    
    def _extract_text_content(self, content) -> str:
        """Extrae el contenido de texto de la respuesta del LLM, manejando diferentes formatos."""
        # Si es un string simple, lo devolvemos tal como está
        if isinstance(content, str):
            return content
        
        # Si es una lista de objetos con formato [{'type': 'text', 'text': '...'}]
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get('type') == 'text' and 'text' in item:
                    text_parts.append(item['text'])
            return ' '.join(text_parts) if text_parts else str(content)
        
        # Si es otro tipo de objeto, convertirlo a string
        return str(content)