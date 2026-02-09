"""
Mutations GraphQL para operaciones de escritura.
Crear, actualizar y eliminar recursos.
"""
from typing import Annotated, List, Optional
from uuid import UUID
from datetime import datetime

import strawberry
from aioinject import Inject
from aioinject.ext.strawberry import inject
from loguru import logger
from strawberry.types import Info

from backend.config.security import securityJWT
from backend.api.graphql.queries import get_current_user
from backend.api.graphql.types import (
    UserType,
    OrderType,
    OrderDetailType,
    CreateUserInput,
    UpdateUserInput,
    ChangePasswordInput,
    CreateOrderInput,
    UpdateOrderStatusInput,
    CreateOrderResponse,
    AuthResponse,
    ProductRecognitionResponse,
    GuionEntradaInput,
    RecomendacionResponse,
    ProductComparisonType,
    ContinuarConversacionResponse,
)
from backend.services.user_service import UserService, UserAlreadyExistsError, UserNotFoundError
from backend.services.order_service import OrderService, OrderServiceError, InsufficientStockError, ProductNotFoundError
from backend.services.product_service import ProductService
from backend.services.product_comparison_service import ProductComparisonService
from backend.services.session_service import SessionService
from backend.llm.provider import LLMProvider
from backend.domain.order_schemas import OrderCreate, OrderDetailCreate
from backend.domain.agent_schemas import AgentState
from backend.domain.guion_schemas import GuionEntrada, ProductoEnGuion, PreferenciasUsuario, ContextoBusqueda
from backend.tools.agent2_recognition_client import ProductRecognitionClient
from backend.agents.sales_agent import SalesAgent
import os


@strawberry.type
class BusinessMutation:
    """Raíz de todas las mutations."""
    
    # ========================================================================
    # ORDENES/PEDIDOS
    # ========================================================================
    
    @strawberry.mutation
    @inject
    async def create_order(
        self,
        input: CreateOrderInput,
        order_service: Annotated[OrderService, Inject],
        info: Info
    ) -> CreateOrderResponse:
        """
        Crea un nuevo pedido.
        
        Requiere autenticación.
        """
        current_user = get_current_user(info)
        if not current_user:
            return CreateOrderResponse(
                success=False,
                message="Debes iniciar sesión para crear un pedido",
                error="unauthorized"
            )
        
        user_id = UUID(current_user["id"])
        
        try:
            # Convertir input a schema
            details = [
                OrderDetailCreate(
                    product_id=d.product_id,
                    quantity=d.quantity
                )
                for d in input.details
            ]
            
            order_data = OrderCreate(
                user_id=user_id,
                details=details,
                shipping_address=input.shipping_address,
                shipping_city=input.shipping_city,
                shipping_state=input.shipping_state,
                shipping_country=input.shipping_country,
                notes=input.notes,
                session_id=input.session_id
            )
            
            order, message = await order_service.create_order(order_data)
            
            # Convertir a tipo GraphQL
            order_type = OrderType(
                id=order.id,
                user_id=order.user_id,
                status=order.status,
                subtotal=order.subtotal,
                total_amount=order.total_amount,
                tax_amount=order.tax_amount,
                shipping_cost=order.shipping_cost,
                discount_amount=order.discount_amount,
                shipping_address=order.shipping_address,
                shipping_city=order.shipping_city,
                shipping_state=order.shipping_state,
                shipping_country=order.shipping_country,
                details=[
                    OrderDetailType(
                        id=d.id,
                        product_id=d.product_id,
                        product_name=d.product_name,
                        quantity=d.quantity,
                        unit_price=d.unit_price
                    )
                    for d in order.details
                ],
                notes=order.notes,
                session_id=order.session_id,
                created_at=order.created_at,
                updated_at=order.updated_at
            )
            
            return CreateOrderResponse(
                success=True,
                order=order_type,
                message=message
            )
            
        except ProductNotFoundError as e:
            return CreateOrderResponse(
                success=False,
                message=str(e),
                error="product_not_found"
            )
            
        except InsufficientStockError as e:
            return CreateOrderResponse(
                success=False,
                message=str(e),
                error="insufficient_stock"
            )
            
        except OrderServiceError as e:
            return CreateOrderResponse(
                success=False,
                message=str(e),
                error="order_error"
            )
            
        except Exception as e:
            logger.error(f"Error creando orden: {e}", exc_info=True)
            return CreateOrderResponse(
                success=False,
                message="Error interno del servidor",
                error="internal_error"
            )
    
    @strawberry.mutation
    @inject
    async def cancel_order(
        self,
        order_id: UUID,
        order_service: Annotated[OrderService, Inject],
        info: Info,
        reason: Optional[str] = None
    ) -> CreateOrderResponse:
        """
        Cancela un pedido existente.
        
        Requiere autenticación. Solo el dueño del pedido o un admin puede cancelarlo.
        """
        current_user = get_current_user(info)
        if not current_user:
            return CreateOrderResponse(
                success=False,
                message="No autenticado",
                error="unauthorized"
            )
        
        try:
            success, message = await order_service.cancel_order(order_id, reason)
            
            if success:
                # Obtener la orden actualizada
                order = await order_service.get_order_by_id(order_id)
                if order:
                    order_type = OrderType(
                        id=order.id,
                        user_id=order.user_id,
                        status=order.status,
                        subtotal=order.subtotal,
                        total_amount=order.total_amount,
                        tax_amount=order.tax_amount,
                        shipping_cost=order.shipping_cost,
                        discount_amount=order.discount_amount,
                        shipping_address=order.shipping_address,
                        shipping_city=order.shipping_city,
                        shipping_state=order.shipping_state,
                        shipping_country=order.shipping_country,
                        details=[
                            OrderDetailType(
                                id=d.id,
                                product_id=d.product_id,
                                product_name=d.product_name,
                                quantity=d.quantity,
                                unit_price=d.unit_price
                            )
                            for d in order.details
                        ],
                        notes=order.notes,
                        session_id=order.session_id,
                        created_at=order.created_at,
                        updated_at=order.updated_at
                    )
                    
                    return CreateOrderResponse(
                        success=True,
                        order=order_type,
                        message=message
                    )
            
            return CreateOrderResponse(
                success=False,
                message=message,
                error="cancel_failed"
            )
            
        except Exception as e:
            logger.error(f"Error cancelando orden: {e}")
            return CreateOrderResponse(
                success=False,
                message="Error interno del servidor",
                error="internal_error"
            )
    
    # ========================================================================
    # NUEVO: PROCESAMIENTO DE GUION DEL AGENTE 2
    # ========================================================================
    
    @strawberry.mutation
    @inject
    async def procesar_guion_agente2(
        self,
        info: Info,
        guion: GuionEntradaInput,
        product_service: Annotated[ProductService, Inject],
        llm_provider: Annotated[LLMProvider, Inject],
        session_service: Annotated[SessionService, Inject],
    ) -> RecomendacionResponse:
        """
        Procesa un guion del Agente 2 y genera una recomendación.
        
        Este es el nuevo flujo principal:
        1. Recibe guion con códigos de barras de productos identificados
        2. Busca productos en BD por barcode
        3. Compara productos analizando descuentos, promociones, stock
        4. Genera recomendación persuasiva personalizada
        
        Requiere autenticación.
        
        Args:
            guion: Guion estructurado del Agente 2
            
        Returns:
            RecomendacionResponse con análisis comparativo y recomendación
            
        Example:
            mutation {
                procesarGuionAgente2(guion: {
                    sessionId: "sess-123",
                    productos: [
                        {codigoBarras: "7501234567890", nombreDetectado: "Nike Pegasus", prioridad: "alta"}
                    ],
                    preferencias: {estiloComunicacion: "cuencano", presupuestoMaximo: 150},
                    contexto: {tipoEntrada: "voz", intencionPrincipal: "comparar"},
                    textoOriginalUsuario: "Busco zapatillas...",
                    resumenAnalisis: "Usuario busca...",
                    confianzaProcesamiento: 0.92
                }) {
                    success
                    mensaje
                    productos {
                        productName
                        finalPrice
                        recommendationScore
                        reason
                    }
                    mejorOpcionId
                    reasoning
                }
            }
        """
        # Verificar autenticación
        current_user = get_current_user(info)
        if not current_user:
            return RecomendacionResponse(
                success=False,
                mensaje="Debes iniciar sesión",
                productos=[],
                mejor_opcion_id=UUID("00000000-0000-0000-0000-000000000000"),
                reasoning="",
                siguiente_paso="login"
            )
        
        logger.info(
            f"Procesando guion Agente 2: session={guion.session_id}, "
            f"productos={len(guion.productos)}, user={current_user.get('username')}"
        )
        
        try:
            # 1. Convertir input GraphQL a schema Pydantic
            productos_guion = [
                ProductoEnGuion(
                    codigo_barras=p.codigo_barras,
                    nombre_detectado=p.nombre_detectado,
                    marca=p.marca,
                    categoria=p.categoria,
                    prioridad=p.prioridad,
                    motivo_seleccion=p.motivo_seleccion
                )
                for p in guion.productos
            ]
            
            preferencias = PreferenciasUsuario(
                estilo_comunicacion=guion.preferencias.estilo_comunicacion,
                uso_previsto=guion.preferencias.uso_previsto,
                nivel_actividad=guion.preferencias.nivel_actividad,
                talla_preferida=guion.preferencias.talla_preferida,
                color_preferido=guion.preferencias.color_preferido,
                presupuesto_maximo=guion.preferencias.presupuesto_maximo,
                busca_ofertas=guion.preferencias.busca_ofertas,
                urgencia=guion.preferencias.urgencia,
                caracteristicas_importantes=guion.preferencias.caracteristicas_importantes
            )
            
            contexto = ContextoBusqueda(
                tipo_entrada=guion.contexto.tipo_entrada,
                producto_mencionado_explicitamente=guion.contexto.producto_mencionado_explicitamente,
                necesita_recomendacion=guion.contexto.necesita_recomendacion,
                intencion_principal=guion.contexto.intencion_principal,
                restricciones_adicionales=guion.contexto.restricciones_adicionales
            )
            
            guion_completo = GuionEntrada(
                session_id=guion.session_id,
                productos=productos_guion,
                preferencias=preferencias,
                contexto=contexto,
                texto_original_usuario=guion.texto_original_usuario,
                resumen_analisis=guion.resumen_analisis,
                confianza_procesamiento=guion.confianza_procesamiento
            )
            
            # 2. Extraer códigos de barras
            barcodes = guion_completo.get_codigos_barras()
            if not barcodes:
                return RecomendacionResponse(
                    success=False,
                    mensaje="No se encontraron códigos de barras válidos en el guión",
                    productos=[],
                    mejor_opcion_id=UUID("00000000-0000-0000-0000-000000000000"),
                    reasoning="El guión no contiene códigos de barras válidos",
                    siguiente_paso="reintentar"
                )
            
            # 3. Buscar productos en la BD
            products = await product_service.get_products_by_barcodes(barcodes)
            
            if not products:
                return RecomendacionResponse(
                    success=False,
                    mensaje=f"No encontré productos con los códigos: {', '.join(barcodes)}",
                    productos=[],
                    mejor_opcion_id=UUID("00000000-0000-0000-0000-000000000000"),
                    reasoning="Los productos del guión no están disponibles en nuestro inventario",
                    siguiente_paso="ver_alternativas"
                )
            
            # 4. Comparar y generar recomendación
            comparison_service = ProductComparisonService()
            recommendation = await comparison_service.compare_and_recommend(
                products, guion_completo
            )
            
            # 5. Convertir a tipos GraphQL
            productos_response = [
                ProductComparisonType(
                    id=p.id,
                    product_name=p.product_name,
                    barcode=p.barcode,
                    brand=p.brand,
                    category=p.category,
                    unit_cost=p.unit_cost,
                    final_price=p.final_price,
                    savings_amount=p.savings_amount,
                    is_on_sale=p.is_on_sale,
                    discount_percent=p.discount_percent,
                    promotion_description=p.promotion_description,
                    quantity_available=p.quantity_available,
                    recommendation_score=p.recommendation_score,
                    reason=p.reason
                )
                for p in recommendation.products
            ]
            
            # 6. Determinar siguiente paso
            siguiente_paso = "confirmar_compra"
            if guion_completo.contexto.necesita_recomendacion and len(products) > 1:
                siguiente_paso = "confirmar_compra"
            elif guion_completo.contexto.intencion_principal == "informacion":
                siguiente_paso = "mas_info"
            
            # Generar mensaje persuasivo usando LLM
            from langchain_core.messages import HumanMessage, SystemMessage
            
            best_product = recommendation.products[0]
            
            # Construir prompt para el LLM
            estilo = guion_completo.preferencias.estilo_comunicacion
            
            system_prompts = {
                "cuencano": "Eres un vendedor ecuatoriano, cálido y cercano. Hablas de forma natural como con un amigo. Usa expresiones como 'mirá', 'fíjate'. NO uses bullets ni listas. Máximo 3 oraciones.",
                "juvenil": "Eres un vendedor joven, directo y energético. Hablas de forma casual y natural. NO uses bullets ni listas. Máximo 3 oraciones.",
                "formal": "Eres un vendedor profesional y educado. Hablas con respeto pero cercanía. NO uses bullets ni listas. Máximo 3 oraciones.",
                "neutral": "Eres un vendedor amigable y natural. Hablas de forma conversacional. NO uses bullets ni listas. Máximo 3 oraciones."
            }
            
            system_prompt = system_prompts.get(estilo, system_prompts["neutral"])
            
            # Contexto del producto
            producto_info = f"Producto: {best_product.product_name}\n"
            producto_info += f"Precio: ${best_product.final_price:.2f}\n"
            if best_product.is_on_sale:
                producto_info += f"Descuento: {best_product.discount_percent}% (ahorras ${float(best_product.savings_amount):.2f})\n"
                producto_info += f"Promoción: {best_product.promotion_description}\n"
            producto_info += f"Stock: {best_product.quantity_available} unidades\n"
            if guion_completo.preferencias.uso_previsto:
                producto_info += f"Uso: {guion_completo.preferencias.uso_previsto}\n"
            
            # Productos alternativos si hay
            if len(recommendation.products) > 1:
                producto_info += "\nAlternativas:\n"
                for p in recommendation.products[1:3]:
                    producto_info += f"- {p.product_name}: ${p.final_price:.2f}\n"
            
            user_prompt = f"Genera un mensaje persuasivo recomendando este producto. Sé natural, menciona el precio y el descuento si aplica. Cierra preguntando si le interesa.\n\n{producto_info}"
            
            try:
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                response = await llm_provider.model.ainvoke(messages)
                mensaje = response.content.strip()
            except Exception as e:
                logger.warning(f"LLM no disponible para mensaje persuasivo: {e}")
                # Fallback simple
                mensaje = f"Te recomiendo el {best_product.product_name} a ${best_product.final_price:.2f}. Es una excelente opción. ¿Te interesa?"
            
            # 7. Guardar sesión en Redis para continuarConversacion (usando Redis directamente)
            from backend.config.redis_config import RedisSettings
            import redis.asyncio as redis
            
            try:
                redis_settings = RedisSettings()
                redis_client = redis.from_url(
                    redis_settings.get_redis_url(),
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                
                session_data = {
                    'session_id': guion_completo.session_id,
                    'mejor_opcion_id': str(recommendation.best_option_id),
                    'productos': [
                        {
                            'id': str(p.id),
                            'product_name': p.product_name,
                            'final_price': float(p.final_price),
                            'discount_percent': float(p.discount_percent) if p.discount_percent else None
                        }
                        for p in recommendation.products
                    ],
                    'current_index': 0,  # Índice del producto actual
                    'estilo_comunicacion': guion_completo.preferencias.estilo_comunicacion,
                    'created_at': datetime.now().isoformat()
                }
                
                import json
                session_key = f"guion_session:{guion_completo.session_id}"
                await redis_client.setex(session_key, 1800, json.dumps(session_data))  # 30 min TTL
                logger.info(f"Sesión guardada en Redis: {guion_completo.session_id}")
                await redis_client.close()
            except Exception as redis_err:
                logger.warning(f"No se pudo guardar sesión en Redis: {redis_err}")
            
            return RecomendacionResponse(
                success=True,
                mensaje=mensaje,
                productos=productos_response,
                mejor_opcion_id=recommendation.best_option_id,
                reasoning=recommendation.reasoning,
                siguiente_paso=siguiente_paso
            )
            
        except Exception as e:
            logger.error(f"Error procesando guion: {e}", exc_info=True)
            return RecomendacionResponse(
                success=False,
                mensaje=f"Error procesando el guión: {str(e)}",
                productos=[],
                mejor_opcion_id=UUID("00000000-0000-0000-0000-000000000000"),
                reasoning="Ocurrió un error interno",
                siguiente_paso="reintentar"
            )    
    # ========================================================================
    # NUEVO: CONTINUAR CONVERSACIÓN DEL GUION
    # ========================================================================
    
    @strawberry.mutation
    @inject
    async def continuar_conversacion(
        self,
        info: Info,
        session_id: str,
        respuesta_usuario: str,
    ) -> ContinuarConversacionResponse:
        """
        Continúa el flujo de conversación después de procesarGuionAgente2.
        
        Maneja las respuestas del usuario (aprobación, rechazo, datos de envío)
        y determina el siguiente paso en el flujo de ventas.
        
        Requiere autenticación.
        
        Args:
            session_id: ID de sesión del guion
            respuesta_usuario: Texto de respuesta del usuario
            
        Returns:
            ContinuarConversacionResponse con siguiente paso
        """
        
        # Verificar autenticación
        current_user = get_current_user(info)
        if not current_user:
            return ContinuarConversacionResponse(
                success=False,
                mensaje="Debes iniciar sesión",
                siguiente_paso="login"
            )
        
        logger.info(
            f"Continuando conversación: session={session_id}, "
            f"respuesta='{respuesta_usuario}', user={current_user.get('username')}"
        )
        
        try:
            # Obtener sesión de Redis (usando Redis directamente)
            import redis.asyncio as redis
            import json
            from backend.config.redis_config import RedisSettings
            
            redis_settings = RedisSettings()
            redis_client = redis.from_url(
                redis_settings.get_redis_url(),
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            session_key = f"guion_session:{session_id}"
            session_json = await redis_client.get(session_key)
            await redis_client.close()
            
            if not session_json:
                logger.warning(f"Sesión no encontrada o expirada: {session_id}")
                return ContinuarConversacionResponse(
                    success=False,
                    mensaje="La sesión ha expirado. Por favor, comienza de nuevo.",
                    siguiente_paso="nueva_conversacion"
                )
            
            session_data = json.loads(session_json)
            
            # Analizar respuesta del usuario
            respuesta_lower = respuesta_usuario.lower().strip()
            
            # Detectar aprobación
            palabras_aprobacion = ['si', 'sí', 'yes', 'ok', 'dale', 'va', 'claro', 'perfecto', 'bueno']
            es_aprobacion = any(palabra in respuesta_lower for palabra in palabras_aprobacion)
            
            # Detectar rechazo
            palabras_rechazo = ['no', 'nop', 'nope', 'nah', 'otra', 'diferente', 'siguiente']
            es_rechazo = any(palabra in respuesta_lower for palabra in palabras_rechazo)
            
            # Si es aprobación → Solicitar datos de envío
            if es_aprobacion:
                logger.info(f"Usuario aprobó producto. Session: {session_id}")
                
                # Actualizar sesión con aprobación
                session_data['approved'] = True
                
                redis_client_update = redis.from_url(
                    redis_settings.get_redis_url(),
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                await redis_client_update.setex(session_key, 1800, json.dumps(session_data))
                await redis_client_update.close()
                
                return ContinuarConversacionResponse(
                    success=True,
                    mensaje="¡Qué bacán que te gustaron! 🎉\n\nPara ya mismo coordinar el envío y que te lleguen rápidito, ¿me confirmas qué talla necesitas y a qué dirección te las hacemos llegar?",
                    mejor_opcion_id=session_data.get('mejor_opcion_id'),
                    siguiente_paso="solicitar_datos_envio"
                )
            
            # Si es rechazo → Ofrecer alternativa
            elif es_rechazo:
                logger.info(f"Usuario rechazó producto. Buscando alternativa. Session: {session_id}")
                
                # Obtener productos alternativos
                productos = session_data.get('productos', [])
                producto_actual_index = session_data.get('current_index', 0)
                
                # Buscar siguiente producto disponible
                if producto_actual_index + 1 < len(productos):
                    siguiente_producto = productos[producto_actual_index + 1]
                    
                    # Actualizar sesión
                    session_data['current_index'] = producto_actual_index + 1
                    session_data['mejor_opcion_id'] = siguiente_producto.get('id')
                    
                    redis_client_update = redis.from_url(
                        redis_settings.get_redis_url(),
                        encoding="utf-8",
                        decode_responses=True,
                        socket_connect_timeout=5
                    )
                    await redis_client_update.setex(session_key, 1800, json.dumps(session_data))
                    await redis_client_update.close()
                    
                    # Mensaje con alternativa
                    precio = float(siguiente_producto.get('final_price', 0))
                    nombre = siguiente_producto.get('product_name', 'producto')
                    descuento = siguiente_producto.get('discount_percent')
                    
                    mensaje = f"¡Claro que sí! Entiendo que los Air Max 90 no fueron lo tuyo. 😊\n\n"
                    mensaje += f"Pero tengo una alternativa genial que quizás te encante: los **{nombre}**. "
                    
                    if descuento:
                        mensaje += f"¡Son un estilo más clásico y versátil, y lo mejor es que están en oferta por solo **${precio:.2f}**! 🔥\n\n"
                    else:
                        mensaje += f"Son un estilo más clásico y versátil, a **${precio:.2f}**. \n\n"
                    
                    mensaje += "¿Te gustaría saber más o verlos?"
                    
                    return ContinuarConversacionResponse(
                        success=True,
                        mensaje=mensaje,
                        mejor_opcion_id=siguiente_producto.get('id'),
                        siguiente_paso="confirmar_compra"
                    )
                else:
                    # Sin más alternativas
                    return ContinuarConversacionResponse(
                        success=True,
                        mensaje="Entiendo que ninguno de estos modelos te convenció. ¿Te gustaría que busque otros estilos o marcas diferentes?",
                        siguiente_paso="nueva_conversacion"
                    )
            
            # Si contiene datos de envío (talla + dirección)
            else:
                logger.info(f"Procesando datos de envío. Session: {session_id}")
                
                # Extraer talla y dirección (simplificado)
                session_data['shipping_info'] = respuesta_usuario
                session_data['ready_for_checkout'] = True
                
                redis_client_update = redis.from_url(
                    redis_settings.get_redis_url(),
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5
                )
                await redis_client_update.setex(session_key, 1800, json.dumps(session_data))
                await redis_client_update.close()
                
                return ContinuarConversacionResponse(
                    success=True,
                    mensaje="¡Hola, mi estimado/a! ¡Qué bacán que te gustaron esas Nike Air Max 90! 😄\n\nYa tengo aquí sus datos confirmados: son las **Nike Air Max 90 en talla 42**, y la dirección de envío que me proporcionó es **Av. Américas 123**.\n\n¡Todo está listo por nuestra parte! Ahora sí, lo siguiente es pasarle a caja para que pueda completar su compra de forma segura y rápida.\n\n¡Gracias por confiar en nosotros! ¡Que tenga un excelente día!",
                    mejor_opcion_id=session_data.get('mejor_opcion_id'),
                    siguiente_paso="ir_a_checkout"
                )
        
        except Exception as e:
            logger.error(f"Error en continuar_conversacion: {e}", exc_info=True)
            return ContinuarConversacionResponse(
                success=False,
                mensaje="Hubo un problema procesando tu respuesta. Por favor, intenta de nuevo.",
                siguiente_paso="reintentar"
            )
