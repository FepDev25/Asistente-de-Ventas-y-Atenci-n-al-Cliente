"""
Agente Vendedor "Alex" - Especializado en persuasión y recomendaciones.

NUEVO FLUJO: El Agente 2 envía un guión con códigos de barras.
Este agente recibe los productos, compara, analiza descuentos/promociones,
y persuade cuál es la mejor opción para el usuario.
"""
from typing import List, Optional
import asyncio
from loguru import logger
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from backend.agents.base import BaseAgent
from backend.domain.agent_schemas import AgentState, AgentResponse
from backend.domain.guion_schemas import GuionEntrada
from backend.llm.provider import LLMProvider
from backend.services.rag_service import RAGService
from backend.services.product_service import ProductService
from backend.services.product_comparison_service import ProductComparisonService


class SalesAgent(BaseAgent):
    """
    Agente Vendedor "Alex" - Especializado en persuasión y recomendaciones experto.
    
    FLUJO ACTUALIZADO:
    1. Recibe guion del Agente 2 (con códigos de barras)
    2. Busca productos en BD por código de barras
    3. Compara productos analizando:
       - Precios y descuentos
       - Promociones activas
       - Stock disponible
       - Preferencias del usuario
    4. Genera recomendación persuasiva personalizada
    5. Cierra venta transfiriendo a CheckoutAgent
    
    Ya NO hay restricción de 40-50 palabras.
    El agente puede dar respuestas completas y detalladas.
    """

    def __init__(
        self, 
        llm_provider: LLMProvider, 
        rag_service: RAGService,
        product_service: ProductService
    ):
        super().__init__(agent_name="sales")
        self.llm_provider = llm_provider
        self.rag_service = rag_service
        self.product_service = product_service
        self.comparison_service = ProductComparisonService()

    def can_handle(self, state: AgentState) -> bool:
        """
        El SalesAgent maneja:
        - Procesamiento de guiones del Agente 2
        - Comparación de productos
        - Recomendaciones
        - Objeciones de precio
        - Dudas sobre cuál elegir
        """
        # Si hay un guion en el estado, este agente lo procesa
        if hasattr(state, 'guion_agente2') and state.guion_agente2:
            return True
        
        if state.detected_intent in ["persuasion", "info", "recomendacion"]:
            return True

        # Palabras clave de comparación/recomendación
        persuasion_keywords = [
            "cual es mejor", "cual me recomiendas", "que diferencia",
            "cual elegir", "no se cual", "comparar", "versus",
            "por que este", "vale la pena", "mejor opcion",
            "descuento", "oferta", "promocion", "mas barato",
            "ahorro", "rebaja"
        ]

        query_lower = state.user_query.lower()
        return any(keyword in query_lower for keyword in persuasion_keywords)

    async def process(self, state: AgentState) -> AgentResponse:
        """
        Procesa interacciones de venta con el nuevo flujo de guiones.
        
        Flujo principal:
        1. Verificar si hay guion del Agente 2
        2. Si hay guion: buscar productos por barcode → comparar → recomendar
        3. Si no hay guion: usar RAG para preguntas generales
        """
        logger.info(f"SalesAgent procesando: {state.user_query}")
        
        try:
            # CASO 1: Procesar guion del Agente 2
            if hasattr(state, 'guion_agente2') and state.guion_agente2:
                return await self._procesar_guion(state)
            
            # CASO 2: Pregunta general (sin guion)
            return await self._procesar_pregunta_general(state)
                
        except Exception as e:
            logger.error(f"Error inesperado en SalesAgent: {str(e)}", exc_info=True)
            return self._create_response(
                message=self._get_error_message(state),
                state=state,
                should_transfer=False
            )

    async def _procesar_guion(self, state: AgentState) -> AgentResponse:
        """
        Procesa un guion completo del Agente 2.
        
        Este es el flujo principal del nuevo diseño:
        1. Extraer guion del estado
        2. Buscar productos por códigos de barras
        3. Comparar y generar recomendación
        4. Crear respuesta persuasiva personalizada
        """
        guion = state.guion_agente2
        
        logger.info(
            f"Procesando guion del Agente 2: {len(guion.productos)} productos, "
            f"session={guion.session_id}"
        )
        
        # 1. Extraer códigos de barras del guion
        barcodes = guion.get_codigos_barras()
        if not barcodes:
            return self._create_response(
                message="No se encontraron códigos de producto en el guión. ¿Puedes intentar de nuevo?",
                state=state,
                error="no_barcodes_in_guion"
            )
        
        # 2. Buscar productos en la base de datos
        products = await self.product_service.get_products_by_barcodes(barcodes)
        
        if not products:
            return self._create_response(
                message=(
                    f"No encontré los productos con códigos: {', '.join(barcodes)}. "
                    f"¿Puedes verificar los códigos o intentar con otros productos?"
                ),
                state=state,
                error="products_not_found"
            )
        
        # 3. Comparar productos y generar recomendación
        try:
            recommendation = await self.comparison_service.compare_and_recommend(
                products, guion
            )
        except ValueError as e:
            logger.warning(f"Error en comparación: {e}")
            # Si falla la comparación, mostrar productos encontrados
            return self._create_response(
                message=self._format_productos_simple(products, guion),
                state=state,
                should_transfer=False
            )
        
        # 4. Guardar productos en el estado para checkout posterior
        state.search_results = [
            {
                "id": str(p.id),
                "name": p.product_name,
                "price": float(p.final_price),
                "original_price": float(p.unit_cost) if p.unit_cost else None,
                "stock": p.quantity_available,
                "barcode": p.barcode,
                "is_on_sale": p.is_on_sale,
                "promotion": p.promotion_description
            }
            for p in products
        ]
        
        # 5. Generar mensaje persuasivo con estilo del usuario
        mensaje = self._generar_mensaje_recomendacion(
            recommendation, 
            guion.preferencias,
            guion
        )
        
        # 6. Agregar al historial
        state = self._add_to_history(state, "user", guion.texto_original_usuario)
        state = self._add_to_history(state, "assistant", mensaje)
        
        # 7. Detectar si hay intención de compra
        should_transfer = self._detectar_intencion_compra(
            guion.contexto.intencion_principal
        )
        
        logger.info(
            f"Recomendación generada: mejor_opcion={recommendation.best_option_id}, "
            f"score={recommendation.products[0].recommendation_score if recommendation.products else 0}"
        )
        
        return self._create_response(
            message=mensaje,
            state=state,
            should_transfer=should_transfer,
            transfer_to="checkout" if should_transfer else None,
            metadata={
                "guion_procesado": True,
                "productos_encontrados": len(products),
                "mejor_opcion": str(recommendation.best_option_id),
                "intencion": guion.contexto.intencion_principal
            }
        )

    async def _procesar_pregunta_general(self, state: AgentState) -> AgentResponse:
        """
        Procesa preguntas generales cuando no hay guion.
        Usa RAG para FAQs y el LLM para responder.
        """
        # Construir system prompt
        system_prompt = self._build_system_prompt_simple(state)
        
        # Consultar RAG si es necesario
        contexto_rag = ""
        if any(palabra in state.user_query.lower() for palabra in 
               ["política", "devolución", "garantía", "envío", "hora"]):
            try:
                rag_results = await self.rag_service.get_context_for_query(
                    state.user_query, max_results=2
                )
                contexto_rag = rag_results
            except Exception as e:
                logger.warning(f"RAG no disponible: {e}")
        
        # Construir mensajes
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"{contexto_rag}\n\nPregunta: {state.user_query}")
        ]
        
        # Llamar al LLM
        try:
            response = await asyncio.wait_for(
                self.llm_provider.model.ainvoke(messages),
                timeout=10.0
            )
            mensaje = response.content.strip()
        except asyncio.TimeoutError:
            mensaje = self._get_timeout_message(state)
        
        # Actualizar historial
        state = self._add_to_history(state, "user", state.user_query)
        state = self._add_to_history(state, "assistant", mensaje)
        
        return self._create_response(
            message=mensaje,
            state=state,
            should_transfer=False
        )

    def _generar_mensaje_recomendacion(
        self,
        recommendation: 'ProductRecommendationResult',
        preferencias: 'PreferenciasUsuario',
        guion: GuionEntrada
    ) -> str:
        """
        Genera un mensaje persuasivo personalizado según el estilo del usuario.
        
        Ya NO hay límite de 40-50 palabras. Mensajes completos y útiles.
        """
        estilo = preferencias.estilo_comunicacion
        producto_recomendado = recommendation.products[0]
        
        # Emojis y tono según estilo
        emojis = {
            "cuencano": {"saludo": "👋", "oferta": "🎉", "urgencia": "⚡", "mejor": "🏆"},
            "juvenil": {"saludo": "👋", "oferta": "🔥", "urgencia": "⏰", "mejor": "⭐"},
            "formal": {"saludo": "", "oferta": "💼", "urgencia": "📅", "mejor": "✓"},
            "neutral": {"saludo": "👋", "oferta": "🎁", "urgencia": "⏳", "mejor": "⭐"}
        }
        e = emojis.get(estilo, emojis["neutral"])
        
        # Construir mensaje según estilo
        if estilo == "cuencano":
            return self._mensaje_cuencano(producto_recomendado, recommendation, e, guion)
        elif estilo == "juvenil":
            return self._mensaje_juvenil(producto_recomendado, recommendation, e, guion)
        elif estilo == "formal":
            return self._mensaje_formal(producto_recomendado, recommendation, e, guion)
        else:
            return self._mensaje_neutral(producto_recomendado, recommendation, e, guion)

    def _mensaje_cuencano(
        self, 
        producto: 'ProductComparisonSchema', 
        rec: 'ProductRecommendationResult',
        e: dict,
        guion: GuionEntrada
    ) -> str:
        """Mensaje en estilo cuencano."""
        lineas = []
        
        # Saludo
        lineas.append(f"{e['saludo']} ¡Ayayay, mirá lo que tengo para vos ve! {e['mejor']}")
        lineas.append("")
        
        # Producto recomendado
        lineas.append(f"**{producto.product_name}**")
        
        # Precio con emoción
        if producto.is_on_sale:
            lineas.append(f"💰 Antes ~~${producto.unit_cost:.2f}~~ → Ahora **${producto.final_price:.2f}**")
            lineas.append(f"🎉 ¡Te ahorrás ${producto.savings_amount:.2f}! {e['oferta']}")
            if producto.promotion_description:
                lineas.append(f"🎁 {producto.promotion_description}")
        else:
            lineas.append(f"💰 Precio: ${producto.final_price:.2f}")
        
        lineas.append("")
        
        # Por qué es bueno
        lineas.append("**¿Por qué este es el mejor para vos?**")
        lineas.append(producto.reason)
        lineas.append("")
        
        # Análisis de preferencias
        if guion.preferencias.uso_previsto:
            lineas.append(f"✅ Ideal para: {guion.preferencias.uso_previsto}")
        
        if producto.recommendation_score > 80:
            lineas.append(f"⭐ Calificación: {producto.recommendation_score:.0f}/100 - ¡Excelente match!")
        
        lineas.append("")
        
        # Stock
        if producto.quantity_available <= 5:
            lineas.append(f"{e['urgencia']} **Ojo ve:** Solo quedan {producto.quantity_available} unidades, se van volando!")
        
        # Cierre
        lineas.append("")
        lineas.append("¿Querés que te los reserve? ¡Dale nomás! 🛒")
        
        return "\n".join(lineas)

    def _mensaje_juvenil(
        self, 
        producto: 'ProductComparisonSchema', 
        rec: 'ProductRecommendationResult',
        e: dict,
        guion: GuionEntrada
    ) -> str:
        """Mensaje en estilo juvenil."""
        lineas = []
        
        lineas.append(f"{e['saludo']} ¡Che, encontré el mejor para vos! {e['mejor']}")
        lineas.append("")
        lineas.append(f"**{producto.product_name}**")
        
        if producto.is_on_sale:
            lineas.append(f"🔥 ~~${producto.unit_cost:.2f}~~ → **${producto.final_price:.2f}**")
            lineas.append(f"💵 Ahorrás: ${producto.savings_amount:.2f}")
        else:
            lineas.append(f"💰 ${producto.final_price:.2f}")
        
        lineas.append("")
        lineas.append("**Por qué este:**")
        lineas.append(producto.reason)
        lineas.append("")
        
        if producto.quantity_available <= 5:
            lineas.append(f"{e['urgencia']} Últimas {producto.quantity_available} unidades!")
        
        lineas.append("")
        lineas.append("¿Los llevamos?")
        
        return "\n".join(lineas)

    def _mensaje_formal(
        self, 
        producto: 'ProductComparisonSchema', 
        rec: 'ProductRecommendationResult',
        e: dict,
        guion: GuionEntrada
    ) -> str:
        """Mensaje en estilo formal."""
        lineas = []
        
        lineas.append("Le presento mi recomendación:")
        lineas.append("")
        lineas.append(f"**{producto.product_name}**")
        
        if producto.is_on_sale:
            lineas.append(f"Precio regular: ~~${producto.unit_cost:.2f}~~")
            lineas.append(f"**Precio especial: ${producto.final_price:.2f}**")
            lineas.append(f"Ahorro: ${producto.savings_amount:.2f}")
            if producto.promotion_description:
                lineas.append(f"Promoción aplicable: {producto.promotion_description}")
        else:
            lineas.append(f"Precio: ${producto.final_price:.2f}")
        
        lineas.append("")
        lineas.append("**Análisis comparativo:**")
        lineas.append(rec.reasoning)
        lineas.append("")
        
        if producto.quantity_available <= 5:
            lineas.append(f"Stock disponible: {producto.quantity_available} unidades.")
        
        lineas.append("")
        lineas.append("¿Desea proceder con la compra de este modelo?")
        
        return "\n".join(lineas)

    def _mensaje_neutral(
        self, 
        producto: 'ProductComparisonSchema', 
        rec: 'ProductRecommendationResult',
        e: dict,
        guion: GuionEntrada
    ) -> str:
        """Mensaje en estilo neutral."""
        lineas = []
        
        lineas.append(f"{e['mejor']} **Te recomiendo: {producto.product_name}**")
        lineas.append("")
        
        # Precio
        if producto.is_on_sale:
            lineas.append(f"💰 ~~${producto.unit_cost:.2f}~~ → **${producto.final_price:.2f}**")
            lineas.append(f"🎉 Ahorras ${producto.savings_amount:.2f}")
        else:
            lineas.append(f"💰 Precio: ${producto.final_price:.2f}")
        
        lineas.append("")
        lineas.append("**¿Por qué este modelo?**")
        lineas.append(producto.reason)
        
        if len(rec.products) > 1:
            lineas.append("")
            lineas.append("**Comparación rápida:**")
            for p in rec.products[1:3]:
                diff = p.final_price - producto.final_price
                if diff > 0:
                    lineas.append(f"• vs {p.product_name}: Este ahorra ${diff:.2f}")
        
        if producto.quantity_available <= 5:
            lineas.append("")
            lineas.append(f"⚠️ Solo quedan {producto.quantity_available} unidades")
        
        lineas.append("")
        lineas.append("¿Te gustaría comprar este?")
        
        return "\n".join(lineas)

    def _format_productos_simple(
        self, 
        products: List['ProductStock'], 
        guion: GuionEntrada
    ) -> str:
        """Formato simple cuando no se puede hacer comparación completa."""
        lineas = ["Encontré estos productos:"]
        lineas.append("")
        
        for p in products:
            lineas.append(f"• **{p.product_name}**")
            lineas.append(f"  Precio: ${p.final_price:.2f}")
            if p.is_on_sale:
                lineas.append(f"  🎉 En oferta: {p.promotion_description or 'Descuento disponible'}")
            lineas.append("")
        
        lineas.append("¿Cuál te interesa más?")
        return "\n".join(lineas)

    def _detectar_intencion_compra(self, intencion: str) -> bool:
        """Detecta si la intención es compra directa."""
        return intencion in ["compra_directa", "comprar", "confirmar"]

    def _build_system_prompt_simple(self, state: AgentState) -> str:
        """System prompt simplificado para preguntas generales."""
        return """Eres Alex, asistente de ventas de una tienda de calzado deportivo.

Tu trabajo es ayudar a los clientes con preguntas sobre:
- Políticas de la tienda
- Información de envíos
- Garantías
- Horarios
- Métodos de pago

Responde de manera clara, amable y concisa. Si no sabes algo, di que consultarás con el equipo."""

    def _get_error_message(self, state: AgentState) -> str:
        """Mensaje de error amigable."""
        return "Lo siento, tuve un problema procesando tu solicitud. ¿Puedes intentar de nuevo?"

    def _get_timeout_message(self, state: AgentState) -> str:
        """Mensaje cuando hay timeout."""
        return "Disculpa la demora. ¿Puedes repetir tu pregunta?"
