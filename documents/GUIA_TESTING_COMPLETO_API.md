# Guia de Testing Completo del Sistema

Documento para probar todos los endpoints del backend paso a paso.
Ultima actualizacion: 2026-02-03 (con JWT obligatorio)

---

## 1. Preparacion

### 1.1 Verificar que los servicios esten corriendo

```bash
# Verificar PostgreSQL
docker-compose ps

# Verificar Redis (si esta configurado)
redis-cli ping
# Respuesta esperada: PONG

# Verificar backend
curl http://localhost:8000/health
```

---

## 2. Autenticacion (Obligatoria para GraphQL)

### 2.1 Login - Cliente

**Request:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Cliente1",
    "password": "cliente123"
  }'
```

**Respuesta exitosa:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImVhMGJmMzUxLWUxMTUtNDQ0NS1hMGRmLWFmMTBhYmUwZjVlOCIsInVzZXJuYW1lIjoiQ2xpZW50ZTEiLCJlbWFpbCI6ImNsaWVudGUxQGNsaWVudGUuY29tIiwicm9sZSI6MiwiZXhwIjoxNzcwMjY2NDA3fQ.JcnBmVOlsuer8mE813ClG5dPtwd8cxBoXb8G_QSD7pA",
  "token_type": "bearer"
}
```

---

### 2.2 Login - Admin

**Request:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6ImE0OTY3YTg3LTRhZWMtNGU1Mi1iOTVjLWIyNjI0NTAzYzg4MiIsInVzZXJuYW1lIjoiYWRtaW4iLCJlbWFpbCI6ImFkbWluQHZlbnRhcy5jb20iLCJyb2xlIjoxLCJleHAiOjE3NzAyNjY0ODB9.LJvBITxVB1Y7QbIeWPugU_plw9v9ta5QuufrnKAeeRg",
  "token_type": "bearer"
}
```

---

### 2.3 Guardar Token en Variable

```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "Cliente1", "password": "cliente123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

---

## 3. GraphQL API (Requiere JWT)

**Headers requeridos:**
```
Content-Type: application/json
Authorization: Bearer <TOKEN_JWT>
```

---

### 3.1 Query: Listar Productos

**Request:**
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query { listProducts(limit: 5) { id productName unitCost quantityAvailable stockStatus warehouseLocation } }"
  }'
```

**Respuesta:**
```json
{
  "data": {
    "listProducts": [
      {
        "id": "cef7afb2-27db-434c-8de3-d09ff457c36f",
        "productName": "Nike Air Zoom Pegasus 40",
        "unitCost": "120.00",
        "quantityAvailable": 10,
        "stockStatus": 1,
        "warehouseLocation": "CUENCA-CENTRO"
      },
      {
        "id": "73de65e1-21cd-45a9-b9d3-2c5f4d1f73c0",
        "productName": "Adidas Ultraboost Light",
        "unitCost": "180.00",
        "quantityAvailable": 5,
        "stockStatus": 1,
        "warehouseLocation": "CUENCA-CENTRO"
      },
      {
        "id": "1e0945c1-97a8-4863-876d-28ae083314a2",
        "productName": "Puma Velocity Nitro 2",
        "unitCost": "95.50",
        "quantityAvailable": 20,
        "stockStatus": 1,
        "warehouseLocation": "QUITO-NORTE"
      },
      {
        "id": "3fb823c4-3c20-440f-922c-36187bb34c66",
        "productName": "Calcetines Nike Crew (Pack x3)",
        "unitCost": "15.00",
        "quantityAvailable": 50,
        "stockStatus": 1,
        "warehouseLocation": "CUENCA-CENTRO"
      }
    ]
  }
}
```

---

### 3.2 Query: Chat con el Agente (Primera consulta)

**Request:**
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query Chat($query: String!, $sessionId: String) { semanticSearch(query: $query, sessionId: $sessionId) { answer query error } }",
    "variables": {
      "query": "Quiero zapatos Nike para correr",
      "sessionId": "test-session-001"
    }
  }'
```

**Respuesta:**
```json
{
  "data": {
    "semanticSearch": {
      "answer": "Los **Nike Air Zoom Pegasus 40** son perfectos para correr por **$120.00**. ¿Qué talla buscas?",
      "query": "Quiero zapatos Nike para correr",
      "error": null
    }
  }
}
```

---

### 3.3 Query: Chat (Manteniendo Contexto - Segunda consulta)

**Request:**
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query { semanticSearch(query: \"Quiero Nike\", sessionId: \"s-123\") { answer } }"
  }'
```

**Respuesta:**
```json
{
  "data": {
    "semanticSearch": {
      "answer": "¡Excelente elección! Tenemos las **Nike Air Zoom Pegasus 40** y los **Calcetines Nike Crew (Pack x3)**. ¿Cuál te interesa más?"
    }
  }
}
```

---

### 3.4 Query: Chat (Contexto de Precios - Tercera consulta)

**Request:**
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query { semanticSearch(query: \"Cuanto cuestan?\", sessionId: \"s-123\") { answer } }"
  }'
```

**Respuesta (mantiene contexto de Nike):**
```json
{
  "data": {
    "semanticSearch": {
      "answer": "Las **Nike Air Zoom Pegasus 40** cuestan **$120.00**. Los **Calcetines Nike Crew (Pack x3)**, **$15.00**. ¿Qué te parece?"
    }
  }
}
```

---

## 4. REST API - Rate Limiting

### 4.1 Ver Limites

**Request:**
```bash
curl http://localhost:8000/auth/rate-limit-status
```

**Respuesta:**
```json
{
  "login_limit": "5 requests per minute",
  "graphql_limit": "30 requests per minute",
  "health_limit": "100 requests per minute"
}
```

---

## 5. Script de Prueba Automatico

```bash
#!/bin/bash

echo "========================================="
echo "  TESTING COMPLETO API - AGENTE VENTAS"
echo "========================================="
echo ""

# 1. LOGIN
echo "1. LOGIN como Cliente1"
echo "----------------------"
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "Cliente1", "password": "cliente123"}' \
  | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "ERROR: No se pudo obtener token"
    exit 1
fi

echo "Token obtenido: ${TOKEN:0:50}..."
echo ""

# 2. LISTAR PRODUCTOS
echo "2. LISTAR PRODUCTOS (con auth)"
echo "-------------------------------"
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "query { listProducts(limit: 3) { productName unitCost } }"}' \
  | jq
echo ""

# 3. CHAT - Primera consulta
echo "3. CHAT - Primera consulta"
echo "--------------------------"
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query { semanticSearch(query: \"Quiero Nike\", sessionId: \"demo-001\") { answer } }"
  }' \
  | jq
echo ""

# 4. CHAT - Segunda consulta (contexto)
echo "4. CHAT - Segunda consulta (con contexto)"
echo "-----------------------------------------"
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query { semanticSearch(query: \"Cuanto cuestan?\", sessionId: \"demo-001\") { answer } }"
  }' \
  | jq
echo ""

# 5. RATE LIMIT
echo "5. RATE LIMIT STATUS"
echo "--------------------"
curl -s http://localhost:8000/auth/rate-limit-status | jq
echo ""

echo "========================================="
echo "  TODOS LOS TESTS COMPLETADOS"
echo "========================================="
```

---

## 6. Errores Comunes

### Error sin autenticacion

**Request:**
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { listProducts(limit: 3) { productName } }"}'
```

**Comportamiento:** Retorna lista vacia o error en logs.

**Solucion:** Agregar header `Authorization: Bearer $TOKEN`

---

### Error de login

**Causa:** Usuario o password incorrectos.

**Verificar usuarios disponibles:**
```bash
uv run python -c "
import asyncio
import os
os.environ['PG_URL'] = 'postgresql+asyncpg://postgres:postgres@localhost:5433/app_db'
from backend.database.session import get_session
from backend.database.models.user_model import User
from sqlalchemy import select

async def check():
    async with get_session() as s:
        users = (await s.execute(select(User))).scalars().all()
        for u in users:
            print(f'- {u.username} (role={u.role})')

asyncio.run(check())
"
```

---

## 7. Endpoints Disponibles

| Endpoint | Metodo | Auth | Descripcion |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/auth/login` | POST | No | Obtener token JWT |
| `/auth/rate-limit-status` | GET | No | Ver rate limits |
| `/graphql` - `listProducts` | POST | **Si** | Listar productos |
| `/graphql` - `semanticSearch` | POST | **Si** | Chat con agente |

---

## 8. Usuarios de Prueba

| Username | Password | Rol |
|----------|----------|-----|
| Cliente1 | cliente123 | Cliente (2) |
| admin | admin123 | Admin (1) |

---

## 9. Productos Disponibles

| Producto | Precio | Stock | Ubicacion |
|----------|--------|-------|-----------|
| Nike Air Zoom Pegasus 40 | $120.00 | 10 | CUENCA-CENTRO |
| Adidas Ultraboost Light | $180.00 | 5 | CUENCA-CENTRO |
| Puma Velocity Nitro 2 | $95.50 | 20 | QUITO-NORTE |
| Calcetines Nike Crew (Pack x3) | $15.00 | 50 | CUENCA-CENTRO |

---

Documento version 2.1 - 2026-02-03
