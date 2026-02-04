# Guia de Testing Completo del Sistema

Documento para probar todos los endpoints del backend paso a paso.

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

### 1.2 Instalar herramientas necesarias

```bash
# Opcion A: curl (ya viene en la mayoria de sistemas)

# Opcion B: httpie (mas amigable)
pip install httpie

# Opcion C: Postman/Insomnia (GUI)
```

---

## 2. GraphQL - Queries y Mutations

### 2.1 URL Base

```
POST http://localhost:8000/graphql
Content-Type: application/json
```

---

### 2.2 Query: Chat con el Agente (Alex)

**Request:**
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
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
      "answer": "¡Claro! Encontré estos Nike para correr...",
      "query": "Quiero zapatos Nike para correr",
      "error": null
    }
  }
}
```

**Probar mantenimiento de contexto:**
```bash
# Segundo mensaje (misma sesion)
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{
    "query": "query Chat($query: String!, $sessionId: String) { semanticSearch(query: $query, sessionId: $sessionId) { answer error } }",
    "variables": {
      "query": "¿Cuánto cuestan?",
      "sessionId": "test-session-001"
    }
  }'
# El agente deberia recordar que hablamos de zapatos Nike
```

---

### 2.3 Query: Listar Productos

**Request:**
```bash
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
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
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "productName": "Nike Air Max 90",
        "unitCost": 129.99,
        "quantityAvailable": 15,
        "stockStatus": 1,
        "warehouseLocation": "CUENCA-CENTRO"
      }
    ]
  }
}
```

---

## 3. REST API - Autenticacion

### 3.1 Login con Usuario Existente

Si usaste `init.db.py`, tienes estos usuarios por defecto:

| Username | Password | Rol |
|----------|----------|-----|
| admin | admin123 | Admin (1) |
| cliente1 | cliente123 | Cliente (2) |
| cliente2 | cliente123 | Cliente (2) |

**Request:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cliente1",
    "password": "cliente123"
  }'
```

**Respuesta:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Guardar token en variable (bash):**
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "cliente1", "password": "cliente123"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

---

### 3.2 Ver Informacion del Usuario (/auth/me)

**Request:**
```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

**Respuesta:**
```json
{
  "user_id": "d47a4417-7c5d-44e9-853d-27eb98fad5c6",
  "username": "cliente1",
  "email": "cliente1@example.com",
  "role": "client",
  "role_id": 2,
  "is_active": true
}
```

---

### 3.3 Login Fallido (Prueba de Error)

**Request:**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "usuario_invalido",
    "password": "password_incorrecto"
  }'
```

**Respuesta (401):**
```json
{
  "detail": "Credenciales invalidas"
}
```

---

### 3.4 Verificar Rate Limiting

**Login (limite: 5/minuto):**
```bash
# Intentar 6 veces rapidamente
for i in {1..6}; do
  curl -X POST http://localhost:8000/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "test", "password": "test"}' \
    -w "\nStatus: %{http_code}\n"
done
# La 6ta deberia retornar 429 (Too Many Requests)
```

**Ver estado del rate limit:**
```bash
curl http://localhost:8000/auth/rate-limit-status
```

---

## 4. Endpoints Protegidos por Rol

### 4.1 Endpoint Publico (Sin token)

```bash
curl http://localhost:8000/auth/public
# Respuesta: {"message": "Endpoint publico - No se requiere autenticacion"}
```

---

### 4.2 Endpoint Basico Protegido (Cualquier rol)

```bash
curl http://localhost:8000/auth/protected-basic \
  -H "Authorization: Bearer $TOKEN"
```

---

### 4.3 Endpoint Solo Admin

**Con admin (debe funcionar):**
```bash
# Login como admin
ADMIN_TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' \
  | jq -r '.access_token')

curl http://localhost:8000/auth/admin-only \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

**Con cliente (debe fallar 403):**
```bash
curl http://localhost:8000/auth/admin-only \
  -H "Authorization: Bearer $TOKEN"
# Respuesta: {"detail": "Permiso denegado: Se requiere rol de administrador"}
```

---

### 4.4 Endpoint Solo Cliente

```bash
curl http://localhost:8000/auth/client-only \
  -H "Authorization: Bearer $TOKEN"
# Debe funcionar con TOKEN de cliente
```

---

## 5. Flujo Completo de Chat con Autenticacion

### Paso 1: Login
```bash
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "cliente1", "password": "cliente123"}' \
  | jq -r '.access_token')
```

### Paso 2: Verificar usuario
```bash
curl http://localhost:8000/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Paso 3: Chat (sin auth en GraphQL actualmente)
```bash
# Nota: El endpoint GraphQL actual no requiere auth
# Pero puedes enviar el user_id si lo necesitas

curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "query Chat($query: String!) { semanticSearch(query: $query) { answer error } }",
    "variables": {"query": "Quiero comprar zapatos"}
  }'
```

---

## 6. Testing con HTTPie (Alternativa a curl)

Si instalaste `httpie`, los comandos son mas limpios:

### Login
```bash
http POST localhost:8000/auth/login \
  username=cliente1 \
  password=cliente123
```

### Guardar token
```bash
http POST localhost:8000/auth/login \
  username=cliente1 \
  password=cliente123 \
  -b | jq -r '.access_token' > /tmp/token.txt

TOKEN=$(cat /tmp/token.txt)
```

### Usar token
```bash
http localhost:8000/auth/me \
  Authorization:"Bearer $TOKEN"
```

### GraphQL
```bash
http POST localhost:8000/graphql \
  query='query { listProducts(limit: 3) { productName unitCost } }'
```

---

## 7. Pruebas de Estres (Opcional)

### Instalar herramienta de benchmarking
```bash
pip install locust
```

### Archivo de prueba: `locustfile.py`
```python
from locust import HttpUser, task, between

class ChatUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        # Login al iniciar
        response = self.client.post("/auth/login", json={
            "username": "cliente1",
            "password": "cliente123"
        })
        self.token = response.json()["access_token"]
    
    @task(3)
    def chat_query(self):
        self.client.post("/graphql", json={
            "query": 'query($q: String!) { semanticSearch(query: $q) { answer } }',
            "variables": {"q": "Quiero zapatos Nike"}
        })
    
    @task(1)
    def list_products(self):
        self.client.post("/graphql", json={
            "query": 'query { listProducts(limit: 10) { productName } }'
        })
```

### Ejecutar
```bash
locust -f locustfile.py --host=http://localhost:8000
# Abrir http://localhost:8089
```

---

## 8. Scripts de Prueba Automatica

### Script bash completo: `test_api.sh`
```bash
#!/bin/bash

BASE_URL="http://localhost:8000"
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "=== Test de API ==="

# 1. Health check
echo -n "Health check: "
if curl -s ${BASE_URL}/health > /dev/null; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    exit 1
fi

# 2. Login
echo -n "Login: "
TOKEN=$(curl -s -X POST ${BASE_URL}/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "cliente1", "password": "cliente123"}' \
  | jq -r '.access_token')

if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    exit 1
fi

# 3. Get me
echo -n "Get user info: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/auth/me \
  -H "Authorization: Bearer $TOKEN")

if [ "$STATUS" == "200" ]; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL (status $STATUS)${NC}"
fi

# 4. GraphQL - Chat
echo -n "GraphQL Chat: "
RESPONSE=$(curl -s -X POST ${BASE_URL}/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { semanticSearch(query: \"hola\") { answer } }"}')

if echo "$RESPONSE" | grep -q "answer"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
    echo "$RESPONSE"
fi

# 5. GraphQL - Products
echo -n "GraphQL Products: "
RESPONSE=$(curl -s -X POST ${BASE_URL}/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "query { listProducts(limit: 3) { id productName } }"}')

if echo "$RESPONSE" | grep -q "listProducts"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${RED}FAIL${NC}"
fi

echo "=== Tests completados ==="
```

### Hacer ejecutable y correr
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## 9. Solucion de Problemas Comunes

### Error: Connection refused
```bash
# Verificar que el servidor este corriendo
curl http://localhost:8000/health

# Si no responde, reiniciar:
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Error: 401 Unauthorized
- Token expirado (dura 24 horas)
- Token mal formado (debe ser "Bearer {token}")
- Endpoint requiere rol especifico

### Error: 429 Too Many Requests
```bash
# Esperar 1 minuto para rate limit de login
# O reiniciar Redis si esta configurado:
redis-cli FLUSHALL
```

### Error: Database connection
```bash
# Verificar PostgreSQL
docker-compose logs postgres

# Resetear base de datos si es necesario:
./reset_database.sh
```

---

## 10. Variables de Entorno para Testing

Crear archivo `.env.test`:
```bash
# Database
PG_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/app_db

# Redis (opcional)
REDIS_HOST=localhost
REDIS_PORT=6379

# Seguridad
SECRET_KEY=test-secret-key
JWT_SECRET=test-secret-key

# Logging
LOG_LEVEL=DEBUG
```

Cargar antes de probar:
```bash
export $(cat .env.test | xargs)
```

---

Documento version 1.0 - 2026-02-03
