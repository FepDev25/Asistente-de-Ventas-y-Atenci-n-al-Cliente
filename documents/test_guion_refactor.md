# 🧪 Guía de Testing - Refactorización del Guion (Agente 2 → Agente 3)

Este documento describe cómo probar el nuevo flujo de trabajo donde:
- **Agente 2** (Visión/Reconocimiento) detecta productos y genera un "guion"
- **Agente 3** (Ventas/Persuasión) recibe el guion, compara productos y genera respuestas persuasivas

---

## 📋 Pre-requisitos

```bash
# 1. Asegurar que la BD está reiniciada con productos y barcodes
./reset_database.sh

# 2. Iniciar el servidor
uv run -m backend.main

# 3. Verificar que el servidor está corriendo en http://localhost:8000
```

---

## 🔑 1. Autenticación

La autenticación se realiza por **REST API** (no GraphQL). Obtén el token JWT:

### Paso 1: Login vía REST

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Cliente1",
    "password": "cliente123"
  }'
```

**Respuesta esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### Paso 2: Usar token en GraphQL

Copia el `access_token` y úsalo en los headers de GraphQL:

**Headers requeridos:**
```json
{
  "Authorization": "Bearer eyJhbGciOiJIUzI1NiIs..."
}
```

> 💡 **Tip:** En GraphQL Playground (http://localhost:8000/graphql), haz clic en "HTTP HEADERS" en la parte inferior y pega el header con tu token.

---

## 🎯 2. Flujo Principal: Procesar Guion del Agente 2

### Mutación: `procesarGuionAgente2`

**⚠️ IMPORTANTE:** Strawberry convierte automáticamente snake_case → camelCase en GraphQL:
- `session_id` → `sessionId`
- `codigo_barras` → `codigoBarras`

---

#### Caso 2.1: Un solo producto detectado

```graphql
mutation ProcesarGuionUnProducto {
  procesarGuionAgente2(
    guion: {
      sessionId: "test-session-001"
      productos: [
        {
          codigoBarras: "7501234567891"
          nombreDetectado: "Nike Air Max 90"
          prioridad: "alta"
          motivoSeleccion: "Cliente mostró interés en zapatillas clásicas"
        }
      ]
      preferencias: {
        estiloComunicacion: "cuencano"
        presupuestoMaximo: 200
        urgencia: "media"
        usoPrevisto: "Uso casual diario, caminar por la ciudad"
        buscaOfertas: true
      }
      contexto: {
        tipoEntrada: "texto"
        intencionPrincipal: "compra_directa"
        necesitaRecomendacion: true
      }
      textoOriginalUsuario: "Estoy buscando unas zapatillas cómodas para caminar"
      resumenAnalisis: "Usuario busca zapatillas lifestyle para uso casual"
      confianzaProcesamiento: 0.92
    }
  ) {
    success
    mensaje
    productos {
      productName
      unitCost
      finalPrice
      recommendationScore
      reason
    }
    mejorOpcionId
    reasoning
    siguientePaso
  }
}
```

**✅ Resultado esperado:**
- Respuesta persuasiva detallada del Agente 3
- Mensaje personalizado considerando el contexto "uso casual diario"
- Si hay descuento (Nike Air Max 90 tiene 10% OFF), debe mencionarlo

---

#### Caso 2.2: Múltiples productos (comparación)

```graphql
mutation ProcesarGuionMultiplesProductos {
  procesarGuionAgente2(
    guion: {
      sessionId: "test-session-002"
      productos: [
        {
          codigoBarras: "7501234567891"
          nombreDetectado: "Nike Air Max 90"
          prioridad: "alta"
          motivoSeleccion: "Zapatilla clásica, buen precio"
        }
        {
          codigoBarras: "7501234567895"
          nombreDetectado: "Nike Air Force 1"
          prioridad: "media"
          motivoSeleccion: "Muy popular, estilo icónico"
        }
        {
          codigoBarras: "7501234567894"
          nombreDetectado: "Nike Court Vision Low"
          prioridad: "baja"
          motivoSeleccion: "Alternativa económica con descuento"
        }
      ]
      preferencias: {
        estiloComunicacion: "neutral"
        presupuestoMaximo: 150
        urgencia: "baja"
        usoPrevisto: "Regalo para hermano de 25 años"
        buscaOfertas: true
      }
      contexto: {
        tipoEntrada: "imagen"
        intencionPrincipal: "comparar"
        necesitaRecomendacion: true
      }
      textoOriginalUsuario: "Mostré una foto de zapatillas Nike y necesito ayuda para elegir"
      resumenAnalisis: "Usuario comparando 3 modelos Nike lifestyle para regalo"
      confianzaProcesamiento: 0.88
    }
  ) {
    success
    mensaje
    productos {
      productName
      unitCost
      finalPrice
      recommendationScore
      reason
      isOnSale
      discountPercent
    }
    mejorOpcionId
    reasoning
    siguientePaso
  }
}
```

**✅ Resultado esperado:**
- Comparación de los 3 productos
- Análisis de precio-calidad
- Recomendación del "mejor" producto basado en:
  - Precio (dentro del presupuesto de $150)
  - Descuento (Court Vision tiene 20% OFF)
  - Popularidad/estilo (para regalo de 25 años)

---

#### Caso 2.3: Producto con promoción activa

```graphql
mutation ProcesarGuionConPromocion {
  procesarGuionAgente2(
    guion: {
      sessionId: "test-session-003"
      productos: [
        {
          codigoBarras: "8884071234567"
          nombreDetectado: "Calcetines Nike Crew Performance"
          prioridad: "alta"
          motivoSeleccion: "Accesorio complementario"
        }
      ]
      preferencias: {
        estiloComunicacion: "cuencano"
        presupuestoMaximo: 20
        urgencia: "alta"
        usoPrevisto: "Necesito para entrenamiento de mañana"
        buscaOfertas: true
      }
      contexto: {
        tipoEntrada: "texto"
        intencionPrincipal: "compra_directa"
        necesitaRecomendacion: false
      }
      textoOriginalUsuario: "Necesito calcetines para correr urgentemente"
      resumenAnalisis: "Usuario busca calcetines running con urgencia"
      confianzaProcesamiento: 0.95
    }
  ) {
    success
    mensaje
    productos {
      productName
      unitCost
      finalPrice
      isOnSale
      discountPercent
    }
    mejorOpcionId
    reasoning
    siguientePaso
  }
}
```

**✅ Resultado esperado:**
- Mensaje persuasivo mencionando el **25% de descuento**
- Énfasis en la urgencia ("para entrenamiento de mañana")
- Destacar características técnicas (Dri-FIT)

---

## 📊 3. Verificación de Datos (Queries Disponibles)

### 3.1 Listar todos los productos

```graphql
query ListarProductos {
  listProducts(limit: 50) {
    id
    productName
    barcode
    brand
    category
    unitCost
    finalPrice
    quantityAvailable
    stockStatus
    isOnSale
    discountPercent
    savingsAmount
    promotionDescription
    warehouseLocation
  }
}
```

> **Nota:** Si retorna lista vacía, verifica que la BD tenga productos (`./reset_database.sh`)

---

### 3.2 Buscar producto por ID

```graphql
query ProductoPorId {
  getProductById(id: "uuid-del-producto-aqui") {
    id
    productName
    barcode
    unitCost
    finalPrice
    quantityAvailable
    isOnSale
    discountPercent
  }
}
```

---

### 3.3 Chat con el Agente (semanticSearch)

```graphql
query ChatAgente {
  semanticSearch(
    query: "Quiero ver zapatillas Nike en oferta"
    sessionId: "test-session-chat"
  ) {
    answer
    query
    error
  }
}
```

---

## 🔄 4. Flujo Completo: Detección → Guion → Venta

```graphql
mutation FlujoCompleto {
  procesarGuionAgente2(
    guion: {
      sessionId: "session-demo-001"
      productos: [
        {
          codigoBarras: "7501234567896"
          nombreDetectado: "Nike Revolution 7"
          prioridad: "alta"
          motivoSeleccion: "Running diario, buen precio con descuento"
        }
        {
          codigoBarras: "7501234567892"
          nombreDetectado: "Nike React Infinity Run 4"
          prioridad: "media"
          motivoSeleccion: "Mayor amortiguación para largas distancias"
        }
      ]
      preferencias: {
        estiloComunicacion: "neutral"
        presupuestoMaximo: 120
        urgencia: "media"
        usoPrevisto: "Entreno 3 veces por semana, 5-10km"
        buscaOfertas: true
      }
      contexto: {
        tipoEntrada: "texto"
        intencionPrincipal: "comparar"
        necesitaRecomendacion: true
      }
      textoOriginalUsuario: "Necesito zapatillas para correr 10km, algo cómodo"
      resumenAnalisis: "Usuario runner amateur buscando zapatillas para entrenamiento regular"
      confianzaProcesamiento: 0.89
    }
  ) {
    success
    mensaje
    productos {
      productName
      unitCost
      finalPrice
      recommendationScore
      reason
      isOnSale
      discountPercent
    }
    mejorOpcionId
    reasoning
    siguientePaso
  }
}
```

---

## ✅ 5. Checklist de Verificación

### Funcionalidad del Guion

- [ ] El guion acepta múltiples productos con barcodes
- [ ] El guion incluye preferencias del usuario (estilo, presupuesto, urgencia)
- [ ] El guion incluye contexto de entrada (tipo, intención)
- [ ] El texto original del usuario se preserva

### Respuesta del Agente 3

- [ ] Para **un producto**: mensaje persuasivo detallado (>50 palabras)
- [ ] Para **múltiples productos**: comparación y recomendación del mejor
- [ ] Se mencionan **descuentos y promociones** activas
- [ ] Se considera el **contexto del usuario** (uso, urgencia, etc.)
- [ ] Se indica el **siguiente paso** (ej: "agregar_al_carrito", "finalizar_compra")

### Validaciones

- [ ] Error si el barcode no existe en la BD
- [ ] Error si el sessionId está vacío
- [ ] Error si no hay productos en el guion
- [ ] Requiere autenticación (sin token debe dar error)

---

## 🔧 6. Casos Edge/Error

### Caso 6.1: Barcode inexistente

```graphql
mutation BarcodeInexistente {
  procesarGuionAgente2(
    guion: {
      sessionId: "test-error-001"
      productos: [
        {
          codigoBarras: "9999999999999"
          nombreDetectado: "Producto Inexistente"
          prioridad: "alta"
          motivoSeleccion: "Test de error"
        }
      ]
      preferencias: {
        estiloComunicacion: "neutral"
        urgencia: "media"
      }
      contexto: {
        tipoEntrada: "texto"
        intencionPrincipal: "compra_directa"
        necesitaRecomendacion: true
      }
      textoOriginalUsuario: "Test"
      resumenAnalisis: "Test error"
      confianzaProcesamiento: 0.5
    }
  ) {
    success
    mensaje
    siguientePaso
  }
}
```

**✅ Esperado:** `success: false`, mensaje de error indicando producto no encontrado

---

### Caso 6.2: Sin autenticación

Intenta la query del Caso 2.1 **sin** el header `Authorization`.

**✅ Esperado:** 
```json
{
  "success": false,
  "mensaje": "Debes iniciar sesión",
  "siguientePaso": "login"
}
```

---

## 📈 7. Métricas de Comparación

| Escenario | Productos | Descuentos | Urgencia | Respuesta Esperada |
|-----------|-----------|------------|----------|-------------------|
| Búsqueda simple | 1 | No | Media | Persuasión directa |
| Comparación | 2-3 | Mixto | Baja | Análisis comparativo |
| Oferta urgente | 1 | Sí (25%) | Alta | Énfasis en descuento + stock |
| Regalo | 2-3 | Sí | Baja | Estilo + valor percibido |

---

## 🚀 Comandos Rápidos

```bash
# Reset completo de BD
./reset_database.sh

# Iniciar servidor
uv run -m backend.main

# Ver logs del servidor
docker logs -f sales_agent_db

# Test de login REST
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "Cliente1", "password": "cliente123"}'

# Luego usa el token en GraphQL:
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token_aqui>" \
  -d '{"query": "query { listProducts(limit: 10) { productName unitCost } }"}'
```

---

## 📚 Referencias

- **Schema GraphQL:** Ver `backend/api/graphql/types.py`
- **Mutations:** `backend/api/graphql/mutations.py`
- **Queries:** `backend/api/graphql/queries.py`
- **SalesAgent:** `backend/agents/sales_agent.py`
- **ProductComparisonService:** `backend/services/product_comparison.py`
- **Modelo ProductStock:** `backend/database/models/product_stock.py`

---

## 🎨 Mapeo de Campos (IMPORTANTE)

Strawberry convierte automáticamente `snake_case` → `camelCase`:

### Inputs (GuionEntradaInput)

| Python (snake_case) | GraphQL (camelCase) |
|---------------------|---------------------|
| `session_id` | `sessionId` |
| `codigo_barras` | `codigoBarras` |
| `nombre_detectado` | `nombreDetectado` |
| `motivo_seleccion` | `motivoSeleccion` |
| `estilo_comunicacion` | `estiloComunicacion` |
| `presupuesto_maximo` | `presupuestoMaximo` |
| `uso_previsto` | `usoPrevisto` |
| `busca_ofertas` | `buscaOfertas` |
| `tipo_entrada` | `tipoEntrada` |
| `intencion_principal` | `intencionPrincipal` |
| `necesita_recomendacion` | `necesitaRecomendacion` |
| `texto_original_usuario` | `textoOriginalUsuario` |
| `resumen_analisis` | `resumenAnalisis` |
| `confianza_procesamiento` | `confianzaProcesamiento` |

### Outputs (Respuestas)

| Python (snake_case) | GraphQL (camelCase) |
|---------------------|---------------------|
| `product_name` | `productName` |
| `unit_cost` | `unitCost` |
| `final_price` | `finalPrice` |
| `recommendation_score` | `recommendationScore` |
| `mejor_opcion_id` | `mejorOpcionId` |
| `siguiente_paso` | `siguientePaso` |
| `discount_percent` | `discountPercent` |
| `is_on_sale` | `isOnSale` |
| `savings_amount` | `savingsAmount` |
| `promotion_description` | `promotionDescription` |
| `quantity_available` | `quantityAvailable` |
| `stock_status` | `stockStatus` |
| `warehouse_location` | `warehouseLocation` |

---

## 📝 Queries y Mutations Disponibles

### Queries (Consultas)

| Query | Parámetros | Descripción |
|-------|------------|-------------|
| `listProducts` | `limit: Int` | Lista todos los productos |
| `getProductById` | `id: UUID` | Producto por ID |
| `getCurrentUser` | - | Usuario autenticado |
| `getUserById` | `id: UUID` | Usuario por ID |
| `getOrderById` | `id: UUID` | Orden por ID |
| `getMyOrders` | - | Órdenes del usuario |
| `getRecentOrders` | `limit: Int` | Órdenes recientes |
| `semanticSearch` | `query: String, sessionId: String` | Chat con IA |

### Mutations (Modificaciones)

| Mutation | Input | Descripción |
|----------|-------|-------------|
| `createUser` | `input: CreateUserInput` | Registro de usuario |
| `procesarGuionAgente2` | `guion: GuionEntradaInput` | Procesar guion Agente 2 |
| `createOrder` | `input: CreateOrderInput` | Crear pedido |
| `cancelOrder` | `orderId: UUID, reason: String` | Cancelar pedido |
| `recognizeProductImage` | `imageBase64: String` | Reconocer producto por imagen |
| `updateUser` | `input: UpdateUserInput` | Actualizar perfil |
| `changePassword` | `input: ChangePasswordInput` | Cambiar contraseña |

---

*Última actualización: Febrero 2026*
