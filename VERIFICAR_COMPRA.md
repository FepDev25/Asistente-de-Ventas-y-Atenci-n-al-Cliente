# 🔍 Cómo Verificar si una Compra se Completó

## ⚠️ PROBLEMA ACTUAL DETECTADO

**Tu compra NO se completó** porque el sistema tiene un bug:
- El `user_id` NO se está pasando al CheckoutAgent
- Sin `user_id`, el checkout no puede crear órdenes
- El sistema entra en loop infinito de transferencias

**Evidencia en los logs:**
```
WARNING | backend.agents.checkout_agent:_process_payment:289 - Checkout sin user_id autenticado
```

---

## 📊 Comandos de Verificación

### 1. Ver Última Orden Creada
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db -c "
SELECT 
    id,
    user_id,
    total_amount,
    status,
    shipping_address,
    created_at
FROM orders 
ORDER BY created_at DESC 
LIMIT 1;
"
```

**Qué verificar:**
- `created_at`: Si la fecha es de hace segundos/minutos, es tu compra
- `status`: Debería estar en `CONFIRMED` o `PAID`
- `total_amount`: Debería coincidir con el precio del producto

---

### 2. Ver Últimas 5 Órdenes con Items
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db -c "
SELECT 
    o.id,
    u.username,
    o.total_amount,
    o.status,
    COUNT(od.id) as items,
    o.created_at
FROM orders o
JOIN users u ON o.user_id = u.id
LEFT JOIN order_details od ON od.order_id = o.id
GROUP BY o.id, u.username, o.total_amount, o.status, o.created_at
ORDER BY o.created_at DESC
LIMIT 5;
"
```

**Qué verificar:**
- `items`: Debe ser > 0 (si es 0, la orden está incompleta)
- `username`: Debería ser tu usuario (Cliente1, admin, etc.)

---

### 3. Ver Detalles de la Última Orden
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db -c "
SELECT 
    od.order_id,
    od.product_name,
    od.quantity,
    od.unit_price,
    od.subtotal,
    od.created_at
FROM order_details od
ORDER BY od.created_at DESC
LIMIT 5;
"
```

**Qué verificar:**
- `product_name`: El producto que compraste
- `quantity`: Cantidad comprada
- `subtotal`: Precio total (quantity × unit_price)

---

### 4. Verificar Reducción de Inventario
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db -c "
SELECT 
    product_name,
    quantity_available,
    product_id
FROM product_stocks 
WHERE product_name LIKE '%Nike Air Zoom%';
"
```

**Qué verificar:**
- Antes de comprar: 10 unidades
- Después de comprar 1: 9 unidades
- Después de comprar 2: 8 unidades

**IMPORTANTE**: Si el número NO cambió, la compra NO se completó.

---

### 5. Ver Total de Órdenes por Usuario
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db -c "
SELECT 
    u.username,
    COUNT(o.id) as total_ordenes,
    SUM(o.total_amount) as total_gastado
FROM users u
LEFT JOIN orders o ON o.user_id = u.id
GROUP BY u.username
ORDER BY total_gastado DESC NULLS LAST;
"
```

**Qué verificar:**
- Tu `total_ordenes` aumentó en 1
- Tu `total_gastado` aumentó en el precio del producto

---

### 6. Ver Órdenes de HOY
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db -c "
SELECT 
    o.id,
    u.username,
    o.total_amount,
    o.status,
    o.created_at AT TIME ZONE 'America/Guayaquil' as fecha_ecuador
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.created_at > CURRENT_DATE
ORDER BY o.created_at DESC;
"
```

---

### 7. Buscar Órdenes de los Últimos 10 Minutos
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db -c "
SELECT 
    o.id,
    u.username,
    o.total_amount,
    o.status,
    o.created_at,
    NOW() - o.created_at as hace_cuanto
FROM orders o
JOIN users u ON o.user_id = u.id
WHERE o.created_at > NOW() - INTERVAL '10 minutes'
ORDER BY o.created_at DESC;
"
```

---

## 🐛 Cómo Saber si la Compra Falló

**Señales de FALLO:**
1. ❌ No aparece orden nueva en últimos 10 minutos
2. ❌ El inventario NO se redujo
3. ❌ Logs muestran: `WARNING | Checkout sin user_id autenticado`
4. ❌ Logs muestran: `max_transfers_reached`
5. ❌ Loop infinito: `checkout->sales->checkout->sales`

**Señales de ÉXITO:**
1. ✅ Aparece orden nueva con tu username
2. ✅ La orden tiene `items > 0`
3. ✅ El inventario se redujo
4. ✅ Logs muestran: `Orden creada exitosamente`
5. ✅ Frontend muestra mensaje: "Pedido confirmado #UUID"

---

## 🛠️ Solución Temporal (Para Probar Compras)

**Hasta que se arregle el bug del `user_id`**, puedes:

### Opción 1: Crear órdenes manualmente en BD
```bash
docker exec -it sales_agent_db psql -U postgres -d app_db
```

Luego ejecuta:
```sql
-- Obtener tu user_id
SELECT id, username FROM users WHERE username = 'Cliente1';

-- Obtener un producto
SELECT id, product_name, unit_cost FROM product_stocks LIMIT 1;

-- Crear orden (reemplaza los UUIDs con los valores reales)
INSERT INTO orders (user_id, total_amount, status, shipping_address)
VALUES (
    'TU_USER_ID_AQUI',
    120.00,
    'CONFIRMED',
    'Av. Loja 123, Cuenca, Ecuador'
)
RETURNING id;

-- Crear detalle (usa el order_id devuelto arriba)
INSERT INTO order_details (order_id, product_id, product_name, product_sku, quantity, unit_price)
VALUES (
    'ORDER_ID_AQUI',
    'PRODUCTO_ID_AQUI',
    'Nike Air Zoom Pegasus 40',
    'NIKE-001',
    1,
    120.00
);

-- Reducir inventario
UPDATE product_stocks 
SET quantity_available = quantity_available - 1
WHERE id = 'PRODUCTO_ID_AQUI';
```

### Opción 2: Usar el script create_test_orders.py
```bash
python create_test_orders.py
```
Esto crea 15 órdenes aleatorias con items y reduce inventario automáticamente.

---

## 📝 Ejemplo de Verificación Completa

Después de intentar una compra:

```bash
# 1. ¿Se creó orden nueva?
docker exec -it sales_agent_db psql -U postgres -d app_db -c "
SELECT COUNT(*) as total FROM orders WHERE created_at > NOW() - INTERVAL '5 minutes';
"

# 2. ¿Se redujo inventario del producto comprado?
docker exec -it sales_agent_db psql -U postgres -d app_db -c "
SELECT product_name, quantity_available FROM product_stocks 
WHERE product_name = 'Nike Air Zoom Pegasus 40';
"

# 3. Ver detalles de la última orden
docker exec -it sales_agent_db psql -U postgres -d app_db -c "
SELECT o.*, u.username FROM orders o 
JOIN users u ON o.user_id = u.id 
ORDER BY o.created_at DESC LIMIT 1;
"
```

---

## 🔧 El Bug Debe Ser Corregido

**El problema está en:** `backend/api/graphql/queries.py` línea ~138

**Falta pasar:**
```python
result = await search_service.semantic_search(
    query, 
    session_id=session_id,
    user_id=user.get('id')  # ← ESTO FALTA
)
```

Y luego propagar `user_id` por:
- `SearchService.semantic_search()`
- `AgentOrchestrator.process_query()`
- `AgentState.user_id`

**Mientras no se arregle**, las compras desde el frontend NO funcionarán.
