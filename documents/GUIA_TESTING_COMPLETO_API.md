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

### 2.1 Login y Obtencion de Token

**Usuarios disponibles por defecto:**

| Username | Password | Rol |
|----------|----------|-----|
| admin | admin123 | Admin (1) |
| Cliente1 | cliente123 | Cliente (2) |

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
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Guardar token en variable (bash):**
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "Cliente1", "password": "cliente123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

---

## 3. GraphQL API (Requiere JWT)

### 3.1 URL Base y Headers

```
POST http://localhost:8000/graphql
Content-Type: application/json
Authorization: Bearer <TOKEN_JWT>
```

---

### 3.2 Query: Listar Productos (Requiere Auth)

**Request:**
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query { listProducts(limit: 5) { id productName unitCost quantityAvailable stockStatus warehouseLocation } }"
  }'
```

**Respuesta exitosa:**
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
      }
    ]
  }
}
```

**Error sin token:**
```json
{
  "data": {
    "listProducts": []
  }
}
```
(Nota: actualmente retorna lista vacia si no hay auth, o puedes ver en logs)

---

### 3.3 Query: Chat con el Agente (Requiere Auth)

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

**Respuesta exitosa:**
```json
{
  "data": {
    "semanticSearch": {
      "answer": "Excelente eleccion! Tenemos los Nike Air Zoom Pegasus 40 por $120.00...",
      "query": "Quiero zapatos Nike para correr",
      "error": null
    }
  }
}
```

**Error sin token:**
```json
{
  "data": {
    "semanticSearch": {
      "answer": "Debes iniciar sesion para usar el chat.",
      "query": "Quiero zapatos Nike para correr",
      "error": "unauthorized"
    }
  }
}
```

---

### 3.4 Probar Contexto de Sesion (Mismo sessionId)

```bash
# Primer mensaje
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query { semanticSearch(query: \"Quiero Nike\", sessionId: \"s-123\") { answer } }"
  }'

# Segundo mensaje (deberia recordar el contexto)
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query { semanticSearch(query: \"Cuanto cuestan?\", sessionId: \"s-123\") { answer } }"
  }'
```

---

## 4. REST API - Endpoints de Autenticacion

### 4.1 Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 4.2 Rate Limit Status

```bash
curl http://localhost:8000/auth/rate-limit-status
```

---

## 5. Flujo Completo de Prueba

### Script completo de prueba:

```bash
#!/bin/bash

echo "=== 1. LOGIN ==="
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

echo "=== 2. LISTAR PRODUCTOS (con auth) ==="
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "query { listProducts(limit: 3) { productName unitCost } }"}' \
  | jq
echo ""

echo "=== 3. CHAT (con auth) ==="
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query { semanticSearch(query: \"Hola\", sessionId: \"test-001\") { answer error } }"
  }' \
  | jq
echo ""

echo "=== 4. CHAT SIN AUTH (debe fallar) ==="
curl -s -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query { semanticSearch(query: \"Hola\") { answer error } }"
  }' \
  | jq
echo ""

echo "=== Tests completados ==="
```

---

## 6. Errores Comunes

### Error: "Debes iniciar sesion para usar el chat"

**Causa:** No se envio el header Authorization o el token es invalido.

**Solucion:**
```bash
# Verificar que el token no este vacio
echo $TOKEN

# Verificar formato del header
-H "Authorization: Bearer $TOKEN"
```

### Error: "Credenciales invalidas"

**Causa:** Usuario o password incorrectos.

**Solucion:** Verificar usuarios en BD:
```bash
# Listar usuarios disponibles
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

### Error: "Connection refused"

**Causa:** Backend no esta corriendo.

**Solucion:**
```bash
uv run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 7. Testing con Postman/Insomnia

### Configuracion:

1. **Crear Environment:**
   - Variable: `base_url` = `http://localhost:8000`
   - Variable: `token` = (se autoguarda despues del login)

2. **Request: Login**
   - POST: `{{base_url}}/auth/login`
   - Body: `{"username": "Cliente1", "password": "cliente123"}`
   - Tests: Guardar token en variable de entorno

3. **Request: List Products**
   - POST: `{{base_url}}/graphql`
   - Header: `Authorization: Bearer {{token}}`
   - Body GraphQL:
     ```graphql
     query {
       listProducts(limit: 5) {
         id
         productName
         unitCost
       }
     }
     ```

4. **Request: Chat**
   - POST: `{{base_url}}/graphql`
   - Header: `Authorization: Bearer {{token}}`
   - Body GraphQL:
     ```graphql
     query Chat($query: String!) {
       semanticSearch(query: $query, sessionId: "s-001") {
         answer
         error
       }
     }
     ```
   - Variables: `{"query": "Quiero zapatos Nike"}`

---

## 8. Endpoints Disponibles

| Endpoint | Metodo | Auth | Descripcion |
|----------|--------|------|-------------|
| `/health` | GET | No | Health check |
| `/auth/login` | POST | No | Obtener token JWT |
| `/auth/rate-limit-status` | GET | No | Ver rate limits |
| `/graphql` - `listProducts` | POST | **Si** | Listar productos |
| `/graphql` - `semanticSearch` | POST | **Si** | Chat con agente |

---

## 9. Variables de Entorno

Archivo `.env` para testing:
```bash
PG_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/app_db
REDIS_HOST=localhost
REDIS_PORT=6379
SECRET_KEY=test-secret-key
JWT_SECRET=test-secret-key
LOG_LEVEL=DEBUG
```

---

Documento version 2.0 - 2026-02-03
