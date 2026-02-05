"""
Mutations GraphQL para operaciones de escritura.
Crear, actualizar y eliminar recursos.
"""
from typing import Annotated, List, Optional
from uuid import UUID

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
    # USUARIOS
    # ========================================================================
    
    @strawberry.mutation
    @inject
    async def create_user(
        self,
        input: CreateUserInput,
        user_service: Annotated[UserService, Inject]
    ) -> AuthResponse:
        """
        Registra un nuevo usuario en el sistema.
        
        No requiere autenticación (endpoint público para registro).
        """
        try:
            user, message = await user_service.create_user(
                username=input.username,
                email=input.email,
                password=input.password,
                full_name=input.full_name,
                role=input.role
            )
            
            # Generar token JWT para el usuario creado
            token_data = {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role
            }
            access_token = securityJWT.create_access_token(token_data, token_data)
            
            return AuthResponse(
                success=True,
                access_token=access_token,
                user=UserType(
                    id=user.id,
                    username=user.username,
                    email=user.email,
                    full_name=user.full_name,
                    role=user.role,
                    is_active=user.is_active,
                    created_at=user.created_at
                )
            )
            
        except UserAlreadyExistsError as e:
            logger.warning(f"Intento de registro con datos duplicados: {e}")
            return AuthResponse(
                success=False,
                error=str(e)
            )
            
        except Exception as e:
            logger.error(f"Error creando usuario: {e}", exc_info=True)
            return AuthResponse(
                success=False,
                error="Error interno del servidor"
            )
    
    @strawberry.mutation
    @inject
    async def update_user(
        self,
        input: UpdateUserInput,
        user_service: Annotated[UserService, Inject],
        info: Info
    ) -> UserType:
        """
        Actualiza los datos del usuario autenticado.
        
        Requiere autenticación.
        """
        current_user = get_current_user(info)
        if not current_user:
            raise Exception("No autenticado")
        
        user_id = UUID(current_user["id"])
        
        try:
            user, message = await user_service.update_user(
                user_id=user_id,
                full_name=input.full_name,
                email=input.email,
                is_active=input.is_active
            )
            
            return UserType(
                id=user.id,
                username=user.username,
                email=user.email,
                full_name=user.full_name,
                role=user.role,
                is_active=user.is_active,
                created_at=user.created_at
            )
            
        except UserNotFoundError:
            raise Exception("Usuario no encontrado")
            
        except Exception as e:
            logger.error(f"Error actualizando usuario: {e}")
            raise Exception("Error interno del servidor")
    
    @strawberry.mutation
    @inject
    async def change_password(
        self,
        input: ChangePasswordInput,
        user_service: Annotated[UserService, Inject],
        info: Info
    ) -> bool:
        """
        Cambia la contraseña del usuario autenticado.
        
        Requiere autenticación.
        """
        current_user = get_current_user(info)
        if not current_user:
            raise Exception("No autenticado")
        
        user_id = UUID(current_user["id"])
        
        success, message = await user_service.change_password(
            user_id=user_id,
            old_password=input.old_password,
            new_password=input.new_password
        )
        
        if not success:
            raise Exception(message)
        
        return True
    
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
    # RECONOCIMIENTO DE PRODUCTOS (AGENTE 2 - SIFT/ML)
    # ========================================================================
    
    @strawberry.mutation
    async def recognize_product_image(
        self,
        info: Info,
        image: strawberry.file_uploads.Upload
    ) -> ProductRecognitionResponse:
        """
        Reconoce un producto a partir de una imagen usando el Agente 2.
        
        Este endpoint utiliza SIFT (Scale-Invariant Feature Transform) para
        identificar productos por sus características visuales.
        
        Requiere autenticación.
        
        Args:
            image: Archivo de imagen (JPEG, PNG)
            
        Returns:
            ProductRecognitionResponse con el producto identificado o error
            
        Example:
            mutation {
                recognizeProductImage(image: $file) {
                    success
                    productName
                    confidence
                    matches
                }
            }
        """
        # Verificar autenticación
        current_user = get_current_user(info)
        if not current_user:
            return ProductRecognitionResponse(
                success=False,
                error="Debes iniciar sesión para usar esta función"
            )
        
        # Verificar si el Agente 2 está habilitado
        if os.getenv("AGENT2_ENABLED", "true").lower() != "true":
            return ProductRecognitionResponse(
                success=False,
                error="El servicio de reconocimiento de imágenes está deshabilitado"
            )
        
        try:
            logger.info(
                f"Recognizing product from image for user {current_user.get('username')}"
            )
            
            # Leer bytes de la imagen
            image_bytes = await image.read()
            
            if not image_bytes:
                return ProductRecognitionResponse(
                    success=False,
                    error="No se pudo leer la imagen"
                )
            
            # Llamar al Agente 2
            client = ProductRecognitionClient()
            try:
                result = await client.recognize_product(
                    image_bytes=image_bytes,
                    filename=getattr(image, 'filename', 'image.jpg')
                )
                
                return ProductRecognitionResponse(
                    success=result["success"],
                    product_name=result["product_name"],
                    matches=result["matches"],
                    confidence=result["confidence"],
                    error=result.get("error")
                )
                
            finally:
                await client.close()
                
        except Exception as e:
            logger.error(f"Error en recognize_product_image: {e}", exc_info=True)
            return ProductRecognitionResponse(
                success=False,
                error="Error interno procesando la imagen"
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
            
            # Guardar sesión en Redis para continuar conversación
            try:
                agent_state = AgentState(
                    session_id=guion.session_id,
                    user_query=guion.texto_original_usuario,
                    search_results=[{
                        "id": str(p.id),
                        "name": p.product_name,
                        "price": float(p.final_price),
                        "barcode": p.barcode,
                        "is_on_sale": p.is_on_sale
                    } for p in recommendation.products],
                    selected_products=[str(recommendation.best_option_id)],
                    conversation_stage="esperando_confirmacion",
                    metadata={
                        "estilo": guion.preferencias.estilo_comunicacion,
                        "producto_recomendado": best_product.product_name,
                        "precio": float(best_product.final_price)
                    }
                )
                await session_service.save_session(guion.session_id, agent_state)
                logger.info(f"Sesión guardada: {guion.session_id}")
            except Exception as e:
                logger.error(f"Error guardando sesión: {e}")
            
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
    
    @strawberry.mutation
    @inject
    async def continuar_conversacion(
        self,
        info: Info,
        session_id: str,
        respuesta_usuario: str,
        session_service: Annotated[SessionService, Inject],
        product_service: Annotated[ProductService, Inject],
        llm_provider: Annotated[LLMProvider, Inject],
    ) -> RecomendacionResponse:
        """
        Continúa una conversación guardada en sesión.
        
        Flujo:
        1. Recupera sesión de Redis
        2. Procesa respuesta del usuario (sí/no)
        3. Si aprueba: pide talla y dirección, o crea orden si ya tiene datos
        4. Si rechaza: vuelve a recomendar o pregunta qué quiere
        
        Args:
            session_id: ID de sesión de la conversación anterior
            respuesta_usuario: Texto de respuesta del usuario
            
        Returns:
            RecomendacionResponse con siguiente mensaje
        """
        from langchain_core.messages import HumanMessage, SystemMessage
        
        # 1. Recuperar sesión
        state = await session_service.get_session(session_id)
        if not state:
            return RecomendacionResponse(
                success=False,
                mensaje="La sesión expiró. Por favor, inicia una nueva conversación.",
                productos=[],
                mejor_opcion_id=UUID("00000000-0000-0000-0000-000000000000"),
                reasoning="Sesión no encontrada",
                siguiente_paso="nueva_conversacion"
            )
        
        estilo = state.metadata.get("estilo", "neutral")
        producto_nombre = state.metadata.get("producto_recomendado", "el producto")
        precio = state.metadata.get("precio", 0)
        
        # 2. Analizar intención del usuario
        respuesta_lower = respuesta_usuario.lower()
        
        # Palabras de aprobación
        aprobaciones = ["sí", "si", "ok", "dale", "perfecto", "me gusta", "interesa", "lo quiero", "comprar", "adelante"]
        # Palabras de rechazo
        rechazos = ["no", "no gracias", "otro", "diferente", "no me gusta", "paso", "rechazar"]
        # Datos de envío (talla, dirección)
        tiene_talla = any(palabra in respuesta_lower for palabra in ["talla", "calzo", "número", "numero", "size"])
        tiene_direccion = any(palabra in respuesta_lower for palabra in ["dirección", "direccion", "calle", "casa", "departamento", "apt", "piso"])
        
        es_aprobacion = any(aprob in respuesta_lower for aprob in aprobaciones)
        es_rechazo = any(rech in respuesta_lower for rech in rechazos)
        
        # 3. Generar respuesta según intención
        if es_aprobacion or (state.conversation_stage == "esperando_datos_envio" and (tiene_talla or tiene_direccion)):
            # Usuario aprueba o está dando datos de envío
            
            if state.conversation_stage == "esperando_confirmacion":
                # Primera aprobación - pedir datos de envío
                state.conversation_stage = "esperando_datos_envio"
                await session_service.save_session(session_id, state)
                
                # Generar mensaje pidiendo datos
                system_prompts = {
                    "cuencano": "Eres un vendedor ecuatoriano cálido. Pide talla y dirección de forma natural, como hablando con un amigo.",
                    "juvenil": "Eres un vendedor joven y casual. Pide talla y dirección de forma directa.",
                    "formal": "Eres un vendedor profesional. Pide talla y dirección de forma educada.",
                    "neutral": "Eres un vendedor amigable. Pide talla y dirección de forma natural."
                }
                
                prompt = f"El usuario quiere comprar {producto_nombre} a ${precio:.2f}. Pídele la talla y dirección de envío en una sola pregunta natural."
                
                try:
                    messages = [
                        SystemMessage(content=system_prompts.get(estilo, system_prompts["neutral"])),
                        HumanMessage(content=prompt)
                    ]
                    response = await llm_provider.model.ainvoke(messages)
                    mensaje = response.content.strip()
                except:
                    mensaje = "¡Excelente! Para completar tu compra, ¿qué talla necesitas y a qué dirección te los enviamos?"
                
                return RecomendacionResponse(
                    success=True,
                    mensaje=mensaje,
                    productos=[],
                    mejor_opcion_id=UUID(state.selected_products[0]) if state.selected_products else UUID("00000000-0000-0000-0000-000000000000"),
                    reasoning="Esperando datos de envío",
                    siguiente_paso="solicitar_datos_envio"
                )
                
            elif state.conversation_stage == "esperando_datos_envio":
                # Usuario proporcionó datos - confirmar y enviar a checkout
                
                # Extraer talla y dirección (simplificado)
                # En producción usarías NLP más sofisticado
                state.metadata["datos_envio"] = respuesta_usuario
                state.conversation_stage = "listo_para_checkout"
                await session_service.save_session(session_id, state)
                
                system_prompts = {
                    "cuencano": "Eres un vendedor ecuatoriano. Confirma los datos y di que va a pasar a caja de forma cálida.",
                    "juvenil": "Eres un vendedor joven. Confirma y di que va a pasar a caja.",
                    "formal": "Eres un vendedor profesional. Confirma los datos y confirma el paso a checkout.",
                    "neutral": "Eres un vendedor amigable. Confirma y di que va a pasar a caja."
                }
                
                prompt = f"Confirma que recibiste estos datos: '{respuesta_usuario}' para {producto_nombre}. Di que todo listo y que va a pasar a completar la compra en caja."
                
                try:
                    messages = [
                        SystemMessage(content=system_prompts.get(estilo, system_prompts["neutral"])),
                        HumanMessage(content=prompt)
                    ]
                    response = await llm_provider.model.ainvoke(messages)
                    mensaje = response.content.strip()
                except:
                    mensaje = f"¡Perfecto! Recibí tus datos. Ahora te llevo a completar la compra de {producto_nombre}."
                
                return RecomendacionResponse(
                    success=True,
                    mensaje=mensaje,
                    productos=[],
                    mejor_opcion_id=UUID(state.selected_products[0]) if state.selected_products else UUID("00000000-0000-0000-0000-000000000000"),
                    reasoning="Listo para checkout",
                    siguiente_paso="ir_a_checkout"
                )
                
        elif es_rechazo:
            # Usuario rechazó - preguntar qué quiere o buscar alternativas
            state.conversation_stage = "buscando_alternativas"
            await session_service.save_session(session_id, state)
            
            system_prompts = {
                "cuencano": "Eres un vendedor ecuatoriano. Pregunta qué no le gustó o qué busca de forma cálida.",
                "juvenil": "Eres un vendedor joven. Pregunta qué busca de forma casual.",
                "formal": "Eres un vendedor profesional. Pregunta qué necesita diferente.",
                "neutral": "Eres un vendedor amigable. Pregunta qué busca."
            }
            
            prompt = f"El usuario no quiso {producto_nombre}. Pregúntale qué no le convenció o qué otro tipo de producto busca."
            
            try:
                messages = [
                    SystemMessage(content=system_prompts.get(estilo, system_prompts["neutral"])),
                    HumanMessage(content=prompt)
                ]
                response = await llm_provider.model.ainvoke(messages)
                mensaje = response.content.strip()
            except:
                mensaje = "Entiendo. ¿Qué es lo que buscas? Puedo mostrarte otras opciones."
            
            return RecomendacionResponse(
                success=True,
                mensaje=mensaje,
                productos=[],
                mejor_opcion_id=UUID("00000000-0000-0000-0000-000000000000"),
                reasoning="Buscando alternativas",
                siguiente_paso="nueva_recomendacion"
            )
            
        else:
            # Respuesta no clara - pedir clarificación
            return RecomendacionResponse(
                success=True,
                mensaje="¿Te interesa este producto o prefieres ver otras opciones?",
                productos=[],
                mejor_opcion_id=UUID(state.selected_products[0]) if state.selected_products else UUID("00000000-0000-0000-0000-000000000000"),
                reasoning="Esperando clarificación",
                siguiente_paso="confirmar_intencion"
            )
