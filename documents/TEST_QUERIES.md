# Test Queries - Sistema Multi-Agente Mejorado

**Versión:** 2.1 (Detección Inteligente + Error Handling)
**Fecha:** Enero 2026

---

## 📋 Índice de Pruebas

1. [Detección Inteligente (LLM Zero-shot)](#1-detección-inteligente-llm-zero-shot)
2. [Detección de Estilos](#2-detección-de-estilos)
3. [Flujos Completos de Conversación](#3-flujos-completos-de-conversación)
4. [Manejo de Errores](#4-manejo-de-errores)
5. [Transferencias entre Agentes](#5-transferencias-entre-agentes)
6. [Casos Edge](#6-casos-edge)

---

## 1. Detección Inteligente (LLM Zero-shot)

### ✅ Test 1.1: Negación (Mejorado con LLM)

**Antes (Keywords):** Detectaba "busco" → search ❌
**Ahora (LLM):** Entiende que NO busca Nike, busca Adidas ✅

```graphql
query {
  semanticSearch(query: "No busco Nike, quiero Adidas") {
    answer
    query
  }
}
```

**Esperado:**

- Intent: `search`
- Agente: `retriever`
- Reasoning: "Usuario rechaza Nike, busca Adidas"

---

### ✅ Test 1.2: Sinónimos (Mejorado con LLM)

**Antes (Keywords):** No detectaba "ando buscando" ❌
**Ahora (LLM):** Detecta sinónimos automáticamente ✅

```graphql
query {
  semanticSearch(query: "Ando buscando zapatos para correr") {
    answer
    query
  }
}
```

**Esperado:**

- Intent: `search`
- Reasoning: "'Ando buscando' es sinónimo de 'busco'"

---

### ✅ Test 1.3: Formalidad Sutil (Mejorado con LLM)

**Antes (Keywords):** style=neutral (sin "usted") ❌
**Ahora (LLM):** Detecta tono formal sin palabras clave ✅

```graphql
query {
  semanticSearch(query: "Buenos días, quisiera consultar por zapatillas deportivas") {
    answer
    query
  }
}
```

**Esperado:**

- Style: `formal`
- Intent: `search`
- Reasoning: "Uso de 'quisiera' indica cortesía"

---

### ✅ Test 1.4: Contexto Complejo (Mejorado con LLM)

```graphql
query {
  semanticSearch(
    query: "Me gustaría saber si tienen disponibilidad en talla 42"
    sessionId: "test-context-complex"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- Intent: `search`
- Reasoning: "Consulta sobre disponibilidad = búsqueda"

---

### ✅ Test 1.5: Objeción sin Keywords

```graphql
query {
  semanticSearch(
    query: "Uff, eso es mucho dinero"
    sessionId: "test-objecion"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- Intent: `persuasion`
- Agente: `sales`
- Reasoning: "Expresión de preocupación por precio"

---

## 2. Detección de Estilos

### 🇪🇨 Test 2.1: Estilo Cuencano

```graphql
query {
  semanticSearch(query: "Ayayay que lindo ve, busco unos Nike full buenos") {
    answer
    query
  }
}
```

**Esperado:**

- Style: `cuencano`
- Patrones: "ayayay", "ve", "full"
- Respuesta adaptada con modismos ecuatorianos

---

### 🎮 Test 2.2: Estilo Juvenil

```graphql
query {
  semanticSearch(query: "Che bro, mostrame algo copado tipo para correr") {
    answer
    query
  }
}
```

**Esperado:**

- Style: `juvenil`
- Patrones: "che", "bro", "tipo", "copado"
- Respuesta casual y energética

---

### 👔 Test 2.3: Estilo Formal (Sin Keywords Explícitos)

```graphql
query {
  semanticSearch(query: "Estimado, quisiera consultar disponibilidad de calzado deportivo") {
    answer
    query
  }
}
```

**Esperado:**

- Style: `formal` (detectado por tono, no keywords)
- Reasoning: "Uso de 'estimado' y 'quisiera' indica formalidad"

---

### 😊 Test 2.4: Estilo Neutral

```graphql
query {
  semanticSearch(query: "Hola, busco zapatillas Nike para running") {
    answer
    query
  }
}
```

**Esperado:**

- Style: `neutral`
- Respuesta estándar, profesional pero amigable

---

## 3. Flujos Completos de Conversación

### 🛒 Test 3.1: Flujo Completo - Búsqueda → Objeción → Compra (Cuencano)

#### Step 1: Búsqueda inicial

```graphql
query {
  semanticSearch(
    query: "Ayayay, busco unas Nike ve"
    sessionId: "flow-cuencano-1"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- RetrieverAgent → busca productos
- Transfiere a SalesAgent
- Estilo: cuencano detectado

---

#### Step 2: Objeción de precio

```graphql
query {
  semanticSearch(
    query: "Están caros ve"
    sessionId: "flow-cuencano-1"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- SalesAgent persuade con estilo cuencano
- Justifica precio
- Crea urgencia

---

#### Step 3: Decisión de compra

```graphql
query {
  semanticSearch(
    query: "Bueno dámelos"
    sessionId: "flow-cuencano-1"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- SalesAgent detecta intención de compra
- Transfiere a CheckoutAgent
- Solicita confirmación

---

#### Step 4: Confirmar

```graphql
query {
  semanticSearch(
    query: "Sí, confirmo"
    sessionId: "flow-cuencano-1"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- CheckoutAgent solicita dirección
- Mensaje en estilo cuencano

---

#### Step 5: Dirección

```graphql
query {
  semanticSearch(
    query: "Av. Solano 123, Cuenca, Ecuador"
    sessionId: "flow-cuencano-1"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- CheckoutAgent procesa pedido
- Confirma con resumen
- Estilo cuencano: "Ayayay, listo ve!"

---

### 🎯 Test 3.2: Flujo Completo - Formal (Sin Checkout)

#### Step 1: Saludo formal

```graphql
query {
  semanticSearch(
    query: "Buenos días, quisiera información sobre zapatillas para running"
    sessionId: "flow-formal-1"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- Style: formal detectado
- Intent: search
- RetrieverAgent busca

---

#### Step 2: Pregunta técnica

```graphql
query {
  semanticSearch(
    query: "Podría indicarme cuál ofrece mejor amortiguación?"
    sessionId: "flow-formal-1"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- SalesAgent responde formalmente
- Proporciona información técnica

---

#### Step 3: Consulta de garantía

```graphql
query {
  semanticSearch(
    query: "Qué garantía incluyen?"
    sessionId: "flow-formal-1"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- SalesAgent usa RAG para info de garantías
- Responde con trato de usted

---

### 🏃 Test 3.3: Flujo Juvenil - Rápido

#### Step 1: Búsqueda casual

```graphql
query {
  semanticSearch(
    query: "Che, que tenés en Adidas?"
    sessionId: "flow-juvenil-1"
  ) {
    answer
    query
  }
}
```

---

#### Step 2: Recomendación

```graphql
query {
  semanticSearch(
    query: "Cual está más copado bro?"
    sessionId: "flow-juvenil-1"
  ) {
    answer
    query
  }
}
```

---

#### Step 3: Compra directa

```graphql
query {
  semanticSearch(
    query: "Dale, los quiero"
    sessionId: "flow-juvenil-1"
  ) {
    answer
    query
  }
}
```

---

#### Step 4: Confirmación rápida

```graphql
query {
  semanticSearch(
    query: "Ok"
    sessionId: "flow-juvenil-1"
  ) {
    answer
    query
  }
}
```

---

#### Step 5: Dirección Flujos

```graphql
query {
  semanticSearch(
    query: "Calle Larga 456, depto 2B, Cuenca"
    sessionId: "flow-juvenil-1"
  ) {
    answer
    query
  }
}
```

---

## 4. Manejo de Errores

### ⚠️ Test 4.1: Query sin Términos de Búsqueda

```graphql
query {
  semanticSearch(query: "Hola") {
    answer
    query
  }
}
```

**Esperado:**

- Mensaje amigable pidiendo especificar
- No crashea
- Transfiere a SalesAgent

---

### ⚠️ Test 4.2: Dirección Muy Corta

#### Setup (búsqueda + compra)

```graphql
query {
  semanticSearch(
    query: "Quiero Nike Air Max"
    sessionId: "test-direccion-corta"
  ) {
    answer
    query
  }
}
```

```graphql
query {
  semanticSearch(
    query: "Los quiero"
    sessionId: "test-direccion-corta"
  ) {
    answer
    query
  }
}
```

```graphql
query {
  semanticSearch(
    query: "Sí"
    sessionId: "test-direccion-corta"
  ) {
    answer
    query
  }
}
```

#### Dirección inválida

```graphql
query {
  semanticSearch(
    query: "Calle 123"
    sessionId: "test-direccion-corta"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- CheckoutAgent rechaza dirección corta
- Pide dirección completa
- No procesa pedido

---

### ⚠️ Test 4.3: Cancelación Mid-Checkout

#### Setup

```graphql
query {
  semanticSearch(
    query: "Dame los Nike"
    sessionId: "test-cancelacion"
  ) {
    answer
    query
  }
}
```

#### Cancelar

```graphql
query {
  semanticSearch(
    query: "No, mejor no"
    sessionId: "test-cancelacion"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- CheckoutAgent cancela pedido
- Limpia estado
- Transfiere a SalesAgent
- Mensaje: "No hay problema, ¿buscamos otra cosa?"

---

## 5. Transferencias entre Agentes

### 🔄 Test 5.1: Retriever → Sales → Checkout

```graphql
query {
  semanticSearch(
    query: "Busco Nike"
    sessionId: "test-transfers-1"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- RetrieverAgent busca
- Si ≤5 resultados → transfiere a Sales

---

```graphql
query {
  semanticSearch(
    query: "El primero está bien, lo quiero"
    sessionId: "test-transfers-1"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- SalesAgent detecta intención
- Transfiere a CheckoutAgent

---

### 🔄 Test 5.2: Sales → Retriever (Búsqueda Refinada)

```graphql
query {
  semanticSearch(
    query: "Tienes algo más barato?"
    sessionId: "test-refine"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- SalesAgent puede sugerir nueva búsqueda
- O trabajar con resultados existentes

---

## 6. Casos Edge

### 🔍 Test 6.1: Sin Resultados

```graphql
query {
  semanticSearch(query: "Busco zapatillas Reebok") {
    answer
    query
  }
}
```

**Esperado:**

- RetrieverAgent: 0 resultados
- Mensaje: "No encontré productos para 'Reebok'"
- Transfiere a SalesAgent para alternativas

---

### 🔍 Test 6.2: Query Ambiguo

```graphql
query {
  semanticSearch(query: "???") {
    answer
    query
  }
}
```

**Esperado:**

- SalesAgent maneja query inválido
- Mensaje amigable pidiendo aclaración

---

### 🔍 Test 6.3: Cambio de Intención

```graphql
query {
  semanticSearch(
    query: "Busco Nike"
    sessionId: "test-cambio"
  ) {
    answer
    query
  }
}
```

```graphql
query {
  semanticSearch(
    query: "No, mejor cancela eso, dame Adidas"
    sessionId: "test-cambio"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- LLM detecta cambio de intención
- Nueva búsqueda de Adidas
- Cancela contexto anterior

---

### 🔍 Test 6.4: Múltiples Productos (Future)

```graphql
query {
  semanticSearch(
    query: "Quiero 2 Nike Air Max y 1 Adidas Ultraboost"
    sessionId: "test-multiple"
  ) {
    answer
    query
  }
}
```

**Esperado:**

- CheckoutAgent puede manejar o pedir uno por uno
- Procesamiento individual con error handling

---

## 7. Tests de Información (RAG)

### 📚 Test 7.1: Horarios

```graphql
query {
  semanticSearch(query: "Qué horarios tienen?") {
    answer
    query
  }
}
```

**Esperado:**

- SalesAgent usa RAG
- Responde con horarios de chunks.csv

---

### 📚 Test 7.2: Envíos

```graphql
query {
  semanticSearch(query: "Hacen envíos a domicilio?") {
    answer
    query
  }
}
```

**Esperado:**

- SalesAgent usa RAG
- Info de delivery_online

---

### 📚 Test 7.3: Garantías

```graphql
query {
  semanticSearch(query: "Cuál es la política de garantía?") {
    answer
    query
  }
}
```

**Esperado:**

- SalesAgent usa RAG
- Info de warranties_support

---

### 📚 Test 7.4: Promociones

```graphql
query {
  semanticSearch(query: "Tienen descuentos o promociones?") {
    answer
    query
  }
}
```

**Esperado:**

- SalesAgent usa RAG
- Info de promotions_financing

---

## 8. Tests de Resiliencia

### 💪 Test 8.1: Sesión Larga

```graphql
# Query 1
query { semanticSearch(query: "Hola", sessionId: "long-session") { answer } }

# Query 2
query { semanticSearch(query: "Busco Nike", sessionId: "long-session") { answer } }

# Query 3
query { semanticSearch(query: "Están caros", sessionId: "long-session") { answer } }

# Query 4
query { semanticSearch(query: "Hay descuentos?", sessionId: "long-session") { answer } }

# Query 5
query { semanticSearch(query: "Ok, los quiero", sessionId: "long-session") { answer } }

# Query 6
query { semanticSearch(query: "Sí", sessionId: "long-session") { answer } }

# Query 7
query { semanticSearch(query: "Av. Solano 123", sessionId: "long-session") { answer } }
```

**Esperado:**

- Mantiene contexto durante toda la conversación
- Estilo detectado se mantiene
- Transferencias funcionan correctamente

---

### 💪 Test 8.2: Conversación con Interrupciones

```graphql
query {
  semanticSearch(
    query: "Busco Nike"
    sessionId: "test-interruption"
  ) {
    answer
  }
}
```

```graphql
query {
  semanticSearch(
    query: "Espera, mejor Adidas"
    sessionId: "test-interruption"
  ) {
    answer
  }
}
```

```graphql
query {
  semanticSearch(
    query: "No, volvamos a Nike"
    sessionId: "test-interruption"
  ) {
    answer
  }
}
```

**Esperado:**

- LLM entiende cambios de dirección
- Maneja interrupciones graciosamente

---

## 9. Tests Comparativos (LLM vs Keywords)

### ⚖️ Test 9.1: Frases Complejas

#### Con LLM

```graphql
query {
  semanticSearch(query: "Me gustaría ver si tienen algo de Nike en mi presupuesto") {
    answer
    query
  }
}
```

**Esperado (LLM):**

- Intent: `search` + `persuasion`
- Entiende: búsqueda + preocupación por precio

---

### ⚖️ Test 9.2: Doble Negación

```graphql
query {
  semanticSearch(query: "No es que no quiera Nike, pero prefiero Adidas") {
    answer
    query
  }
}
```

**Esperado (LLM):**

- Intent: `search`
- Entiende: Preferencia por Adidas

---

### ⚖️ Test 9.3: Tono Sarcástico

```graphql
query {
  semanticSearch(query: "Wow, qué baratos...") {
    answer
    query
  }
}
```

**Esperado (LLM):**

- Intent: `persuasion`
- Detecta sarcasmo = objeción de precio

---

## 10. Validación de Metadata (Debug)

### 🔍 Test 10.1: Ver Metadata Completa

Para debugging, revisar los logs del servidor después de:

```graphql
query {
  semanticSearch(
    query: "Ayayay busco Nike ve"
    sessionId: "test-metadata"
  ) {
    answer
    query
  }
}
```

**Revisar en logs:**

```bash
grep "test-metadata" logs/app.log
```

**Esperado en logs:**

```bash
INFO: Estilo detectado: cuencano (confianza: 0.92)
INFO: LLM clasificó como 'search' (confianza: 0.95): Usuario busca productos Nike
INFO: Intención detectada: search -> Agente: retriever (confianza: 0.95)
INFO: RetrieverAgent procesando: Ayayay busco Nike ve
INFO: Productos encontrados: 5
INFO: Transferencia #1: retriever -> sales
INFO: Query procesado por agente final: sales
```

---

## 📊 Matriz de Tests Recomendados

| Test | Objetivo | Prioridad |
| ------ | ---------- | ----------- |
| 1.1-1.5 | Detección LLM | 🔥 Alta |
| 2.1-2.4 | Estilos | 🔥 Alta |
| 3.1-3.3 | Flujos completos | 🔥 Alta |
| 4.1-4.3 | Error handling | 🔥 Alta |
| 5.1-5.2 | Transferencias | 🟡 Media |
| 6.1-6.4 | Casos edge | 🟡 Media |
| 7.1-7.4 | RAG | 🟢 Baja |
| 8.1-8.2 | Resiliencia | 🟢 Baja |

---

## 🎯 Quick Start - Tests Mínimos

Si tienes poco tiempo, ejecuta estos 5 tests esenciales:

### 1. Detección Inteligente

```graphql
query { semanticSearch(query: "No busco Nike, quiero Adidas") { answer query } }
```

### 2. Estilo Cuencano

```graphql
query { semanticSearch(query: "Ayayay busco Nike ve") { answer query } }
```

### 3. Flujo Completo

```graphql
query { semanticSearch(query: "Busco Nike", sessionId: "quick-1") { answer } }
query { semanticSearch(query: "Los quiero", sessionId: "quick-1") { answer } }
query { semanticSearch(query: "Sí", sessionId: "quick-1") { answer } }
query { semanticSearch(query: "Av. Solano 123", sessionId: "quick-1") { answer } }
```

### 4. Error Handling

```graphql
query { semanticSearch(query: "???") { answer } }
```

### 5. Información

```graphql
query { semanticSearch(query: "Qué horarios tienen?") { answer } }
```

---

## 🔧 Tips de Testing

### Ejecutar en GraphQL Playground

1. Abre: `http://localhost:8000/graphql`
2. Copia una query del archivo
3. Pega en el panel izquierdo
4. Click en ▶️ (Play)
5. Revisa respuesta en panel derecho

### Ver Logs en Tiempo Real

```bash
tail -f logs/app.log | grep -E "(Estilo|Intención|LLM|Agent)"
```

### Limpiar Sesión

```graphql
# Usar nuevo sessionId para empezar fresh
query {
  semanticSearch(
    query: "..."
    sessionId: "nuevo-id-unico"
  ) {
    answer
  }
}
```

---

## 📝 Checklist de Testing

```bash
Funcionalidad Core:
[ ] Detección de intención con LLM
[ ] Detección de estilo con LLM
[ ] Fallback a keywords si LLM falla
[ ] Búsqueda de productos
[ ] Persuasión con SalesAgent
[ ] Checkout completo
[ ] RAG para información

Error Handling:
[ ] LLM timeout (simular apagando Vertex AI)
[ ] BD caída (simular apagando PostgreSQL)
[ ] Query inválido
[ ] Dirección inválida
[ ] Stock insuficiente
[ ] Cancelación mid-checkout

Estilos:
[ ] Cuencano detectado correctamente
[ ] Juvenil detectado correctamente
[ ] Formal detectado correctamente
[ ] Neutral por defecto

Transferencias:
[ ] Retriever → Sales
[ ] Sales → Checkout
[ ] Checkout → Sales (cancelación)

Sesiones:
[ ] Contexto mantenido entre queries
[ ] Estilo persiste en sesión
[ ] Productos recordados en sesión
```

---

**Versión:** 2.1
**Última actualización:** Enero 2026
**Estado:** ✅ Listo para testing completo
