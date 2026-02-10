# 📊 SISTEMA DE LOGGING - Flujo Completo Agente 2 → Agente 3

**Fecha:** 10 de febrero de 2026  
**Propósito:** Documentar todos los logs que aparecen en cada paso del flujo para debugging y seguimiento

---

## 🎯 VISIÓN GENERAL

El sistema genera logs detallados en cada paso del flujo de ventas, desde que el usuario escribe un mensaje hasta que se crea la orden. Los logs están organizados jerárquicamente y usan emojis para facilitar la lectura.

### Niveles de Log:
- **INFO** 🔵 - Flujo normal del sistema
- **WARNING** 🟡 - Situaciones anormales pero recuperables
- **ERROR** 🔴 - Errores que impiden completar la operación

---

## 📋 FLUJO COMPLETO DE LOGS

### 1️⃣ INICIO DE APLICACIÓN

```
⚠️  SECRET_KEY no encontrada, usando valor por defecto para desarrollo
INFO - Contenedor de servicios iniciado correctamente.
INFO - ✅ Rate limiting configurado
INFO - ✅ CORS configurado para localhost:3000
INFO - Arrancando servidor en http://0.0.0.0:8000
```

**Qué significa:**
- Sistema iniciando
- Dependencias inyectadas
- Configuraciones aplicadas
- Servidor listo en puerto 8000

---

### 2️⃣ AUTENTICACIÓN DE USUARIO

```
INFO - OPTIONS /auth/login HTTP/1.1" 200 OK
INFO - POST /auth/login HTTP/1.1" 200 OK
```

**Qué significa:**
- Usuario inició sesión
- Token JWT generado
- Autenticación exitosa

---

### 3️⃣ CARGA DE PRODUCTOS (Inicial)

```
INFO - GraphQL: Listando 100 productos (usuario=Cliente1)
INFO - 🗃️ ProductService: Listados 32 productos
```

**Qué significa:**
- Frontend cargó lista de productos
- 32 productos disponibles en BD
- Usuario "Cliente1" autenticado

---

### 4️⃣ PROCESAMIENTO DE GUION (procesarGuionAgente2)

#### **4.1 Entrada del Guion**

```
================================================================================
🎬 INICIO FLUJO GUION AGENTE 2 → AGENTE 3
================================================================================
📋 Datos de entrada:
   • Usuario: Cliente1
   • Session ID: sess-1770314205998-ojthmt9db
   • Productos detectados: 3
   • Presupuesto máximo: $130
   • Urgencia: media
   • Busca ofertas: Sí
   • Estilo comunicación: cuencano
   • Uso previsto: trabajo y casa
   • Texto original usuario: Buenas tardes, necesito comprar unas zapatillas para mi trabajo...
--------------------------------------------------------------------------------
```

**Qué significa:**
- Inicio del flujo principal
- Usuario y sesión identificados
- Preferencias del usuario capturadas
- 3 productos detectados por Agente 2

#### **4.2 Extracción de Códigos de Barras**

```
📦 PASO 1: Extrayendo códigos de barras de productos detectados
   ✅ Códigos de barras extraídos: 3
   1. Nike Air Max 90
      • Código: 7501234567891
      • Prioridad: ALTA
      • Motivo: Zapatilla clásica, buen precio
   2. Adidas Ultraboost
      • Código: 8806098934474
      • Prioridad: MEDIA
      • Motivo: Súper cómoda para caminar
   3. Nike Court Vision Low
      • Código: 7501234567894
      • Prioridad: BAJA
      • Motivo: Alternativa económica
--------------------------------------------------------------------------------
```

**Qué significa:**
- Agente 2 detectó 3 productos
- Cada uno con su código de barras
- Prioridades asignadas (alta → media → baja)
- Razones de selección documentadas

#### **4.3 Búsqueda en Base de Datos**

```
🔍 PASO 2: Buscando productos en base de datos por códigos de barras
INFO - 🗃️ Búsqueda por barcodes: 3/3 encontrados
   ✅ Productos encontrados en BD: 3
   • Nike Air Max 90 - $104.0000 (antes $130.00, 10.00% OFF) - Stock: 10
   • Adidas Ultraboost Light - $180.00 - Stock: 8
   • Nike Court Vision Low - $45.0000 (antes $75.00, 20.00% OFF) - Stock: 15
--------------------------------------------------------------------------------
```

**Qué significa:**
- Los 3 códigos de barras se encontraron en BD
- Air Max 90: en oferta 10% OFF
- Ultraboost: sin oferta
- Court Vision: en oferta 20% OFF
- Stock disponible para todos

#### **4.4 Comparación y Scoring**

```
⚖️  PASO 3: Comparando productos y generando recomendación
   ✅ Mejor opción seleccionada: Nike Air Max 90
   • Score: 75/100
   • Precio: $104.00
   • Razón: Producto de alta prioridad; Precio dentro del presupuesto; En oferta
   📊 Alternativas disponibles: 2
      2. Nike Court Vision Low - Score: 65/100 - $45.00
      3. Adidas Ultraboost Light - Score: 35/100 - $180.00
--------------------------------------------------------------------------------
```

**Qué significa:**
- ProductComparisonService evaluó los 3 productos
- Air Max 90 ganó con 75 puntos
- Court Vision segunda opción (65 pts)
- Ultraboost tercera (35 pts, excede presupuesto)
- Razones claras de scoring

#### **4.5 Generación de Mensaje Persuasivo**

```
💬 PASO 4: Generando mensaje persuasivo (estilo: cuencano)
   ✅ LLM generó mensaje personalizado (245 caracteres)
```

**Qué significa:**
- LLM (Gemini) generó texto persuasivo
- Estilo cuencano aplicado
- Mensaje natural y conversacional

#### **4.6 Guardado en Redis**

```
💾 Sesión guardada en Redis:
   • Session ID: sess-1770314205998-ojthmt9db
   • TTL: 1800 segundos (30 minutos)
   • Productos en sesión: 3
   • Mejor opción ID: 94d7c19b-856f-4f99-a6e6-553e0a1eac26
--------------------------------------------------------------------------------
```

**Qué significa:**
- Sesión guardada para continuación
- Expira en 30 minutos
- Contiene los 3 productos evaluados
- ID del producto recomendado guardado

#### **4.7 Finalización Exitosa**

```
✅ FLUJO COMPLETADO EXITOSAMENTE
   • Siguiente paso: confirmar_compra
   • Mensaje generado para usuario (245 caracteres)
================================================================================
INFO - POST /graphql HTTP/1.1" 200 OK
```

**Qué significa:**
- Todo el flujo completado sin errores
- Frontend debe mostrar confirmación
- Respuesta 200 OK enviada

---

### 5️⃣ CONTINUACIÓN DE CONVERSACIÓN (continuarConversacion)

#### **5.1 Usuario Responde "Sí"**

```
================================================================================
🔄 CONTINUACIÓN DE CONVERSACIÓN
================================================================================
📨 Datos de entrada:
   • Session ID: sess-1770314205998-ojthmt9db
   • Respuesta usuario: "Sí"
   • Usuario: Cliente1
--------------------------------------------------------------------------------
```

**Qué significa:**
- Usuario aprobó la recomendación
- Iniciando siguiente paso del flujo

#### **5.2 Recuperación de Sesión**

```
🔍 PASO 1: Recuperando sesión de Redis
   ✅ Sesión encontrada
   • Productos en sesión: 3
   • Mejor opción ID: 94d7c19b-856f-4f99-a6e6-553e0a1eac26
   • Estilo comunicación: cuencano
--------------------------------------------------------------------------------
```

**Qué significa:**
- Sesión recuperada exitosamente
- Datos conservados de paso anterior
- Continuidad del flujo mantenida

#### **5.3 Detección de Intención**

```
🎯 PASO 2: Analizando respuesta del usuario
   ✅ Intención detectada: APROBACIÓN
   • Palabras clave: ["sí"]
   • Confianza: ALTA
   • Acción: Solicitar datos de envío
--------------------------------------------------------------------------------
```

**Qué significa:**
- Sistema entendió que usuario dijo "Sí"
- No es rechazo ni datos de envío
- Debe pedir talla y dirección

#### **5.4 Solicitud de Datos**

```
✅ SIGUIENTE PASO: solicitar_datos_envio
   • Mensaje generado (87 caracteres)
================================================================================
INFO - POST /graphql HTTP/1.1" 200 OK
```

**Qué significa:**
- Sistema pide talla y dirección
- Respuesta enviada al frontend

---

### 6️⃣ USUARIO PROPORCIONA DATOS

#### **6.1 Extracción de Datos**

```
================================================================================
🔄 CONTINUACIÓN DE CONVERSACIÓN
================================================================================
📨 Datos de entrada:
   • Session ID: sess-1770314205998-ojthmt9db
   • Respuesta usuario: "Talla 42, Av. Américas 123"
--------------------------------------------------------------------------------
🎯 PASO 2: Analizando respuesta del usuario
   ✅ Intención detectada: DATOS DE ENVÍO
   • Talla extraída: 42
   • Dirección extraída: Av. Américas 123
   • Validación: EXITOSA
--------------------------------------------------------------------------------
```

**Qué significa:**
- Usuario proporcionó talla y dirección
- Expresiones regulares extrajeron los datos
- Datos validados correctamente

#### **6.2 Creación de Orden**

```
📦 PASO 3: Creando orden en base de datos
   • Producto ID: 94d7c19b-856f-4f99-a6e6-553e0a1eac26
   • Producto: Nike Air Max 90
   • Cantidad: 1
   • Talla: 42
   • Dirección: Av. Américas 123
   • Total: $104.00
--------------------------------------------------------------------------------
INFO - 🛒 OrderService: Creando orden para Cliente1
INFO - 🛒 OrderService: Producto Nike Air Max 90 agregado (cantidad: 1)
INFO - ✅ OrderService: Orden creada exitosamente - Total: $104.00
```

**Qué significa:**
- Orden creándose en PostgreSQL
- Producto agregado a detalles de orden
- Stock verificado y reservado
- Total calculado

#### **6.3 Confirmación Final**

```
✅ ORDEN CREADA EXITOSAMENTE
   • Número de orden: ORD-94D7C19B
   • Producto: Nike Air Max 90
   • Talla: 42
   • Dirección: Av. Américas 123
   • Total: $104.00
   • Estado: Pendiente
   • Sesión marcada como completada
================================================================================
INFO - POST /graphql HTTP/1.1" 200 OK
```

**Qué significa:**
- Orden guardada en BD con éxito
- Número de orden generado
- Usuario recibe confirmación
- Flujo completado

---

## 🔍 LOGS DE ERROR COMUNES

### Error 1: Producto sin stock

```
❌ ERROR: Stock insuficiente
   • Producto: Nike Air Max 90
   • Stock disponible: 0
   • Cantidad solicitada: 1
   • Acción: Sugerir alternativa
```

### Error 2: Sesión expirada

```
❌ ERROR: Sesión no encontrada en Redis
   • Session ID: sess-123456
   • Posible causa: TTL expirado (>30 min)
   • Acción: Reiniciar conversación
```

### Error 3: Código de barras no existe

```
❌ ERROR: Producto no encontrado en BD
   • Código de barras: 999999999999
   • Productos encontrados: 2/3
   • Acción: Continuar con productos encontrados
```

---

## 📊 ESTADÍSTICAS DE LOGS

### Por cada solicitud del usuario se generan:

| Paso | Logs INFO | Logs DEBUG | Total |
|------|-----------|------------|-------|
| procesarGuionAgente2 | ~25 | ~10 | ~35 |
| continuarConversacion (aprobación) | ~15 | ~5 | ~20 |
| continuarConversacion (datos) | ~20 | ~8 | ~28 |
| Creación de orden | ~12 | ~6 | ~18 |
| **TOTAL por flujo completo** | **~72** | **~29** | **~101** |

---

## 🎨 CÓDIGOS DE COLOR EN TERMINAL

- `================` - Separadores de secciones
- `🎬` - Inicio de flujo principal
- `📋` - Datos de entrada
- `📦` - Productos
- `🔍` - Búsquedas
- `⚖️` - Comparaciones
- `💬` - Generación de mensajes
- `💾` - Operaciones de Redis
- `✅` - Éxito
- `❌` - Error
- `🔄` - Continuación
- `🎯` - Detección de intención
- `📨` - Entrada de usuario
- `🛒` - Órdenes

---

## 🔧 CONFIGURACIÓN DE LOGGING

### Archivo: `backend/config/logging_config.py`

- **Desarrollo:** Pretty print con colores
- **Producción:** JSON estructurado
- **Tests:** Silenciado

### Variables de entorno:

```bash
ENVIRONMENT=development  # development, staging, production
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
```

---

## 📝 EJEMPLO COMPLETO DE TERMINAL

```bash
$ uv run uvicorn backend.main:app --reload --port 8000

⚠️  SECRET_KEY no encontrada, usando valor por defecto para desarrollo
INFO - Contenedor de servicios iniciado correctamente.
INFO - ✅ Rate limiting configurado
INFO - ✅ CORS configurado para localhost:3000
INFO - Started server process [360198]
INFO - Waiting for application startup.
INFO - Application startup complete.

# Usuario hace login
INFO - POST /auth/login HTTP/1.1" 200 OK

# Usuario carga productos
INFO - GraphQL: Listando 100 productos (usuario=Cliente1)
INFO - 🗃️ ProductService: Listados 32 productos

# Usuario envía guion
================================================================================
🎬 INICIO FLUJO GUION AGENTE 2 → AGENTE 3
================================================================================
📋 Datos de entrada:
   • Usuario: Cliente1
   • Session ID: sess-1770314205998-ojthmt9db
   • Productos detectados: 3
   • Presupuesto máximo: $130
   • Urgencia: media
   • Busca ofertas: Sí
   • Estilo comunicación: cuencano
   • Uso previsto: trabajo y casa
--------------------------------------------------------------------------------
📦 PASO 1: Extrayendo códigos de barras de productos detectados
   ✅ Códigos de barras extraídos: 3
   1. Nike Air Max 90 - Código: 7501234567891 - ALTA
   2. Adidas Ultraboost - Código: 8806098934474 - MEDIA
   3. Nike Court Vision Low - Código: 7501234567894 - BAJA
--------------------------------------------------------------------------------
🔍 PASO 2: Buscando productos en base de datos
INFO - 🗃️ Búsqueda por barcodes: 3/3 encontrados
   ✅ Productos encontrados en BD: 3
   • Nike Air Max 90 - $104.00 (10% OFF) - Stock: 10
   • Adidas Ultraboost Light - $180.00 - Stock: 8
   • Nike Court Vision Low - $45.00 (20% OFF) - Stock: 15
--------------------------------------------------------------------------------
⚖️  PASO 3: Comparando productos y generando recomendación
   ✅ Mejor opción: Nike Air Max 90 - Score: 75/100
   📊 Alternativas: 2 productos
--------------------------------------------------------------------------------
💾 Sesión guardada en Redis: sess-1770314205998-ojthmt9db
✅ FLUJO COMPLETADO EXITOSAMENTE
================================================================================
INFO - POST /graphql HTTP/1.1" 200 OK

# Usuario responde "Sí"
================================================================================
🔄 CONTINUACIÓN DE CONVERSACIÓN
================================================================================
📨 Respuesta usuario: "Sí"
🔍 Recuperando sesión de Redis
🎯 Intención detectada: APROBACIÓN
✅ SIGUIENTE PASO: solicitar_datos_envio
================================================================================

# Usuario da talla y dirección
================================================================================
🔄 CONTINUACIÓN DE CONVERSACIÓN
================================================================================
📨 Respuesta usuario: "Talla 42, Av. Américas 123"
🎯 Datos extraídos: Talla 42, Av. Américas 123
📦 Creando orden en BD
INFO - 🛒 OrderService: Orden creada - Total: $104.00
✅ ORDEN CREADA: ORD-94D7C19B
================================================================================
INFO - POST /graphql HTTP/1.1" 200 OK
```

---

## ✅ CHECKLIST PARA DEBUGGING

Cuando algo falla, revisar estos logs en orden:

1. [ ] ¿Aparece el log `🎬 INICIO FLUJO`? → Sistema recibió el guion
2. [ ] ¿Cuántos productos detectados? → Validar códigos de barras
3. [ ] ¿Dice `3/3 encontrados`? → Productos existen en BD
4. [ ] ¿Hay score > 0 para mejor opción? → Comparación funcionó
5. [ ] ¿Aparece `💾 Sesión guardada`? → Redis funcionando
6. [ ] ¿Intención detectada correctamente? → Parsing de respuesta OK
7. [ ] ¿Orden creada con número? → BD y stock OK

---

**Última actualización:** 10 de febrero de 2026
