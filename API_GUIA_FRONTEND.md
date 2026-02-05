Claro, aquí tienes el contenido del PDF convertido a markdown limpio y listo para usar. Lo he estructurado con títulos, tablas y bloques de código para que sea fácil de leer y copiar:

---

# Guía de API GraphQL – Módulo de Guion (Agente 2 → Agente 3)

**Documentación técnica para integración del flujo de recomendación basado en guiones del Agente**

---

## 📌 Resumen del Flujo

El sistema implementa un flujo conversacional de ventas con las siguientes etapas:

1. **Entrada de Guion**: Agente 2 (Visión/Reconocimiento) detecta productos y genera un guion con códigos de barras.  
2. **Recomendación**: Agente 3 (Ventas) procesa el guion, compara productos y recomienda el mejor.  
3. **Confirmación**: Usuario aprueba o rechaza la recomendación.  
4. **Datos de Envío**: Si aprueba, se solicita talla y dirección.  
5. **Checkout**: Con los datos completos, se redirige a la pantalla de pago.

---

## 🔁 Mutations GraphQL

### 1. `procesarGuionAgente2`

Inicia el flujo de ventas procesando un guion del Agente 2.

**Endpoint**: `POST /graphql`

**Input**: `GuionEntradaInput`

```graphql
mutation ProcesarGuion {
  procesarGuionAgente2(guion: {
    sessionId: "sess-unique-001"
    productos: [
      {
        codigoBarras: "7501234567891"
        nombreDetectado: "Nike Air Max 90"
        prioridad: "alta"
        motivoSeleccion: "Zapatilla clásica popular"
      },
      {
        codigoBarras: "7501234567894"
        nombreDetectado: "Nike Court Vision Low"
        prioridad: "media"
        motivoSeleccion: "Alternativa económica"
      }
    ]
    preferencias: {
      estiloComunicacion: "cuencano" # cuencano | juvenil | formal | neutral
      presupuestoMaximo: 150
      urgencia: "media" # alta | media | baja
      usoPrevisto: "Uso casual diario"
      buscaOfertas: true
    }
    contexto: {
      tipoEntrada: "texto" # texto | voz | imagen | mixta
      intencionPrincipal: "compra_directa" # compra_directa | comparar | información
      necesitaRecomendacion: true
    }
    textoOriginalUsuario: "Quiero unas zapatillas cómodas para caminar"
    resumenAnalisis: "Usuario busca zapatillas lifestyle para uso casual"
    confianzaProcesamiento: 0.92
  }) {
    success
    mensaje
    productos {
      id
      productName
      finalPrice
      unitCost
      isOnSale
      discountPercent
      recommendationScore
      reason
    }
    mejorOpcionId
    reasoning
    siguientePaso
  }
}
```

---

### ✅ Respuesta Exitosa

```json
{
  "data": {
    "procesarGuionAgente2": {
      "success": true,
      "mensaje": "Te recomiendo las Nike Air Max 90. Están en oferta a $104, te ahorras $26. Son perfectas para caminar por la ciudad. ¿Te interesan?",
      "productos": [
        {
          "id": "94d7c19b-856f-4f99-a6e6-553e0a1eac26",
          "productName": "Nike Air Max 90",
          "finalPrice": "104.0000",
          "unitCost": "130.00",
          "isOnSale": true,
          "discountPercent": "10.00",
          "recommendationScore": 85,
          "reason": "Producto de alta prioridad; Precio dentro del presupuesto; En oferta"
        },
        {
          "id": "849b045e-05a9-4613-9de3-2e2ef9d67f28",
          "productName": "Nike Court Vision Low",
          "finalPrice": "45.0000",
          "unitCost": "75.00",
          "isOnSale": true,
          "discountPercent": "20.00",
          "recommendationScore": 65,
          "reason": "Precio económico; 20% descuento"
        }
      ],
      "mejorOpcionId": "94d7c19b-856f-4f99-a6e6-553e0a1eac26",
      "reasoning": "Recomendación: Nike Air Max 90. Precio: $104.00 (antes $130.00). Razones: Producto prioridad alta, dentro de presupuesto, en oferta 10%",
      "siguientePaso": "confirmar_compra"
    }
  }
}
```

---

### 📋 Campos de Respuesta

| Campo            | Tipo     | Descripción |
|------------------|----------|-------------|
| `success`        | Boolean  | Indica si la operación fue exitosa |
| `mensaje`        | String   | Mensaje persuasivo generado por el LLM |
| `productos`      | Array    | Lista de productos con scores de recomendación |
| `mejorOpcionId`  | UUID     | ID del producto recomendado |
| `siguientePaso`  | String   | Próxima acción esperada |

---

### 🧠 Almacenamiento de Sesión

La mutación guarda automáticamente la sesión en Redis:

- **Key**: `session:{sessionId}`  
- **TTL**: 30 minutos  
- **Contenido**: Productos del guion, selección actual, estilo de comunicación

---

## 2. `continuarConversacion`

Continúa el flujo de ventas con la respuesta del usuario.

**Endpoint**: `POST /graphql`

### 🔧 Parámetros

| Parámetro         | Tipo   | Requerido | Descripción |
|-------------------|--------|-----------|-------------|
| `sessionId`       | String | Sí        | ID de sesión devuelto en `procesarGuionAgente2` |
| `respuestaUsuario`| String | Sí        | Texto de respuesta del usuario |

---

### ✅ Casos de Respuesta

#### Aprobación

```json
{
  "data": {
    "continuarConversacion": {
      "success": true,
      "mensaje": "¡Excelente! ¿Qué talla necesitas y a qué dirección te los enviamos?",
      "mejorOpcionId": "94d7c19b-856f-4f99-a6e6-553e0a1eac26",
      "siguientePaso": "solicitar_datos_envio"
    }
  }
}
```

#### Rechazo con alternativas

```json
{
  "data": {
    "continuarConversacion": {
      "success": true,
      "mensaje": "Entiendo. Entonces mira esta opción: Nike Court Vision Low a $45.00 (en oferta). ¿Te interesa?",
      "mejorOpcionId": "849b045e-05a9-4613-9de3-2e2ef9d67f28",
      "siguientePaso": "confirmar_compra"
    }
  }
}
```

#### Sin alternativas

```json
{
  "data": {
    "continuarConversacion": {
      "success": true,
      "mensaje": "Entiendo. No tengo más opciones de las que te mostré. ¿Quieres que hagamos una nueva búsqueda?",
      "mejorOpcionId": "00000000-0000-0000-0000-000000000000",
      "siguientePaso": "nueva_conversacion"
    }
  }
}
```

---

### 📬 Valores de `siguientePaso`

| Valor                  | Descripción | Acción del Frontend |
|------------------------|-------------|----------------------|
| `confirmar_compra`     | Esperando confirmación del usuario | Mostrar mensaje y opciones Si/No |
| `solicitar_datos_envio`| Usuario aprobó, se necesita talla y dirección | Mostrar formulario de envío |
| `ir_a_checkout`        | Datos completos, listo para pago | Redirigir a pantalla de checkout |
| `nueva_conversacion`   | Sin alternativas o sesión expirada | Ofrecer iniciar nueva búsqueda |

---

## 🔁 Flujos de Uso

### ✅ Flujo 1: Compra Directa (Usuario aprueba a la primera)

1. Frontend llama `procesarGuionAgente2`  
2. Recibe mensaje + `siguientePaso: "confirmar_compra"`  
3. Muestra mensaje con botones “Sí, me interesa” / “No, gracias”  
4. Usuario presiona “Sí, me interesa”  
5. Frontend llama `continuarConversacion` con `respuestaUsuario: "Sí me interesa"`  
6. Recibe `siguientePaso: "solicitar_datos_envio"`  
7. Muestra formulario de talla y dirección  
8. Usuario completa datos  
9. Frontend llama `continuarConversacion` con datos  
10. Recibe `siguientePaso: "ir_a_checkout"`  
11. Redirige a `/checkout?session=sess-unique-001`

---

### 🔁 Flujo 2: Usuario Rechaza y Selecciona Alternativa

(Sigue la misma lógica, pero con rechazo y segunda recomendación.)

---

### ❌ Flujo 3: Usuario Rechaza Todo

1. Usuario rechaza todas las opciones  
2. Backend devuelve `siguientePaso: "nueva_conversacion"`  
3. Frontend muestra mensaje “No tengo más opciones” + botón “Nueva búsqueda”  
4. Usuario presiona “Nueva búsqueda”  
5. Frontend redirige a pantalla de búsqueda o inicia nuevo flujo

---

## 🧩 Manejo de Sesiones

### Almacenamiento en Redis

- **Key**: `session:{session_id}`  
- **TTL**: 30 minutos (1800 segundos)  
- **Formato**: JSON serializado del estado de la conversación

### 📦 Ejemplo de Estructura de Sesión

```json
{
  "session_id": "sess-unique-001",
  "user_query": "Quiero zapatillas",
  "search_results": [
    {
      "id": "uuid-producto-1",
      "name": "Nike Air Max 90",
      "price": 104.00,
      "barcode": "7501234567891",
      "is_on_sale": true
    }
  ],
  "selected_products": ["uuid-producto-1"],
  "conversation_stage": "esperando_confirmacion",
  "metadata": {
    "estilo": "cuencano",
    "producto_recomendado": "Nike Air Max 90",
    "precio": 104.00
  },
  "created_at": "2026-02-05T15:30:00Z"
}
```

---

### ⏳ Manejo de Expiración

Si una sesión expira (30 minutos sin actividad):

```json
{
  "data": {
    "continuarConversacion": {
      "success": false,
      "mensaje": "La sesión expiró. Por favor, inicia una nueva conversación.",
      "siguientePaso": "nueva_conversacion"
    }
  }
}
```

**Acción del Frontend**: Mostrar mensaje de sesión expirada y botón para iniciar nueva búsqueda.

---

## 🧪 Tipos de Input GraphQL

### `GuionEntradaInput`

```graphql
input GuionEntradaInput {
  sessionId: String!
  productos: [ProductoEnGuionInput!]!
  preferencias: PreferenciasUsuarioInput!
  contexto: ContextoBusquedaInput!
  textoOriginalUsuario: String!
  resumenAnalisis: String!
  confianzaProcesamiento: Float!
}
```

### `ProductoEnGuionInput`

```graphql
input ProductoEnGuionInput {
  codigoBarras: String!
  nombreDetectado: String!
  marca: String
  categoria: String
  prioridad: String # alta | media | baja
  motivoSeleccion: String
}
```

### `PreferenciasUsuarioInput`

```graphql
input PreferenciasUsuarioInput {
  estiloComunicacion: String # cuencano | juvenil | formal | neutral
  usoPrevisto: String
  nivelActividad: String # alto | medio | bajo
  tallaPreferida: String
  colorPreferido: String
  presupuestoMaximo: Decimal
  buscaOfertas: Boolean
  urgencia: String # alta | media | baja
  caracteristicasImportantes: [String!]
}
```

### `ContextoBusquedaInput`

```graphql
input ContextoBusquedaInput {
  tipoEntrada: String! # texto | voz | imagen | mixta
  productoMencionadoExplicitamente: Boolean
  necesitaRecomendacion: Boolean!
  intencionPrincipal: String! # compra_directa | comparar | informacion
  restriccionesAdicionales: [String!]
}
```

---

## 📤 Tipos de Respuesta GraphQL

### `RecomendacionResponse`

```graphql
type RecomendacionResponse {
  success: Boolean!
  mensaje: String!
  productos: [ProductComparisonType!]!
  mejorOpcionId: UUID!
  reasoning: String!
  siguientePaso: String!
}
```

### `ProductComparisonType`

```graphql
type ProductComparisonType {
  id: UUID!
  productName: String!
  barcode: String
  brand: String
  category: String
  unitCost: Decimal!
  finalPrice: Decimal!
  savingsAmount: Decimal!
  isOnSale: Boolean!
  discountPercent: Decimal
  promotionDescription: String
  quantityAvailable: Int!
  recommendationScore: Float!
  reason: String!
}
```

---

## 🔐 Headers Requeridos

Todas las mutations requieren autenticación JWT:

```
Authorization: Bearer {token_jwt}
Content-Type: application/json
```

### Obtener token vía REST:

```http
POST /auth/login
{
  "username": "Cliente1",
  "password": "cliente123"
}
```

---

## 📦 Ejemplo de Integración Completa (React)

```javascript
// 1. Iniciar conversación
const iniciarConversacion = async (guion) => {
  const response = await fetch('/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      query: `
        mutation ProcesarGuion($guion: GuionEntradaInput!) {
          procesarGuionAgente2(guion: $guion) {
            success
            mensaje
            mejorOpcionId
            siguientePaso
          }
        }
      `,
      variables: { guion }
    })
  });
  const data = await response.json();
  if (data.data.procesarGuionAgente2.siguientePaso === 'confirmar_compra') {
    // Mostrar mensaje y botones Si/No
  }
};

// 2. Manejar respuesta del usuario
const manejarRespuestaUsuario = async (sessionId, respuesta) => {
  const response = await fetch('/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      query: `
        mutation Continuar($sessionId: String!, $respuesta: String!) {
          continuarConversacion(
            sessionId: $sessionId
            respuestaUsuario: $respuesta
          ) {
            success
            mensaje
            siguientePaso
          }
        }
      `,
      variables: { sessionId, respuesta }
    })
  });
  const data = await response.json();
  const { siguientePaso, mensaje } = data.data.continuarConversacion;

  switch (siguientePaso) {
    case 'confirmar_compra':
      mostrarRecomendacion(mensaje);
      break;
    case 'solicitar_datos_envio':
      mostrarFormularioDatosEnvio(mensaje);
      break;
    case 'ir_a_checkout':
      window.location.href = `/checkout?session=${sessionId}`;
      break;
    case 'nueva_conversacion':
      mostrarOpcionNuevaBusqueda(mensaje);
      break;
  }
};
```

---

## ⚠️ Consideraciones Importantes

1. **Persistencia de Session ID**: El frontend debe almacenar el `sessionId` entre llamadas.  
2. **Manejo de Errores**: Siempre verificar el campo `success` antes de procesar la respuesta.  
3. **Timeout de Sesión**: Si la sesión expira (30 minutos), el usuario debe iniciar un nuevo flujo.  
4. **Rechazos Múltiples**:  
   - Si el guion solo tiene 1 producto y el usuario rechaza → `nueva_conversacion`.  
   - Si tiene 2+ productos → se recomienda el segundo.  
5. **Estilos de Comunicación**: El mensaje generado por el LLM varía según `estiloComunicacion` (cuencano, juvenil, formal, neutral).

---

## 🧭 Diagrama de Estados del Frontend

```plaintext
[INICIO]
   |
   v
[procesarGuionAgente2] --> ¿Error? --> [Mostrar Error]
   |
   v
[MOSTRAR RECOMENDACION] <-- Si rechaza y hay alternativas --
   |        |
   | Acepta |
   v        v
[SOLICITAR DATOS ENVIO]    [CONFIRMAR CHECKOUT]
   |                           |
   | Datos ingresados          |
   v                           v
[REDIRIGIR A CHECKOUT]    [SIN ALTERNATIVAS]
   |                           |
   | Rechaza todo              |
   v                           v
[OFRECER NUEVA BÚSQUEDA] <----+
```

---

**Documentación generada: Febrero 2026**

---

¿Quieres que lo guarde como archivo `.md` o necesitas alguna sección adaptada a otro formato?