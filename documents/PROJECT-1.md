# Contexto del Proyecto: Asistente de Ventas y Atención al Cliente (GenAI)

## 1. Visión General

El objetivo no es crear un simple chatbot de soporte ("Q&A"), sino un **Agente de Ventas Activo**. El sistema debe comportarse como un vendedor experto que guía al usuario desde una necesidad vaga hasta la confirmación de un pedido, utilizando técnicas de persuasión y acceso a herramientas reales (inventario, base de datos).

---

## 2. Requerimientos Críticos (Notas de Clase)

Basado en las directrices del ingeniero, el agente debe cumplir estrictamente con tres comportamientos:

1. **Persuasión de Venta:** El agente no es pasivo. Debe intentar convencer al cliente destacando beneficios, ofertas o urgencia ("quedan pocas unidades") para cerrar la venta.
2. **Venta Consultiva (Discovery -> Delivery):**
    * Escuchar: Entender qué busca el cliente (ej: "tengo una cena elegante").
    * Procesar: Cruzar esa necesidad con el inventario disponible.
    * Recomendar: Ofrecer el producto exacto y crear el pedido.
3. **Persistencia del Ciclo de Vida:** El agente debe mantener el hilo de la conversación y seguir intentando ayudar/vender hasta que ocurra uno de dos eventos finales:
    * El cliente concreta la compra (Éxito).
    * El cliente se despide o rechaza explícitamente la interacción (Cierre).

---

## 3. Arquitectura Lógica del Sistema

El sistema se divide en **Agentes Especializados** orquestados por un planificador central.

### A. Router/Planner (El Cerebro)

* **Función:** Analiza la intención del usuario en cada mensaje.
* **Decisión:** ¿El usuario tiene una duda técnica (RAG), quiere comprar (Sales), o ya va a pagar (Order)?
* **Persistencia:** Mantiene el contexto de la conversación (memoria) para no olvidar qué producto le gustó al usuario hace 5 mensajes.

### B. Recommendation Agent (El Vendedor)

* *Este es el núcleo de la "Persuasión".*
* **Lógica:** Combina reglas de negocio + búsqueda semántica.
* **Input:** Perfil del usuario + Restricciones ("barato", "rojo") + Inventario real.
* **Output:** Argumentos de venta (ej: "Te recomiendo X porque mencionaste que buscas durabilidad, y este tiene la mejor reseña en eso").

### C. RAG Agent (El Experto en Producto)

* **Función:** Responder dudas específicas para eliminar fricción en la compra.
* **Fuente:** Manuales, políticas de devolución, tablas nutricionales, garantías.
* **Objetivo:** Que el cliente no se vaya por falta de información.

### D. Order Agent (El Cajero)

* **Función:** Transaccional pura.
* **Tareas:**
    1. Validar stock final.
    2. Confirmar dirección y método de pago.
    3. Generar el registro en la base de datos.

### E. Verifier Agent (Control de Calidad)

* **Función:** Evitar alucinaciones.
* **Regla de Oro:** "Si no está en el inventario, no existe". Filtra las respuestas del LLM para asegurar que no venda productos imaginarios.

---

## 4. Capacidades del Sistema (Tools)

El LLM interactuará con el backend a través de estas funciones definidas (Function Calling):

| Tool / Función | Descripción | Uso |
| :--- | :--- | :--- |
| `tool_inventory_query` | Consulta SQL filtrada al stock. | Verificar disponibilidad y precios en tiempo real. |
| `tool_product_recognition` | (Opcional) Modelo de visión. | Si el cliente sube una foto: "Quiero algo como esto". |
| `tool_recommend` | Motor de búsqueda híbrida (Vectorial + SQL). | Encontrar el mejor "match" para la necesidad del cliente. |
| `tool_order_create` | Transacción de escritura en DB. | Crear el pedido formalmente y reservar stock. |

---

## 5. Flujo de Interacción Típico

1. **Descubrimiento:**
    * *Usuario:* "Busco unos zapatos para correr en asfalto".
    * *Agente:* (Consulta inventario + RAG sobre tipos de suela) -> "Tengo los Nike Pegasus que son ideales para asfalto..."
2. **Persuasión:**
    * *Usuario:* "Están muy caros".
    * *Agente:* (Recommendation Agent) -> "Entiendo, pero considera que tienen doble durabilidad que los económicos. A la larga ahorras. Además, quedan solo 2 en tu talla".
3. **Cierre:**
    * *Usuario:* "Bueno, dámelos".
    * *Agente:* (Order Agent) -> "Perfecto. ¿Uso tu dirección de envío guardada en Cuenca? Confirmando pedido..."

---

## 6. Stack Tecnológico Sugerido (Python Focus)

* **Orquestación:** LangChain o LangGraph.
* **LLM:** Modelos locales (Ollama/Llama3) o API Externa.
* **Base de Datos Vectorial (RAG):** ChromaDB o Qdrant.
* **Base de Datos Relacional (Inventario):** PostgreSQL.
* **Backend API:** FastAPI.
