# Guía: Reiniciar Base de Datos desde Cero

Esta guía te ayuda a reiniciar PostgreSQL con las nuevas tablas `orders` y `order_details`.

---

## 🚀 Método Rápido (Script Automático)

Ejecuta el script proporcionado:

```bash
./reset_database.sh
```

Esto hará todo automáticamente:
1. Detiene y elimina contenedores
2. Elimina el volumen de datos
3. Crea nuevos contenedores
4. Ejecuta el script de inicialización

---

## 📝 Método Manual (Paso a Paso)

Si prefieres hacerlo manualmente o el script falla:

### Paso 1: Detener Contenedores
```bash
cd "/home/felipep/Documentos/universidad/universidad 7mo/aprendizaje automatico/practica 4"
docker-compose down
```

### Paso 2: Eliminar Volumen de Datos
```bash
# Ver volumenes existentes
docker volume ls

# Eliminar el volumen específico
docker volume rm practica-4_postgres_data

# Si dice que está en uso, forzar:
docker volume rm -f practica-4_postgres_data
```

### Paso 3: Verificar Eliminación
```bash
# No debería aparecer el volumen
docker volume ls | grep postgres
```

### Paso 4: Iniciar Contenedores Nuevos
```bash
docker-compose up -d
```

### Paso 5: Esperar a PostgreSQL
```bash
# Verificar que esté listo
docker exec sales_agent_db pg_isready -U postgres

# Si dice "accepting connections", continuar
# Si no, esperar unos segundos:
sleep 5
```

### Paso 6: Ejecutar Script de Inicialización
```bash
python init.db.py
```

Deberías ver algo como:
```
Iniciando configuración de Base de Datos...
Creando tablas en Postgres...
✓ Tablas creadas: users, product_stocks, orders, order_details
Base de datos vacía. Insertando inventario inicial...
Inventario cargado exitosamente.
Insertando usuarios iniciales...
Usuarios creados exitosamente.
📦 Tabla 'orders': 0 pedidos existentes
📋 Tabla 'order_details': 0 líneas de detalle existentes

✅ Base de datos inicializada correctamente.
```

---

## 🔍 Verificar que Todo Funciona

### Verificar Tablas
```bash
# Entrar al contenedor de PostgreSQL
docker exec -it sales_agent_db psql -U postgres -d app_db

# Listar tablas
\dt

# Ver estructura de orders
\d orders

# Ver estructura de order_details
\d order_details

# Salir
\q
```

### Verificar Contenedores
```bash
# Ver estado
docker-compose ps

# Debería mostrar:
# sales_agent_db    running
# sales_agent_redis running
```

---

## 🧪 Probar con un Pedido de Ejemplo

Una vez reiniciada, puedes probar creando un pedido:

```bash
# Iniciar el servidor
python backend/main.py
```

Y en otra terminal:
```bash
# Login para obtener token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "Cliente1", "password": "cliente123"}'

# Luego hacer un query de checkout (usa el token obtenido)
```

O usa el playground GraphQL en `http://localhost:8000/graphql`

---

## 🛟 Solución de Problemas

### Error: "volume is in use"
```bash
# Forzar eliminación
docker-compose down -v  # Elimina contenedores y volúmenes
```

### Error: "permission denied"
```bash
# Dar permisos al script
chmod +x reset_database.sh
```

### Error: "database app_db does not exist"
```bash
# Crear manualmente
docker exec -it sales_agent_db psql -U postgres -c "CREATE DATABASE app_db;"
```

### Error: "relation already exists"
```bash
# Si las tablas ya existen, eliminarlas primero:
docker exec -it sales_agent_db psql -U postgres -d app_db -c "
DROP TABLE IF EXISTS order_details CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS product_stocks CASCADE;
DROP TABLE IF EXISTS users CASCADE;
"
```

### Puerto 5433 ya en uso
```bash
# Ver qué usa el puerto
sudo lsof -i :5433

# O cambiar el puerto en docker-compose.yml
# Cambia "5433:5432" por "5434:5432" o similar
```

---

## 📊 Estructura de Tablas Creadas

```sql
-- users (existente)
-- product_stocks (existente)

-- orders (NUEVA)
- id: UUID PK
- user_id: UUID FK -> users
- status: VARCHAR (DRAFT, CONFIRMED, PAID, etc.)
- subtotal, tax_amount, shipping_cost, discount_amount, total_amount: DECIMAL
- shipping_address, shipping_city, shipping_state, shipping_country: TEXT/VARCHAR
- contact_name, contact_phone, contact_email: VARCHAR
- payment_method, payment_status: VARCHAR
- notes, internal_notes: TEXT
- session_id: VARCHAR
- created_at, updated_at: TIMESTAMP

-- order_details (NUEVA)
- id: UUID PK
- order_id: UUID FK -> orders
- product_id: UUID FK -> product_stocks
- product_name, product_sku: VARCHAR (congelado al momento de compra)
- quantity: INTEGER
- unit_price, discount_amount: DECIMAL
- created_at: TIMESTAMP
```

---

## ✅ Checklist Post-Reinicio

- [ ] Contenedores corriendo: `docker-compose ps`
- [ ] Tablas creadas: `docker exec sales_agent_db psql -U postgres -d app_db -c "\dt"`
- [ ] Datos iniciales: productos y usuarios
- [ ] Servidor inicia sin errores: `python backend/main.py`
- [ ] Login funciona: POST /auth/login
- [ ] GraphQL responde: GET /graphql

---

**¿Listo?** Ejecuta `./reset_database.sh` y empieza de cero 🚀
