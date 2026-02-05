# 🔄 Flujo End-to-End Completo

Flujo conversacional simple con sesiones Redis.

---

## 📋 Flujo General

```
ENTRA GUION (procesarGuionAgente2)
    ↓
RECOMIENDA PRODUCTO 1 (mejor opción)
    ↓
USUARIO APRUEBA / RECHAZA (continuarConversacion)
    ↓
    ├── SI APRUEBA → Pide talla/dirección → Checkout
    │
    └── SI RECHAZA → Recomienda PRODUCTO 2 (segunda opción del guion)
            ↓
        Usuario aprueba/rechaza
            ↓
        (Si rechaza otra vez y no hay más, fin de ciclo)
```

---

## 🔑 Mutations

### 1. `procesarGuionAgente2` - Inicio

Recibe guion del Agente 2, compara productos, recomienda el mejor y guarda sesión.

```graphql
mutation IniciarConversacion {
  procesarGuionAgente2(
    guion: {
      sessionId: "sess-demo-001"
      productos: [
        {codigoBarras: "7501234567891", nombreDetectado: "Nike Air Max 90", prioridad: "alta"}
        {codigoBarras: "7501234567894", nombreDetectado: "Nike Court Vision", prioridad: "media"}
      ]
      preferencias: {
        estiloComunicacion: "cuencano"
        presupuestoMaximo: 150
      }
      contexto: {
        tipoEntrada: "texto"
        intencionPrincipal: "compra_directa"
      }
      textoOriginalUsuario: "Quiero zapatillas"
      resumenAnalisis: "Usuario busca zapatillas"
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

**Respuesta:** Recomienda el mejor producto (ej: Nike Air Max 90).

---

### 2. `continuarConversacion` - Continuar flujo

Procesa respuesta del usuario.

#### ✅ Usuario aprueba

```graphql
mutation {
  continuarConversacion(
    sessionId: "sess-demo-001"
    respuestaUsuario: "Sí me interesa"
  ) {
    mensaje      # "¡Excelente! ¿Qué talla y dirección?"
    siguientePaso # "solicitar_datos_envio"
  }
}
```

#### ❌ Usuario rechaza

```graphql
mutation {
  continuarConversacion(
    sessionId: "sess-demo-001"
    respuestaUsuario: "No me gustan"
  ) {
    mensaje      # "Entiendo. Entonces mira esta opción: Nike Court Vision..."
    siguientePaso # "confirmar_compra" (recomienda segunda opción)
  }
}
```

**Importante:** Si el guion tenía más de 1 producto, recomienda el **segundo mejor** automáticamente.

---

## 🎯 Estados de Conversación

| Estado | Descripción | Siguiente Acción |
|--------|-------------|------------------|
| `esperando_confirmacion` | Esperando sí/no | `continuarConversacion` |
| `solicitar_datos_envio` | Pedir talla/dirección | `continuarConversacion` |
| `listo_para_checkout` | Ir a checkout | Frontend redirige |

---

## 🚀 Flujo Ejemplo Completo

### Caso 1: Usuario aprueba a la primera

```
1. procesarGuionAgente2 → "Te recomiendo Nike Air Max 90..."
2. Usuario: "Sí me interesa"
3. continuarConversacion → "¿Qué talla y dirección?"
4. Usuario: "Talla 42, Av. Americas 123"
5. continuarConversacion → "Listo, te llevo a caja"
6. Frontend: redirige a checkout
```

### Caso 2: Usuario rechaza una vez

```
1. procesarGuionAgente2 → "Te recomiendo Nike Air Max 90..."
2. Usuario: "No me gustan"
3. continuarConversacion → "Entonces mira: Nike Court Vision..."
4. Usuario: "Sí, esas sí"
5. continuarConversacion → "¿Qué talla y dirección?"
6. ...continúa flujo normal
```

### Caso 3: Usuario rechaza todo

```
1. procesarGuionAgente2 → "Te recomiendo Nike Air Max 90..."
2. Usuario: "No"
3. continuarConversacion → "Entonces mira: Nike Court Vision..."
4. Usuario: "Tampoco"
5. continuarConversacion → "Entiendo. No tengo más opciones..."
6. siguientePaso: "nueva_conversacion"
```

---

## 💾 Sesiones Redis

- **Key:** `session:{session_id}`
- **TTL:** 30 minutos
- **Guarda:** productos del guion, selección actual, etapa

---

## 📊 Diagrama Simple

```
┌─────────────────────────────────────────────┐
│  procesarGuionAgente2                       │
│  (compara productos, guarda en sesión)      │
└──────────────┬──────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────┐
│  Recomienda MEJOR producto                  │
│  (producto con mayor score)                 │
└──────────────┬──────────────────────────────┘
               │
       ┌───────┴───────┐
       ▼               ▼
   ACEPTA           RECHAZA
       │               │
       ▼               ▼
Pide datos      ¿Hay más productos
                   en el guion?
                       │
              ┌────────┴────────┐
              ▼                 ▼
            SÍ (hay)          NO (solo 1)
              │                 │
              ▼                 ▼
    Recomienda SEGUNDO    "No tengo más"
    mejor producto        "¿Nueva búsqueda?"
              │
              └────────┐
                       │
              ┌────────┴────────┐
              ▼                 ▼
          ACEPTA              RECHAZA
              │                 │
              ▼                 ▼
        Pide datos      "No tengo más"
                              "¿Nueva búsqueda?"
```

---

*Documento generado: Febrero 2026*
