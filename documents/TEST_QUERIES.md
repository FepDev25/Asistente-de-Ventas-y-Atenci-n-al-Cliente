# Queries de Prueba - Sistema Multi-Agente

Este archivo contiene queries de ejemplo para probar todas las funcionalidades del sistema multi-agente.

---

## 1. RetrieverAgent (Agente Buscador)

Queries que activan búsqueda SQL directa:

### Búsquedas Básicas

```txt
"Busco zapatillas Nike"
"Mostrame modelos Adidas"
"Quiero ver zapatos para running"
"Tienes Puma?"
"Hay algo para basketball?"
```

### Búsquedas Específicas

```txt
"Necesito talla 42"
"Modelos en color negro"
"Que tienes en el catalogo?"
"Cuales son los modelos disponibles?"
"Zapatos para correr marca Nike"
```

### Búsquedas que NO encuentran resultados

```txt
"Busco Reebok" (si no tienes en BD)
"Tienes sandalias?" (si solo vendes zapatillas)
"Modelos de la marca XYZ"
```

**Comportamiento Esperado:**

- Extrae términos clave (Nike, Adidas, running, etc.)
- Busca en BD usando SQL
- Formatea resultados con precio y stock
- Transfiere a SalesAgent si hay ≤5 resultados
- Mensaje adaptado al estilo del usuario

---

## 2. SalesAgent (Agente Vendedor "Alex")

Queries que activan persuasión con LLM:

### Objeciones de Precio

```txt
"Están muy caros"
"No tengo tanta plata"
"Hay algo más barato?"
"Ese precio es muy alto"
"Vale la pena gastar tanto?"
```

### Solicitud de Recomendaciones

```txt
"Cual me recomiendas?"
"No se cual elegir"
"Que diferencia hay entre estos dos?"
"Cual es mejor para correr?"
"Necesito ayuda para decidir"
```

### Dudas Generales

```txt
"Por qué debería comprar este?"
"Son de buena calidad?"
"Cuanto tiempo duran?"
"Vienen con garantía?"
"Son originales?"
```

### Preguntas de Información (usa RAG)

```txt
"Que horarios tienen?"
"Donde están ubicados?"
"Hacen envíos?"
"Como es el proceso de devolución?"
"Aceptan tarjetas?"
"Tienen promociones?"
```

**Comportamiento Esperado:**

- Responde con personalidad de vendedor
- Justifica precios con calidad/durabilidad
- Sugiere cross-selling (calcetines, limpiadores)
- Crea urgencia ("solo quedan X")
- Adapta tono según estilo detectado
- Usa RAG para info de políticas/horarios

---

## 3. CheckoutAgent (Agente Cajero)

Queries que activan proceso de compra:

### Confirmación de Compra

```txt
"Los quiero"
"Dámelos"
"Quiero comprar"
"Envíamelos"
"Procede con el pedido"
"Me los llevo"
```

### Confirmaciones durante Checkout

```txt
"Sí" (después de ver producto)
"Ok" (confirmar pedido)
"Dale" (aceptar)
"Confirmo" (finalizar)
```

### Cancelaciones

```txt
"No, mejor no"
"Espera, cancela"
"Mejor no lo compro"
```

### Dirección de Envío

```txt
"Av. Solano 123, Cuenca"
"Calle Larga y Borrero, edificio azul, piso 3"
"Urbanización El Bosque, casa 45, Cuenca"
```

**Comportamiento Esperado:**

- Inicia flujo: confirm → address → payment
- Valida stock en tiempo real
- Solicita confirmación antes de procesar
- Pide dirección de envío
- Procesa orden en BD
- NO usa LLM (solo lógica)

---

## 4. Detección de Estilos de Usuario

El sistema detecta automáticamente 4 estilos:

### Estilo CUENCANO 🇪🇨

```txt
"Ayayay, que lindos ve"
"Busco unos zapatos full buenos"
"Están chevere estos"
"Cuanto cuestan ve?"
"Dame los Nike pana"
```

**Patrones detectados:** ayayay, ve, full, chevere, lindo, pana

**Respuestas esperadas:**

- "Ayayay, mirá lo que tengo para vos:"
- "Están full lindos ve"
- "Te quedan solo 2 ve!"

---

### Estilo JUVENIL 🎮

```txt
"Che, mostrame algo copado"
"Bro, que tenés en Nike?"
"Re buenos estos"
"Están tipo caros mal"
"Dale, los quiero"
```

**Patrones detectados:** che, bro, tipo, re, mal, onda, copado

**Respuestas esperadas:**

- "¡Che, mira lo que encontré!"
- "Están re copados estos"
- "Dale, sin drama"

---

### Estilo FORMAL 👔

```txt
"Buenos días, quisiera consultar por zapatillas"
"Disculpe, tienen modelos Nike?"
"Por favor, podría mostrarme el catálogo?"
"Agradezco su ayuda"
"Quisiera proceder con la compra"
```

**Patrones detectados:** usted, señor, señora, por favor, disculpe, agradezco

**Respuestas esperadas:**

- "He encontrado los siguientes productos:"
- "¿Desea proceder con el pedido?"
- "Excelente elección"

---

### Estilo NEUTRAL (default) 😊

```txt
"Hola, busco zapatillas Nike"
"Cuanto cuestan?"
"Me interesa este modelo"
"Quiero comprar"
```

**Respuestas esperadas:**

- "Encontré estos productos:"
- "¿Está correcto?"
- "Perfecto, confirmemos el pedido"

---

## 5. Flujos Completos de Conversación

### Flujo 1: Búsqueda → Objeción → Compra (Estilo Cuencano)

```txt
Query 1: "Ayayay, busco unas Nike ve"
→ RetrieverAgent busca productos
→ Transfiere a SalesAgent

Query 2: "Están caros ve"
→ SalesAgent (estilo cuencano detectado) persuade

Query 3: "Bueno dámelos"
→ SalesAgent detecta intención de compra
→ Transfiere a CheckoutAgent

Query 4: "Sí" (confirmar)
→ CheckoutAgent solicita dirección

Query 5: "Av. Solano 123, Cuenca"
→ CheckoutAgent procesa pedido y confirma
```

---

### Flujo 2: Búsqueda → Recomendación → Compra (Estilo Juvenil)

```txt
Query 1: "Che, qué tenés para running?"
→ RetrieverAgent busca

Query 2: "Cual me recomiendas bro?"
→ SalesAgent (estilo juvenil) recomienda

Query 3: "Re copado, los quiero"
→ Transfiere a CheckoutAgent

Query 4: "Dale, confirmo"
→ CheckoutAgent solicita dirección

Query 5: "Calle Larga 456, depto 2B"
→ CheckoutAgent finaliza compra
```

---

### Flujo 3: Info → Búsqueda → Compra (Estilo Formal)

```txt
Query 1: "Disculpe, qué horarios tienen?"
→ SalesAgent usa RAG para responder

Query 2: "Quisiera ver modelos Adidas, por favor"
→ Transfiere a RetrieverAgent → busca → vuelve a SalesAgent

Query 3: "Me interesa este modelo de $150"
→ SalesAgent responde sobre el producto

Query 4: "Deseo proceder con la compra"
→ Transfiere a CheckoutAgent

Query 5: "Confirmo" → "Urbanización El Bosque, casa 45"
→ CheckoutAgent procesa
```

---

### Flujo 4: Sin Resultados → Alternativas

```txt
Query 1: "Busco zapatillas Reebok"
→ RetrieverAgent no encuentra resultados

Query 2: "Que otras marcas tienes?"
→ SalesAgent (con RetrieverAgent) muestra alternativas

Query 3: "Ok, dame las Nike entonces"
→ Transfiere a CheckoutAgent
```

---

## 6. Casos Edge (Pruebas de Robustez)

### Queries Ambiguos

```txt
"Hola" → SalesAgent responde cordialmente
"Gracias" → SalesAgent agradece
"???" → SalesAgent pide aclaración
```

### Cambio de Intención

```txt
Query 1: "Busco Nike"
Query 2: "No, mejor cancela, dame Adidas"
→ Sistema debe cambiar de búsqueda
```

### Multiple Productos

```txt
"Quiero 2 Nike Air Max y 1 Adidas Ultraboost"
→ CheckoutAgent debe manejar múltiples items (si está implementado)
```

### Stock Insuficiente

```txt
Query 1: RetrieverAgent muestra "Solo quedan 2"
Query 2: "Quiero 5"
→ CheckoutAgent debe avisar stock insuficiente
```

---

## 7. Verificación de Metadata

Después de cada query, revisar la respuesta `metadata`:

```json
{
  "agent_used": "sales",           // ¿Qué agente respondió?
  "user_style": "cuencano",        // ¿Se detectó el estilo?
  "intent": "persuasion",          // ¿Se clasificó bien?
  "products_found": 3,             // ¿Cuántos productos?
  "in_checkout": false             // ¿Está en proceso de compra?
}
```

---

## 8. Comandos GraphQL

### Query Básico

```graphql
query {
  semanticSearch(query: "Busco Nike para correr") {
    answer
    query
  }
}
```

### Con Session ID (para mantener contexto)

```graphql
query {
  semanticSearch(
    query: "Los quiero",
    sessionId: "user123"
  ) {
    answer
    query
  }
}
```

---

## Checklist de Pruebas

### RetrieverAgent

- [ ] Búsqueda simple con 1 palabra clave
- [ ] Búsqueda con múltiples palabras
- [ ] Búsqueda sin resultados
- [ ] Transferencia a SalesAgent con pocos resultados
- [ ] Adaptación de mensaje según estilo

### SalesAgent

- [ ] Manejo de objeción de precio
- [ ] Recomendaciones personalizadas
- [ ] Cross-selling
- [ ] Consulta RAG (horarios/políticas)
- [ ] Detección de intención de compra
- [ ] Transferencia a CheckoutAgent
- [ ] Respuestas en 4 estilos diferentes

### CheckoutAgent

- [ ] Inicio de checkout
- [ ] Confirmación de producto
- [ ] Validación de stock
- [ ] Solicitud de dirección
- [ ] Procesamiento exitoso
- [ ] Cancelación mid-checkout
- [ ] Manejo de stock insuficiente

### Orchestrator

- [ ] Detección correcta de intenciones
- [ ] Detección de estilo cuencano
- [ ] Detección de estilo juvenil
- [ ] Detección de estilo formal
- [ ] Estilo neutral por defecto
- [ ] Transferencias entre agentes
- [ ] Prevención de loops infinitos

### Integración

- [ ] Flujo completo: búsqueda → persuasión → compra
- [ ] Persistencia de sesión entre queries
- [ ] Metadata correcta en respuestas
- [ ] Compatibilidad con API GraphQL existente

---

## Cómo Probar

### Opción 1: GraphQL Playground

1. Ir a <http://localhost:8000/graphql>
2. Usar las queries de arriba
3. Revisar respuestas y metadata

### Opción 2: cURL

```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { semanticSearch(query: \"Busco Nike ve\") { answer query } }"
  }'
```

### Opción 3: Python Script

```python
import requests

query = """
query {
  semanticSearch(query: "Ayayay busco Nike ve") {
    answer
    query
  }
}
"""

response = requests.post(
    "http://localhost:8000/graphql",
    json={"query": query}
)

print(response.json())
```

---

## Notas

- Los estilos se detectan analizando los últimos 5 mensajes
- Se necesitan 2+ patrones para confirmar cuencano/juvenil
- Solo 1 patrón es suficiente para formal
- El sistema aprende el estilo a medida que conversas
- Las transferencias entre agentes son automáticas
- El CheckoutAgent siempre usa lógica dura (no LLM)
- El SalesAgent usa Gemini 2.5 Flash
- El RetrieverAgent solo hace SQL
