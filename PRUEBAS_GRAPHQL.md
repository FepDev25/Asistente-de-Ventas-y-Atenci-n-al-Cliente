# 🧪 Pruebas GraphQL - Formato para GraphQL Playground

## 📋 Qué es esto?

La documentación que te dieron muestra cómo usar el **endpoint GraphQL** para chatear con Alex.

**URL**: http://localhost:8000/graphql

**Endpoint**: `semanticSearch` - Este es el "cerebro" que conecta con los agentes (Retriever, Sales, Checkout)

**Parámetros**:
- `query` (String, requerido): La pregunta del usuario
- `sessionId` (String, opcional): ID de sesión para mantener contexto entre mensajes

---

## 🚀 Cómo Usar

1. **Abre GraphQL Playground**: http://localhost:8000/graphql
2. **Copia la query base** (Panel izquierdo)
3. **Copia las variables** (Panel inferior izquierdo "Query Variables")
4. **Presiona el botón ▶ Play**
5. **Ve la respuesta** (Panel derecho)

---

## 📝 QUERY BASE (Copiar en panel izquierdo)

```graphql
query Chat($query: String!, $sessionId: String) {
  semanticSearch(query: $query, sessionId: $sessionId) {
    answer
    query
    error
  }
}
```

**Nota**: Esta query la usas para TODAS las pruebas. Solo cambias las variables.

---

## 🎯 SECCIÓN 1: RAG - Preguntas Frecuentes

### Test 1.1: Política de Devoluciones

**Variables** (copiar en "Query Variables"):
```json
{
  "query": "¿Cuál es la política de devoluciones?",
  "sessionId": "test-session-001"
}
```

**Esperas en `answer`**: Plazo de 30 días, condiciones, proceso

---

### Test 1.2: Métodos de Pago

**Variables**:
```json
{
  "query": "¿Qué formas de pago aceptan?",
  "sessionId": "test-session-001"
}
```

**Esperas**: Lista de métodos, seguridad

---

### Test 1.3: Tiempos de Envío

**Variables**:
```json
{
  "query": "¿Cuánto tarda el envío?",
  "sessionId": "test-session-001"
}
```

**Esperas**: Tiempo estimado, opciones

---

### Test 1.4: Garantía

**Variables**:
```json
{
  "query": "¿Los productos tienen garantía?",
  "sessionId": "test-session-001"
}
```

**Esperas**: Duración, cobertura, proceso

RESULTADO: {
  "data": {
    "semanticSearch": {
      "answer": "Garantía de autenticidad 100%. Sneakers originales: 6 meses defectos de fábrica. Cambios y devoluciones: 15 días con etiquetas. Servicios: Limpieza profesional $8, protección waterproof $5.",
      "query": "¿Los productos tienen garantía?",
      "error": null
    }
  }
}
---

### Test 1.5: Horarios

**Variables**:
```json
{
  "query": "¿Cuál es su horario de atención?",
  "sessionId": "test-session-001"
}
```

**Esperas**: Días, horas, canales

---

## 🔍 SECCIÓN 2: Búsqueda de Productos (SQL)

### Test 2.1: Búsqueda por Marca Nike

**Variables**:
```json
{
  "query": "¿Tienes zapatillas Nike?",
  "sessionId": "test-session-002"
}
```

**Esperas**: Lista de productos Nike, precios, stock

---

### Test 2.2: Búsqueda por Marca Adidas

**Variables**:
```json
{
  "query": "Muéstrame productos Adidas",
  "sessionId": "test-session-002"
}
```

**Esperas**: Lista de productos Adidas


RESULTADO: {
  "data": {
    "semanticSearch": {
      "answer": "Claro. Tenemos el **Adidas Ultraboost Light** por **$180.00**. Quedan 5 unidades. ¿Te interesa?",
      "query": "Muéstrame productos Adidas",
      "error": null
    }
  }
}

---

### Test 2.3: Búsqueda por Uso

**Variables**:
```json
{
  "query": "Necesito zapatillas para correr en asfalto",
  "sessionId": "test-session-002"
}
```

**Esperas**: Productos running, características técnicas

---

### Test 2.4: Consulta de Stock Específico

**Variables**:
```json
{
  "query": "¿Hay stock de Nike Air Zoom Pegasus?",
  "sessionId": "test-session-002"
}
```

**Esperas**: Confirmación, cantidad disponible, precio

---

### Test 2.5: Listar Todos los Productos

**Variables**:
```json
{
  "query": "Muéstrame todos los productos disponibles",
  "sessionId": "test-session-002"
}
```

**Esperas**: Lista completa de productos

---

### Test 2.6: Rango de Precio

**Variables**:
```json
{
  "query": "¿Tienes zapatillas de menos de $100?",
  "sessionId": "test-session-002"
}
```

**Esperas**: Productos filtrados por precio

---

## 💬 SECCIÓN 3: Persuasión (SalesAgent + LLM)

### Test 3.1: Objeción de Precio

**Variables**:
```json
{
  "query": "Está muy caro",
  "sessionId": "test-session-003"
}
```

**Esperas**: Justificación de precio, comparación, crear urgencia

---

### Test 3.2: Duda de Calidad

**Variables**:
```json
{
  "query": "No sé si es de buena calidad",
  "sessionId": "test-session-003"
}
```

**Esperas**: Características técnicas, materiales premium, garantía

---

### Test 3.3: Comparación de Productos

**Variables**:
```json
{
  "query": "¿Cuál es la diferencia entre las Nike Air y las Adidas Ultraboost?",
  "sessionId": "test-session-003"
}
```

**Esperas**: Comparación técnica, recomendación personalizada

---

### Test 3.4: Solicitud de Descuento

**Variables**:
```json
{
  "query": "¿Puedes darme un descuento?",
  "sessionId": "test-session-003"
}
```

**Esperas**: Manejo cortés, alternativas, crear valor

---

### Test 3.5: Indecisión

**Variables**:
```json
{
  "query": "No estoy seguro si comprar",
  "sessionId": "test-session-003"
}
```

**Esperas**: Preguntas para entender necesidades, recomendación, urgencia

---

### Test 3.6: Cross-Selling

**Variables**:
```json
{
  "query": "Me gustan las Nike Air, ¿algo más que recomiendas?",
  "sessionId": "test-session-003"
}
```

**Esperas**: Productos complementarios, accesorios, combos

---

### Test 3.7: Upselling

**Variables**:
```json
{
  "query": "Busco unas zapatillas baratas",
  "sessionId": "test-session-003"
}
```

**Esperas**: Opciones económicas + destacar productos premium

---

## 🛒 SECCIÓN 4: Checkout (Transacciones BD)

### Test 4.1: Compra Completa - Paso 1

**Variables**:
```json
{
  "query": "Quiero comprar las Nike Air Zoom Pegasus",
  "sessionId": "test-session-004"
}
```

**Esperas**: "¿Confirmas que quieres comprar Nike Air Zoom Pegasus 40?"

---

### Test 4.1: Compra Completa - Paso 2

**Variables**:
```json
{
  "query": "Sí, confirmo",
  "sessionId": "test-session-004"
}
```

**Esperas**: "¿Cuál es tu dirección de envío?"

---

### Test 4.1: Compra Completa - Paso 3

**Variables**:
```json
{
  "query": "Av. Loja 123, Cuenca, Ecuador",
  "sessionId": "test-session-004"
}
```

**Esperas**: Resumen del pedido, "¿Confirmas tu pedido?"

---

### Test 4.1: Compra Completa - Paso 4

**Variables**:
```json
{
  "query": "Sí, proceder con el pago",
  "sessionId": "test-session-004"
}
```

**Esperas**: ✅ Pedido confirmado con número de pedido, total, dirección

**Verificar en BD después**:
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db -c "SELECT id, user_id, total_amount, status, shipping_address FROM orders ORDER BY created_at DESC LIMIT 1;"
```

---

### Test 4.2: Compra con Cantidad

**Variables**:
```json
{
  "query": "Quiero comprar 2 pares de Adidas Ultraboost",
  "sessionId": "test-session-005"
}
```

**Esperas**: Validación de stock (2 unidades), iniciar checkout

---

### Test 4.3: Sin Stock Suficiente

**Variables**:
```json
{
  "query": "Quiero comprar 100 pares de Nike",
  "sessionId": "test-session-006"
}
```

**Esperas**: Error amigable, "Solo tenemos X unidades disponibles"

---

### Test 4.4: Producto Inexistente

**Variables**:
```json
{
  "query": "Quiero comprar las Nike Fake Model 3000",
  "sessionId": "test-session-007"
}
```

**Esperas**: "No encontré ese producto", sugerencias

---

### Test 4.5: Cancelar Compra - Paso 1

**Variables**:
```json
{
  "query": "Quiero comprar Nike Air",
  "sessionId": "test-session-008"
}
```

---

### Test 4.5: Cancelar Compra - Paso 2

**Variables**:
```json
{
  "query": "Cancelar",
  "sessionId": "test-session-008"
}
```

**Esperas**: "Compra cancelada", transfer a Sales

---

## 🎭 SECCIÓN 5: Detección de Estilo

### Test 5.1: Usuario Casual

**Variables**:
```json
{
  "query": "Ey, ¿qué tal? ¿Tienes unas Nike chéveres?",
  "sessionId": "test-session-009"
}
```

**Esperas**: Tono amigable, lenguaje casual, emojis

---

### Test 5.2: Usuario Formal

**Variables**:
```json
{
  "query": "Buenos días. Quisiera información sobre calzado deportivo de alta gama.",
  "sessionId": "test-session-010"
}
```

**Esperas**: Tono profesional, lenguaje formal, sin emojis

---

### Test 5.3: Usuario Neutral

**Variables**:
```json
{
  "query": "Hola, busco zapatillas para correr",
  "sessionId": "test-session-011"
}
```

**Esperas**: Tono balanceado, profesional pero amigable

---

## 🧩 SECCIÓN 6: Transferencias Entre Agentes

### Test 6.1: Retriever → Sales (Paso 1)

**Variables**:
```json
{
  "query": "¿Tienes zapatillas Nike?",
  "sessionId": "test-session-012"
}
```

**Esperas**: Información objetiva (Retriever)

---

### Test 6.1: Retriever → Sales (Paso 2)

**Variables**:
```json
{
  "query": "Están muy caras",
  "sessionId": "test-session-012"
}
```

**Esperas**: Persuasión (SalesAgent) - Transfer detectado

---

### Test 6.2: Sales → Checkout (Paso 1)

**Variables**:
```json
{
  "query": "Busco zapatillas",
  "sessionId": "test-session-013"
}
```

**Esperas**: Recomendaciones (Sales)

---

### Test 6.2: Sales → Checkout (Paso 2)

**Variables**:
```json
{
  "query": "Me gustan las Nike, quiero comprarlas",
  "sessionId": "test-session-013"
}
```

**Esperas**: Iniciar checkout (CheckoutAgent)

---

### Test 6.3: Checkout → Sales (Paso 1)

**Variables**:
```json
{
  "query": "Comprar Nike Air",
  "sessionId": "test-session-014"
}
```

**Esperas**: Checkout inicia

---

### Test 6.3: Checkout → Sales (Paso 2)

**Variables**:
```json
{
  "query": "Mejor no, quiero ver otras opciones",
  "sessionId": "test-session-014"
}
```

**Esperas**: Sales retoma con nuevas opciones

---

## ⚠️ SECCIÓN 7: Casos Edge

### Test 7.1: Query Vacío

**Variables**:
```json
{
  "query": "   ",
  "sessionId": "test-session-015"
}
```

**Esperas**: Mensaje amigable, no crash

---

### Test 7.2: Producto No Existente

**Variables**:
```json
{
  "query": "Busco zapatillas marca XYZ123 inexistente",
  "sessionId": "test-session-016"
}
```

**Esperas**: "No encontré productos", sugerencias

---

### Test 7.3: Múltiples Intenciones

**Variables**:
```json
{
  "query": "Quiero comprar Nike Air pero también quiero saber la política de devoluciones y cuánto cuesta el envío",
  "sessionId": "test-session-017"
}
```

**Esperas**: Manejo secuencial o priorización

---

### Test 7.4: Lenguaje Ofensivo

**Variables**:
```json
{
  "query": "Este chat no sirve",
  "sessionId": "test-session-018"
}
```

**Esperas**: Respuesta cortés, ofrecer ayuda

---

### Test 7.5: Otro Idioma

**Variables**:
```json
{
  "query": "Do you have Nike shoes?",
  "sessionId": "test-session-019"
}
```

**Esperas**: Respuesta en inglés o solicitar español

---

## 🎯 FLUJO COMPLETO E2E (Happy Path)

### Paso 1: Saludo

**Variables**:
```json
{
  "query": "Hola",
  "sessionId": "test-session-e2e"
}
```

---

### Paso 2: Búsqueda

**Variables**:
```json
{
  "query": "Busco zapatillas para correr",
  "sessionId": "test-session-e2e"
}
```

---

### Paso 3: Solicitar Recomendación

**Variables**:
```json
{
  "query": "¿Cuál me recomiendas?",
  "sessionId": "test-session-e2e"
}
```

---

### Paso 4: Objeción

**Variables**:
```json
{
  "query": "Las Nike parecen buenas pero están caras",
  "sessionId": "test-session-e2e"
}
```

---

### Paso 5: Decisión de Compra

**Variables**:
```json
{
  "query": "Ok, me convenciste. Quiero comprarlas",
  "sessionId": "test-session-e2e"
}
```

---

### Paso 6: Confirmación

**Variables**:
```json
{
  "query": "Sí, confirmo",
  "sessionId": "test-session-e2e"
}
```

---

### Paso 7: Dirección

**Variables**:
```json
{
  "query": "Av. Loja 123, Cuenca",
  "sessionId": "test-session-e2e"
}
```

---

### Paso 8: Proceder con Pago

**Variables**:
```json
{
  "query": "Sí, proceder",
  "sessionId": "test-session-e2e"
}
```

---

### Paso 9: Despedida

**Variables**:
```json
{
  "query": "Gracias",
  "sessionId": "test-session-e2e"
}
```

---

## 🔧 QUERIES ADICIONALES PARA TESTING

### Query para Listar Productos (sin IA)

```graphql
query ListProducts {
  listProducts(limit: 10) {
    id
    productName
    unitCost
    quantityAvailable
  }
}
```

**Variables**: No necesita

**Uso**: Ver todos los productos en la BD

---

## 📊 INTERPRETACIÓN DE RESPUESTAS

### Respuesta Exitosa

```json
{
  "data": {
    "semanticSearch": {
      "answer": "Sí, tenemos las siguientes zapatillas Nike: Nike Air Zoom Pegasus 40 ($120.00, 15 unidades disponibles)...",
      "query": "¿Tienes zapatillas Nike?",
      "error": null
    }
  }
}
```

**Campos**:
- `answer`: La respuesta generada por Alex (puede venir de Retriever, Sales o Checkout)
- `query`: Tu pregunta original (eco)
- `error`: Si algo falla, el mensaje de error aparece aquí

---

### Respuesta con Error

```json
{
  "data": {
    "semanticSearch": {
      "answer": null,
      "query": "¿Tienes zapatillas Nike?",
      "error": "Error al procesar consulta: Timeout"
    }
  }
}
```

---

## ✅ CHECKLIST DE PRUEBAS

**RAG/FAQs (5 pruebas):**
- [ ] Política de devoluciones
- [ ] Métodos de pago
- [ ] Tiempos de envío
- [ ] Garantía
- [ ] Horarios

**Productos SQL (6 pruebas):**
- [ ] Búsqueda Nike
- [ ] Búsqueda Adidas
- [ ] Búsqueda por uso
- [ ] Consulta de stock
- [ ] Listar todos
- [ ] Rango de precio

**Persuasión LLM (7 pruebas):**
- [ ] Objeción de precio
- [ ] Duda de calidad
- [ ] Comparación
- [ ] Solicitud de descuento
- [ ] Indecisión
- [ ] Cross-selling
- [ ] Upselling

**Checkout BD (5 pruebas):**
- [ ] Compra completa exitosa (4 pasos)
- [ ] Compra con cantidad
- [ ] Sin stock suficiente
- [ ] Producto inexistente
- [ ] Cancelar compra

**Estilo (3 pruebas):**
- [ ] Usuario casual
- [ ] Usuario formal
- [ ] Usuario neutral

**Transferencias (3 pruebas):**
- [ ] Retriever → Sales
- [ ] Sales → Checkout
- [ ] Checkout → Sales

**Casos Edge (5 pruebas):**
- [ ] Query vacío
- [ ] Producto inexistente
- [ ] Múltiples intenciones
- [ ] Lenguaje ofensivo
- [ ] Otro idioma

**E2E (1 flujo completo):**
- [ ] Flujo happy path (9 pasos)

---

## 📝 TIPS PARA TESTING EN GRAPHQL PLAYGROUND

1. **Mantén sessionId consistente** para pruebas que requieren contexto (ej: checkout completo)
2. **Cambia sessionId** entre diferentes categorías de pruebas para limpiar contexto
3. **Panel derecho** muestra la respuesta en JSON
4. **Panel inferior derecho** muestra logs/errores si hay problemas
5. **Botón "Prettify"** formatea tu JSON automáticamente
6. **Historial** (icono reloj) guarda tus queries anteriores

---

## 🚀 INICIO RÁPIDO

1. **Abre**: http://localhost:8000/graphql
2. **Copia en panel izquierdo**:
   ```graphql
   query Chat($query: String!, $sessionId: String) {
     semanticSearch(query: $query, sessionId: $sessionId) {
       answer
       query
       error
     }
   }
   ```
3. **Copia en "Query Variables"** (panel inferior izquierdo):
   ```json
   {
     "query": "¿Tienes zapatillas Nike?",
     "sessionId": "test-001"
   }
   ```
4. **Presiona ▶ Play**
5. **Ve resultado** en panel derecho

---

**¡Listo para probar en GraphQL Playground!** 🎉
