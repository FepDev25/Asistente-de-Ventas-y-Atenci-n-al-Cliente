# 🔄 Flujo End-to-End Completo

Flujo conversacional con sesiones Redis para persistencia de estado.

---

## 📋 Flujo General

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  1. ENTRA GUION │────▶│ 2. RECOMENDACIÓN │────▶│ 3. USUARIO      │
│   (Agente 2)    │     │    (Agente 3)    │     │   APRUEBA/NO    │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                              ┌───────────────────────────┼───────────┐
                              │                           │           │
                              ▼                           ▼           ▼
                       ┌─────────────┐           ┌──────────────┐ ┌──────────┐
                       │ 4A. SI      │           │ 4B. PIDE     │ │ 5. NO    │
                       │   APRUEBA   │──────────▶│    DATOS     │ │  REBOTA  │
                       └─────────────┘           └──────────────┘ └────┬─────┘
                                                                        │
                                                                        ▼
                                                              ┌──────────────────┐
                                                              │ 6. NUEVA         │
                                                              │    RECOMENDACIÓN │
                                                              │    (vuelve a 2)  │
                                                              └──────────────────┘
```

---

## 🔑 Mutations Disponibles

### 1. `procesarGuionAgente2` - Inicio del flujo

Recibe el guion del Agente 2, genera recomendación y guarda sesión en Redis.

```graphql
mutation IniciarConversacion {
  procesarGuionAgente2(
    guion: {
      sessionId: "sess-demo-001"
      productos: [
        {
          codigoBarras: "7501234567891"
          nombreDetectado: "Nike Air Max 90"
          prioridad: "alta"
          motivoSeleccion: "Zapatilla clásica"
        }
      ]
      preferencias: {
        estiloComunicacion: "cuencano"
        presupuestoMaximo: 150
        urgencia: "media"
        usoPrevisto: "Uso casual diario"
      }
      contexto: {
        tipoEntrada: "texto"
        intencionPrincipal: "compra_directa"
        necesitaRecomendacion: true
      }
      textoOriginalUsuario: "Quiero unas zapatillas cómodas"
      resumenAnalisis: "Usuario busca zapatillas lifestyle"
      confianzaProcesamiento: 0.92
    }
  ) {
    success
    mensaje
    mejorOpcionId
    siguientePaso
  }
}
```

**Respuesta esperada:**
```json
{
  "data": {
    "procesarGuionAgente2": {
      "success": true,
      "mensaje": "¡Qué más, mi pana! Mirá, estas Nike Air Max 90... ¿Te gustaría saber más?",
      "mejorOpcionId": "uuid-del-producto",
      "siguientePaso": "confirmar_compra"
    }
  }
}
```

**Importante:** La sesión se guarda automáticamente en Redis con `sessionId`.

---

### 2. `continuarConversacion` - Continuar el flujo

Procesa la respuesta del usuario y determina el siguiente paso.

#### Caso A: Usuario aprueba ✅

```graphql
mutation UsuarioAprueba {
  continuarConversacion(
    sessionId: "sess-demo-001"
    respuestaUsuario: "Sí, me interesan"
  ) {
    success
    mensaje
    siguientePaso
  }
}
```

**Respuesta:**
```json
{
  "data": {
    "continuarConversacion": {
      "success": true,
      "mensaje": "¡Excelente! ¿Qué talla necesitas y a qué dirección te los enviamos?",
      "siguientePaso": "solicitar_datos_envio"
    }
  }
}
```

---

#### Caso B: Usuario da datos de envío 📦

```graphql
mutation UsuarioDaDatos {
  continuarConversacion(
    sessionId: "sess-demo-001"
    respuestaUsuario: "Talla 42, dirección Av. Americas 123"
  ) {
    success
    mensaje
    siguientePaso
  }
}
```

**Respuesta:**
```json
{
  "data": {
    "continuarConversacion": {
      "success": true,
      "mensaje": "¡Perfecto! Recibí talla 42 y dirección Av. Americas. Ahora te llevo a completar la compra.",
      "siguientePaso": "ir_a_checkout"
    }
  }
}
```

**Frontend:** Cuando recibe `siguientePaso: "ir_a_checkout"`, redirige a la pantalla de checkout con el `sessionId`.

---

#### Caso C: Usuario rechaza ❌

```graphql
mutation UsuarioRechaza {
  continuarConversacion(
    sessionId: "sess-demo-001"
    respuestaUsuario: "No me convencen, tienes otros?"
  ) {
    success
    mensaje
    siguientePaso
  }
}
```

**Respuesta:**
```json
{
  "data": {
    "continuarConversacion": {
      "success": true,
      "mensaje": "Entiendo, ¿qué es lo que buscas? Puedo mostrarte otras opciones.",
      "siguientePaso": "nueva_recomendacion"
    }
  }
}
```

**Frontend:** Cuando recibe `siguientePaso: "nueva_recomendacion"`, puede:
1. Llamar nuevamente a `procesarGuionAgente2` con nuevos productos
2. O usar `semanticSearch` para buscar alternativas

---

## 🎯 Estados de Conversación

| Estado | Descripción | Siguiente Acción |
|--------|-------------|------------------|
| `esperando_confirmacion` | Recomendación enviada | Usuario responde sí/no |
| `esperando_datos_envio` | Usuario aprobó | Pedir talla y dirección |
| `listo_para_checkout` | Datos completos | Ir a checkout |
| `buscando_alternativas` | Usuario rechazó | Nueva recomendación |

---

## 💾 Sesiones Redis

Las sesiones se almacenan en Redis con:
- **Key:** `session:{session_id}`
- **TTL:** 30 minutos (1800 segundos)
- **Contenido:** `AgentState` con productos seleccionados, etapa de conversación, metadata

### Ejemplo de sesión guardada:

```json
{
  "session_id": "sess-demo-001",
  "user_query": "Quiero unas zapatillas cómodas",
  "search_results": [
    {
      "id": "uuid-1",
      "name": "Nike Air Max 90",
      "price": 104.00,
      "barcode": "7501234567891"
    }
  ],
  "selected_products": ["uuid-1"],
  "conversation_stage": "esperando_confirmacion",
  "metadata": {
    "estilo": "cuencano",
    "producto_recomendado": "Nike Air Max 90",
    "precio": 104.00
  },
  "created_at": "2026-02-05T10:30:00"
}
```

---

## 🚀 Flujo Completo Ejemplo

### Paso 1: Iniciar
```graphql
mutation {
  procesarGuionAgente2(guion: {...}) {
    mensaje  # "¡Qué más! Mirá estas Nike Air Max..."
    siguientePaso  # "confirmar_compra"
  }
}
```

### Paso 2: Usuario responde
```graphql
mutation {
  continuarConversacion(
    sessionId: "sess-demo-001"
    respuestaUsuario: "Dale, me gustan"
  ) {
    mensaje  # "¡Excelente! ¿Qué talla y dirección?"
    siguientePaso  # "solicitar_datos_envio"
  }
}
```

### Paso 3: Usuario da datos
```graphql
mutation {
  continuarConversacion(
    sessionId: "sess-demo-001"
    respuestaUsuario: "Talla 42, envío a Av. Americas 123"
  ) {
    mensaje  # "¡Perfecto! Te llevo a caja"
    siguientePaso  # "ir_a_checkout"
  }
}
```

### Paso 4: Frontend redirige
```javascript
// Cuando siguientePaso === "ir_a_checkout"
window.location.href = `/checkout?session=${sessionId}`;
```

---

## ⚠️ Manejo de Errores

### Sesión expirada
```json
{
  "success": false,
  "mensaje": "La sesión expiró. Por favor, inicia una nueva conversación.",
  "siguientePaso": "nueva_conversacion"
}
```

### Sesión no encontrada
Ocurre si:
- Pasaron más de 30 minutos
- Redis se reinició
- El `sessionId` es incorrecto

**Solución:** Iniciar nuevo flujo con `procesarGuionAgente2`.

---

## 📊 Diagrama de Estados

```
                    ┌─────────────────┐
                    │    INICIO       │
                    │ (procesarGuion) │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
         ┌─────────│ ESPERANDO       │◄────────────────┐
         │         │ CONFIRMACIÓN    │                 │
         │         └────────┬────────┘                 │
         │                  │                          │
    ┌────┴────┐        ┌────┴────┐                     │
    │   SI    │        │   NO    │                     │
    │(aprobó) │        │(rechazó)│                     │
    └────┬────┘        └────┬────┘                     │
         │                  │                          │
         ▼                  ▼                          │
┌─────────────────┐  ┌─────────────────┐               │
│ ESPERANDO       │  │ BUSCANDO        │───────────────┘
│ DATOS ENVÍO     │  │ ALTERNATIVAS    │  (nueva recomendación)
└────────┬────────┘  └─────────────────┘
         │
         ▼
┌─────────────────┐
│ LISTO PARA      │──────► Checkout
│ CHECKOUT        │
└─────────────────┘
```

---

*Documento generado: Febrero 2026*
