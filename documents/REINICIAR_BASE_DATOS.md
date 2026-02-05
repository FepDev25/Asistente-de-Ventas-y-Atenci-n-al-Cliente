# Guía: Reiniciar Base de Datos con Nuevos Campos

> **Actualizado para:** Sistema con Barcodes, Descuentos y Promociones

---

## 🚀 Método Rápido (Script Automático)

Ejecuta el script actualizado:

```bash
./reset_database.sh
```

Este script hará todo automáticamente:
1. Detiene y elimina contenedores
2. Elimina el volumen de datos
3. Crea nuevos contenedores
4. Ejecuta el script de inicialización con **barcodes y descuentos**
5. Carga el catálogo completo de productos

---

## 📊 Nuevos Campos en la Base de Datos

### Tabla `product_stocks`

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `barcode` | VARCHAR(100) | Código de barras EAN/UPC (único) |
| `brand` | VARCHAR(100) | Marca (Nike, Adidas, Puma, etc.) |
| `category` | VARCHAR(100) | Categoría (running, lifestyle, training) |
| `original_price` | NUMERIC(12,2) | Precio antes del descuento |
| `discount_percent` | NUMERIC(5,2) | % de descuento (ej: 15.00) |
| `discount_amount` | NUMERIC(12,2) | Monto fijo de descuento |
| `promotion_code` | VARCHAR(50) | Código de promoción |
| `promotion_description` | TEXT | Descripción de la promo |
| `promotion_valid_until` | DATE | Fecha de expiración |
| `is_on_sale` | BOOLEAN | ¿Está en oferta? |

---

## 📝 Método Manual (Paso a Paso)

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

### Paso 3: Iniciar Contenedores Nuevos
```bash
docker-compose up -d
```

### Paso 4: Esperar a PostgreSQL
```bash
# Verificar que esté listo
docker exec sales_agent_db pg_isready -U postgres

# Si dice "accepting connections", continuar
# Si no, esperar unos segundos:
sleep 5
```

### Paso 5: Ejecutar Scripts de Inicialización
```bash
# Script principal (con barcodes y descuentos)
python init.db.py

# Cargar catálogo completo
python init_db_2.py

# Crear DB de tests (opcional)
python init_test_db.py
```

---

## 🔧 Migración de Base de Datos Existente (Sin Perder Datos)

Si ya tienes datos y no quieres reiniciar todo:

```bash
# Ejecutar script de migración
python migrate_db_add_barcode_discounts.py
```

Este script:
- Agrega las nuevas columnas sin borrar datos existentes
- Asigna códigos de barras a productos existentes
- Configura algunas promociones de ejemplo
- Mantiene todos tus datos actuales

---

## 🔍 Verificar la Nueva Estructura

### Verificar Tablas
```bash
# Entrar al contenedor de PostgreSQL
docker exec -it sales_agent_db psql -U postgres -d app_db

# Listar tablas
\dt

# Ver estructura de product_stocks
\d product_stocks

# Ver productos con barcodes
SELECT product_name, barcode, brand, category, is_on_sale, discount_percent
FROM product_stocks
LIMIT 10;

# Ver productos en oferta
SELECT product_name, barcode, unit_cost, discount_percent, promotion_description
FROM product_stocks
WHERE is_on_sale = true;

# Salir
\q
```

### Verificar desde el Backend
```bash
# Iniciar el servidor
python backend/main.py

# En otra terminal, hacer una query GraphQL:
curl -X POST http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TU_TOKEN" \
  -d '{
    "query": "{ listProducts(limit: 5) { productName barcode brand category isOnSale discountPercent finalPrice } }"
  }'
```

---

## 🧪 Probar el Nuevo Sistema

### 1. Login y obtener token
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "Cliente1",
    "password": "cliente123"
  }'
```

### 2. Procesar guion del Agente 2
```graphql
mutation {
  procesarGuionAgente2(guion: {
    sessionId: "test-001"
    productos: [
      {
        codigoBarras: "7501234567890"
        nombreDetectado: "Nike Air Zoom Pegasus 40"
        marca: "Nike"
        categoria: "running"
        prioridad: "alta"
        motivoSeleccion: "Mencionado por usuario"
      }
    ]
    preferencias: {
      estiloComunicacion: "cuencano"
      presupuestoMaximo: 150
      buscaOfertas: true
    }
    contexto: {
      tipoEntrada: "texto"
      intencionPrincipal: "comparar"
      necesitaRecomendacion: true
    }
    textoOriginalUsuario: "Busco zapatillas Nike"
    resumenAnalisis: "Test"
    confianzaProcesamiento: 0.9
  }) {
    success
    productos {
      productName
      barcode
      finalPrice
      isOnSale
      recommendationScore
    }
    mejorOpcionId
    reasoning
  }
}
```

---

## 🛟 Solución de Problemas

### Error: "column does not exist"
```bash
# Si te falta alguna columna, ejecuta la migración:
python migrate_db_add_barcode_discounts.py
```

### Error: "duplicate key value violates unique constraint"
```bash
# Si hay conflictos con barcodes, reinicia completamente:
./reset_database.sh
```

### Error: "relation already exists"
```bash
# Eliminar tablas manualmente:
docker exec -it sales_agent_db psql -U postgres -d app_db -c "
DROP TABLE IF EXISTS order_details CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS product_stocks CASCADE;
DROP TABLE IF EXISTS users CASCADE;
"
```

---

## 📋 Checklist Post-Reinicio

- [ ] Contenedores corriendo: `docker-compose ps`
- [ ] Tablas creadas con nuevos campos
- [ ] Productos con barcodes cargados
- [ ] Algunos productos tienen `is_on_sale = true`
- [ ] Servidor inicia sin errores: `python backend/main.py`
- [ ] Login funciona: POST /auth/login
- [ ] Query de productos muestra barcodes: GraphQL listProducts
- [ ] Procesar guion funciona: mutation procesarGuionAgente2

---

## 🎯 Estructura de Datos Final

```
product_stocks
├── id (UUID, PK)
├── product_id (VARCHAR)
├── product_name (VARCHAR)
├── product_sku (VARCHAR)
├── barcode (VARCHAR, UNIQUE) ⭐ NUEVO
├── supplier_id (VARCHAR)
├── supplier_name (VARCHAR)
├── brand (VARCHAR) ⭐ NUEVO
├── category (VARCHAR) ⭐ NUEVO
├── quantity_available (INTEGER)
├── unit_cost (NUMERIC) - Precio original
├── original_price (NUMERIC) ⭐ NUEVO - Precio antes de descuento
├── total_value (NUMERIC)
├── stock_status (SMALLINT)
├── warehouse_location (VARCHAR)
├── shelf_location (TEXT)
├── batch_number (VARCHAR)
├── is_active (BOOLEAN)
├── is_on_sale (BOOLEAN) ⭐ NUEVO
├── discount_percent (NUMERIC) ⭐ NUEVO
├── discount_amount (NUMERIC) ⭐ NUEVO
├── promotion_code (VARCHAR) ⭐ NUEVO
├── promotion_description (TEXT) ⭐ NUEVO
├── promotion_valid_until (DATE) ⭐ NUEVO
└── created_at (TIMESTAMP)
```

---

**¿Listo?** Ejecuta `./reset_database.sh` y empieza con la nueva arquitectura 🚀
