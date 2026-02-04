# 🧪 Pruebas para el Frontend - Formato Copy/Paste

## 📋 Instrucciones
1. Abre el frontend: http://localhost:3000
2. Login: `cliente@test.com` / `cliente123`
3. Copia cada pregunta y pégala en el chat
4. Anota la respuesta en tu informe

**⚠️ IMPORTANTE - Búsqueda de Productos:**
- ✅ **SÍ funciona**: "¿Tienes zapatillas Nike?", "Busco Adidas", "Productos Puma"
- ❌ **NO funciona**: "Muéstrame productos disponibles", "Qué tienes", "Zapatillas baratas"
- **Razón**: La búsqueda busca palabras literales en nombres de productos (Nike, Adidas, Puma)
- **Solución**: Siempre incluye una MARCA (Nike, Adidas, Puma, New Balance) en tus búsquedas

---

## 🎯 SECCIÓN 1: RAG - Preguntas Frecuentes

### Test 1.1: Política de Devoluciones
```
¿Cuál es la política de devoluciones?
```
**Esperas**: Plazo de 30 días, condiciones, proceso | **Agente**: Retriever | **Fuente**: RAG

---

### Test 1.2: Métodos de Pago
```
¿Qué formas de pago aceptan?
```
**Esperas**: Lista de métodos, seguridad | **Agente**: Retriever | **Fuente**: RAG

---

### Test 1.3: Tiempos de Envío
```
¿Cuánto tarda el envío?
```
**Esperas**: Tiempo estimado, opciones | **Agente**: Retriever | **Fuente**: RAG

---

### Test 1.4: Garantía
```
¿Los productos tienen garantía?
```
**Esperas**: Duración, cobertura, proceso | **Agente**: Retriever | **Fuente**: RAG

---

### Test 1.5: Horarios
```
¿Cuál es su horario de atención?
```
**Esperas**: Días, horas, canales | **Agente**: Retriever | **Fuente**: RAG

---

## 🔍 SECCIÓN 2: Búsqueda de Productos (SQL)

### Test 2.1: Búsqueda por Marca
```
¿Tienes zapatillas Nike?
```
**Esperas**: Lista de Nike, precios, stock | **Agente**: Retriever | **Fuente**: PostgreSQL

---

### Test 2.2: Otra Marca
```
Muéstrame productos Adidas
```
**Esperas**: Lista de Adidas | **Agente**: Retriever | **Fuente**: PostgreSQL

---

### Test 2.3: Búsqueda por Uso
```
Busco zapatillas Nike para correr
```
**Esperas**: Productos Nike running, características | **Agente**: Retriever/Sales | **Fuente**: PostgreSQL
**Nota**: ⚠️ Incluye siempre una marca (Nike, Adidas, Puma) en la búsqueda

---

### Test 2.4: Consulta de Stock
```
¿Hay stock de Nike Air Zoom Pegasus?
```
**Esperas**: Confirmación, cantidad, precio | **Agente**: Retriever | **Fuente**: PostgreSQL

---

### Test 2.5: Listar Todos
```
¿Qué marcas de zapatillas tienes?
```
**Esperas**: Lista de marcas o productos | **Agente**: Retriever/Sales | **Fuente**: PostgreSQL
**Nota**: ⚠️ Evita palabras genéricas como "disponibles", "todos". Usa marcas: Nike, Adidas, Puma

---

### Test 2.6: Rango de Precio
```
¿Tienes zapatillas de menos de $100?
```
**Esperas**: Productos filtrados por precio | **Agente**: Retriever/Sales | **Fuente**: PostgreSQL

---

## 💬 SECCIÓN 3: Persuasión (SalesAgent + LLM)

### Test 3.1: Objeción de Precio
```
Está muy caro
```
**Esperas**: Justificación calidad, comparación, urgencia | **Agente**: SalesAgent | **LLM**: ✅ Sí

---

### Test 3.2: Duda de Calidad
```
No sé si es de buena calidad
```
**Esperas**: Características técnicas, materiales, garantía | **Agente**: SalesAgent | **LLM**: ✅ Sí

---

### Test 3.3: Comparación
```
¿Cuál es la diferencia entre las Nike Air y las Adidas Ultraboost?
```
**Esperas**: Comparación técnica, recomendación | **Agente**: SalesAgent | **LLM**: ✅ Sí

---

### Test 3.4: Solicitud de Descuento
```
¿Puedes darme un descuento?
```
**Esperas**: Manejo cortés, alternativas | **Agente**: SalesAgent | **LLM**: ✅ Sí

---

### Test 3.5: Indecisión
```
No estoy seguro si comprar
```
**Esperas**: Preguntas, recomendación, urgencia | **Agente**: SalesAgent | **LLM**: ✅ Sí

---

### Test 3.6: Cross-Selling
```
Me gustan las Nike Air, ¿algo más que recomiendas?
```
**Esperas**: Productos complementarios | **Agente**: SalesAgent | **LLM**: ✅ Sí

---

### Test 3.7: Upselling
```
Busco unas zapatillas baratas
```
**Esperas**: Opciones económicas + premium | **Agente**: SalesAgent | **LLM**: ✅ Sí

---

## 🛒 SECCIÓN 4: Checkout (Transacciones BD)

**🚨 BUG CRÍTICO DETECTADO:**
- ❌ El `user_id` NO se pasa al CheckoutAgent
- ❌ Las compras NO se completan (loop infinito de transferencias)
- ❌ NO se crean órdenes en BD
- ❌ NO se reduce el inventario
- 📄 Ver [VERIFICAR_COMPRA.md](VERIFICAR_COMPRA.md) para detalles y solución temporal

**Por ahora, SALTA esta sección** o usa `create_test_orders.py` para crear órdenes de prueba.

---

### Test 4.1: Compra Completa (Happy Path) ⚠️ FALLA ACTUALMENTE

**Paso 1:**
```
Quiero comprar las Nike Air Zoom Pegasus
```
**Esperas**: "¿Confirmas que quieres comprar Nike Air Zoom Pegasus 40?"

**Paso 2:**
```
Sí, confirmo
```
**Esperas**: "¿Cuál es tu dirección de envío?"

**Paso 3:**
```
Av. Loja 123, Cuenca, Ecuador
```
**Esperas**: Resumen del pedido, "¿Confirmas tu pedido?"

**Paso 4:**
```
Sí, proceder con el pago
```
**Esperas**: ✅ Pedido confirmado con número de pedido

**Verificar en BD:**
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db -c "SELECT id, user_id, total_amount, status, shipping_address FROM orders ORDER BY created_at DESC LIMIT 1;"
```

---

### Test 4.2: Compra con Cantidad

**Paso 1:**
```
Quiero comprar 2 pares de Adidas Ultraboost
```
**Esperas**: Validación de stock, proceso de checkout

---

### Test 4.3: Sin Stock Suficiente
```
Quiero comprar 100 pares de Nike
```
**Esperas**: Error amigable, "Solo tenemos X unidades"

---

### Test 4.4: Producto Inexistente
```
Quiero comprar las Nike Fake Model 3000
```
**Esperas**: "No encontré ese producto", sugerencias

---

### Test 4.5: Cancelar Compra

**Paso 1:**
```
Quiero comprar Nike Air
```

**Paso 2 (cuando pida confirmación):**
```
Cancelar
```
**Esperas**: "Compra cancelada", transfer a Sales

---

## 🎭 SECCIÓN 5: Detección de Estilo

### Test 5.1: Usuario Casual
```
Ey, ¿qué tal? ¿Tienes unas Nike chéveres?
```
**Esperas**: Tono amigable, lenguaje casual, emojis

---

### Test 5.2: Usuario Formal
```
Buenos días. Quisiera información sobre calzado deportivo de alta gama.
```
**Esperas**: Tono profesional, lenguaje formal, sin emojis

---

### Test 5.3: Usuario Neutral
```
Hola, busco zapatillas para correr
```
**Esperas**: Tono balanceado, profesional pero amigable

---

## 🧩 SECCIÓN 6: Transferencias Entre Agentes

### Test 6.1: Retriever → Sales

**Paso 1:**
```
¿Tienes zapatillas Nike?
```
**Esperas**: Información objetiva (Retriever)

**Paso 2:**
```
Están muy caras
```
**Esperas**: Persuasión (SalesAgent)

---

### Test 6.2: Sales → Checkout

**Paso 1:**
```
Busco zapatillas
```
**Esperas**: Recomendaciones (Sales)

**Paso 2:**
```
Me gustan las Nike, quiero comprarlas
```
**Esperas**: Iniciar checkout (CheckoutAgent)

---

### Test 6.3: Checkout → Sales

**Paso 1:**
```
Comprar Nike Air
```
**Esperas**: Checkout inicia

**Paso 2:**
```
Mejor no, quiero ver otras opciones
```
**Esperas**: Sales retoma con nuevas opciones

---

## ⚠️ SECCIÓN 7: Casos Edge

### Test 7.1: Query Vacío
```
   
```
(solo espacios)
**Esperas**: Mensaje amigable, no crash

---

### Test 7.2: Producto No Existente
```
Busco zapatillas marca XYZ123 inexistente
```
**Esperas**: "No encontré productos", sugerencias

---

### Test 7.3: Múltiples Intenciones
```
Quiero comprar Nike Air pero también quiero saber la política de devoluciones y cuánto cuesta el envío
```
**Esperas**: Manejo secuencial o priorización

---

### Test 7.4: Lenguaje Ofensivo
```
Este chat no sirve
```
**Esperas**: Respuesta cortés, ofrecer ayuda

---

### Test 7.5: Otro Idioma
```
Do you have Nike shoes?
```
**Esperas**: Respuesta en inglés o solicitar español

---

## 🎯 FLUJO COMPLETO E2E (Happy Path)

### Conversación Completa de Principio a Fin

**Paso 1:**
```
Hola
```

**Paso 2:**
```
Busco zapatillas para correr
```

**Paso 3:**
```
¿Cuál me recomiendas?
```

**Paso 4:**
```
Las Nike parecen buenas pero están caras
```

**Paso 5:**
```
Ok, me convenciste. Quiero comprarlas
```

**Paso 6:**
```
Sí, confirmo
```

**Paso 7:**
```
Av. Loja 123, Cuenca
```

**Paso 8:**
```
Sí, proceder
```

**Paso 9:**
```
Gracias
```

**Validar**: Transferencias correctas, contexto mantenido, pedido en BD

---

## 📊 VALIDACIONES DE BASE DE DATOS

### Después de una compra exitosa:

**Ver último pedido:**
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db -c "SELECT id, user_id, total_amount, status, shipping_address, created_at FROM orders ORDER BY created_at DESC LIMIT 1;"
```

**Ver detalles del pedido:**
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db -c "SELECT od.*, ps.product_name, ps.unit_cost FROM order_details od JOIN product_stocks ps ON od.product_id = ps.id ORDER BY od.created_at DESC LIMIT 5;"
```

**Verificar stock reducido:**
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db -c "SELECT product_name, quantity_available FROM product_stocks WHERE product_name LIKE '%Nike Air Zoom%';"
```

---

## ✅ CHECKLIST DE PRUEBAS

Marca cada prueba completada:

**RAG/FAQs:**
- [ ] Política de devoluciones
- [ ] Métodos de pago
- [ ] Tiempos de envío
- [ ] Garantía
- [ ] Horarios

**Productos (SQL):**
- [ ] Búsqueda por marca (Nike)
- [ ] Búsqueda por marca (Adidas)
- [ ] Búsqueda por uso
- [ ] Consulta de stock
- [ ] Listar todos
- [ ] Rango de precio

**Persuasión (LLM):**
- [ ] Objeción de precio
- [ ] Duda de calidad
- [ ] Comparación de productos
- [ ] Solicitud de descuento
- [ ] Indecisión
- [ ] Cross-selling
- [ ] Upselling

**Checkout (BD):**
- [ ] Compra completa exitosa
- [ ] Compra con cantidad
- [ ] Sin stock suficiente
- [ ] Producto inexistente
- [ ] Cancelar compra
- [ ] Pedido en BD ✅
- [ ] Stock reducido ✅

**Estilo:**
- [ ] Usuario casual
- [ ] Usuario formal
- [ ] Usuario neutral

**Transferencias:**
- [ ] Retriever → Sales
- [ ] Sales → Checkout
- [ ] Checkout → Sales

**Casos Edge:**
- [ ] Query vacío
- [ ] Producto inexistente
- [ ] Múltiples intenciones
- [ ] Lenguaje ofensivo
- [ ] Otro idioma

**E2E:**
- [ ] Flujo completo happy path

---

## 📝 PLANTILLA PARA TU INFORME

Para cada prueba anota:

```
PRUEBA: [Número y título]
ENTRADA: [Pregunta copiada]
RESPUESTA: [Lo que respondió Alex]
AGENTE: [Retriever/Sales/Checkout]
HERRAMIENTAS: [RAG/SQL/LLM/BD]
ESTADO: [✅ Exitoso / ⚠️ Parcial / ❌ Fallido]
OBSERVACIONES: [Notas adicionales]
```

---

**¡Listo para copiar y pegar en el chat!** 🚀
