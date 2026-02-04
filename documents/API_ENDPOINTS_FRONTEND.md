# API Endpoints Disponibles - Frontend

---

## 1. GraphQL API

**URL Base:** `POST /graphql`

**Headers requeridos:**
```
Content-Type: application/json
```

**Headers opcionales (para endpoints protegidos):**
```
Authorization: Bearer <JWT_TOKEN>
```

---

### 1.1 Chat con el Agente (Alex)

**Query:** `semanticSearch`

**Descripcion:** Endpoint principal para el chat. El usuario envia una consulta y recibe una respuesta del agente de ventas.

**Variables:**
- `query` (String, requerido): Mensaje del usuario
- `sessionId` (String, opcional): ID de sesion para mantener contexto entre mensajes

**Ejemplo de request:**
```json
{
  "query": "
    query Chat($query: String!, $sessionId: String) {
      semanticSearch(query: $query, sessionId: $sessionId) {
        answer
        query
        error
      }
    }
  ",
  "variables": {
    "query": "Quiero zapatos Nike para correr",
    "sessionId": "sesion-usuario-123"
  }
}
```

**Ejemplo de respuesta exitosa:**
```json
{
  "data": {
    "semanticSearch": {
      "answer": "Encontré estos Nike para correr...",
      "query": "Quiero zapatos Nike para correr",
      "error": null
    }
  }
}
```

**Ejemplo de respuesta con error:**
```json
{
  "data": {
    "semanticSearch": {
      "answer": "Lo siento, estoy teniendo problemas para responder...",
      "query": "Quiero zapatos Nike para correr",
      "error": "timeout"
    }
  }
}
```

**Valores posibles de error:**
- `null`: Sin error, respuesta exitosa
- `timeout`: El servicio tardo mas de 30 segundos
- `service_unavailable`: Base de datos o servicio no disponible
- `internal_error`: Error tecnico general

**Notas:**
- Guardar el `sessionId` en localStorage para mantener el contexto de la conversacion
- Si no se envia `sessionId`, cada mensaje se trata como conversacion independiente
- Rate limit: 30 peticiones por minuto por IP

---

### 1.2 Listar Productos (Catalogo)

**Query:** `listProducts`

**Descripcion:** Obtiene la lista de productos disponibles en inventario.

**Variables:**
- `limit` (Int, opcional): Cantidad maxima de productos a retornar (default: 20)

**Ejemplo de request:**
```json
{
  "query": "
    query {
      listProducts(limit: 10) {
        id
        productName
        unitCost
        quantityAvailable
        stockStatus
        warehouseLocation
        shelfLocation
        batchNumber
      }
    }
  "
}
```

**Ejemplo de respuesta:**
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
        "warehouseLocation": "CUENCA-CENTRO",
        "shelfLocation": "Pasillo 3, Estante B",
        "batchNumber": "NIKE-2026-A"
      }
    ]
  }
}
```

**Campos de respuesta:**
- `id`: UUID del producto
- `productName`: Nombre del producto
- `unitCost`: Precio unitario
- `quantityAvailable`: Cantidad en stock
- `stockStatus`: 1 = Disponible, 0 = Agotado
- `warehouseLocation`: Ubicacion del almacen
- `shelfLocation`: Ubicacion en estante (o descripcion)
- `batchNumber`: Numero de lote (o keywords)

**Notas:**
- Si hay error en la base de datos, retorna lista vacia (no lanza error)
- Rate limit: 30 peticiones por minuto por IP

---

## 2. REST API - Autenticacion

**URL Base:** `/auth`

---

### 2.1 Login

**Endpoint:** `POST /auth/login`

**Descripcion:** Inicia sesion con username o email y password. Retorna un token JWT.

**Rate limit:** 5 intentos por minuto (proteccion contra fuerza bruta)

**Body:**
```json
{
  "username": "usuario123",
  "email": "usuario@example.com",
  "password": "contraseñaSegura123"
}
```

Nota: Debe enviar `username` O `email`, no ambos obligatoriamente.

**Respuesta exitosa (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Respuesta error (401):**
```json
{
  "detail": "Credenciales invalidas"
}
```

**Respuesta error (400):**
```json
{
  "detail": "Se requiere 'username' o 'email' junto con 'password'"
}
```

**Respuesta error (429 - Rate limit):**
```json
{
  "detail": "Rate limit exceeded: 5 per 1 minute"
}
```

---

### 2.2 Estado de Rate Limiting

**Endpoint:** `GET /auth/rate-limit-status`

**Descripcion:** Verifica el estado actual de los limites de peticiones.

**Headers requeridos:**
```
X-Forwarded-For: <IP del cliente> (opcional, para debugging)
```

**Respuesta:**
```json
{
  "limit": "30/minute",
  "remaining": 25,
  "reset": 45
}
```

---

## 3. REST API - Endpoints Protegidos (Requieren JWT)

Todos estos endpoints requieren el header:
```
Authorization: Bearer <JWT_TOKEN>
```

---

### 3.1 Informacion Publica

**Endpoint:** `GET /auth/public`

**Descripcion:** Endpoint de prueba, no requiere autenticacion.

**Respuesta:**
```json
{
  "message": "Endpoint publico - No se requiere autenticacion"
}
```

---

### 3.2 Recurso Basico Protegido

**Endpoint:** `GET /auth/protected-basic`

**Descripcion:** Cualquier usuario autenticado puede acceder.

**Respuesta exitosa:**
```json
{
  "message": "Acceso concedido",
  "user_id": "uuid-del-usuario",
  "role": "client"
}
```

**Respuesta error (401):**
```json
{
  "detail": "Token no proporcionado o invalido"
}
```

---

### 3.3 Recurso Solo Admin

**Endpoint:** `GET /auth/admin-only`

**Descripcion:** Solo usuarios con rol de administrador (role=1).

**Respuesta exitosa (solo admin):**
```json
{
  "message": "Bienvenido administrador",
  "admin_id": "uuid-del-admin"
}
```

**Respuesta error (403):**
```json
{
  "detail": "Permiso denegado: Se requiere rol de administrador"
}
```

---

### 3.4 Recurso Solo Cliente

**Endpoint:** `GET /auth/client-only`

**Descripcion:** Solo usuarios con rol de cliente (role=2).

**Respuesta exitosa:**
```json
{
  "message": "Bienvenido cliente",
  "client_id": "uuid-del-cliente"
}
```

**Respuesta error (403):**
```json
{
  "detail": "Permiso denegado: Se requiere rol de cliente"
}
```

---

### 3.5 Informacion del Usuario Actual

**Endpoint:** `GET /auth/me`

**Descripcion:** Obtiene la informacion completa del usuario autenticado.

**Respuesta:**
```json
{
  "user_id": "uuid-del-usuario",
  "username": "usuario123",
  "email": "usuario@example.com",
  "role": "client",
  "role_id": 2,
  "is_active": true
}
```

---

## 4. Flujo de Autenticacion Completo

### Paso 1: Login
```javascript
const response = await fetch('/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    username: 'usuario123',
    password: 'contraseñaSegura123'
  })
});

const { access_token } = await response.json();
localStorage.setItem('token', access_token);
```

### Paso 2: Usar token en peticiones protegidas
```javascript
const token = localStorage.getItem('token');

const response = await fetch('/auth/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});
```

### Paso 3: Manejar expiracion (401)
```javascript
if (response.status === 401) {
  localStorage.removeItem('token');
  window.location.href = '/login';
}
```

---

## 5. Codigos de Rol

| Rol | ID | Descripcion |
|-----|-----|-------------|
| Admin | 1 | Administrador del sistema |
| Client | 2 | Cliente regular |
| Guest | 3 | Usuario no autenticado (solo endpoints publicos) |

---

## 6. Errores Comunes

### 401 Unauthorized
- Token no proporcionado
- Token expirado
- Token invalido o mal formado

### 403 Forbidden
- Token valido pero sin permisos para el recurso
- Usuario con rol incorrecto

### 429 Too Many Requests
- Se excedio el rate limit
- Reintentar despues del tiempo indicado

### 500 Internal Server Error
- Error en el servidor
- Contactar al equipo de backend

---

## 7. Endpoints Pendientes (En desarrollo)

Los siguientes endpoints estan planificados pero aun no implementados:

### Checkout / Pedidos
- `POST /api/orders` - Crear nuevo pedido
- `GET /api/orders` - Listar pedidos del usuario
- `GET /api/orders/{id}` - Obtener detalle de un pedido
- `PUT /api/orders/{id}/cancel` - Cancelar pedido

### Reconocimiento de Imagenes (Agente 2)
- `POST /api/recognize` - Subir imagen para reconocimiento de producto

### Historial de Conversaciones
- `GET /api/chat/history` - Obtener historial de chat del usuario

---

## 8. URLs de Desarrollo

| Entorno | URL Base |
|---------|----------|
| Local | `http://localhost:8000` |
| GraphQL Endpoint | `http://localhost:8000/graphql` |

---
