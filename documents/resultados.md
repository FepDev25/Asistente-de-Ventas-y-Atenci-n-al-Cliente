# 📊 Resultados de Testing - API GraphQL

Documento con los resultados de las pruebas realizadas al sistema de Agente 2 → Agente 3.

---

## 🧪 Caso 2.1: Un Solo Producto Detectado

### Query

```graphql
mutation ProcesarGuionUnProducto {
  procesarGuionAgente2(
    guion: {
      sessionId: "test-session-001"
      productos: [
        {
          codigoBarras: "7501234567891"
          nombreDetectado: "Nike Air Max 90"
          prioridad: "alta"
          motivoSeleccion: "Cliente mostró interés en zapatillas clásicas"
        }
      ]
      preferencias: {
        estiloComunicacion: "cuencano"
        presupuestoMaximo: 200
        urgencia: "media"
        usoPrevisto: "Uso casual diario, caminar por la ciudad"
        buscaOfertas: true
      }
      contexto: {
        tipoEntrada: "texto"
        intencionPrincipal: "compra_directa"
        necesitaRecomendacion: true
      }
      textoOriginalUsuario: "Estoy buscando unas zapatillas cómodas para caminar"
      resumenAnalisis: "Usuario busca zapatillas lifestyle para uso casual"
      confianzaProcesamiento: 0.92
    }
  ) {
    success
    mensaje
    productos {
      productName
      finalPrice
      recommendationScore
      reason
    }
    mejorOpcionId
    reasoning
    siguientePaso
  }
}
```

### Respuesta

```json
{
  "data": {
    "procesarGuionAgente2": {
      "success": true,
      "mensaje": "Recomendación generada exitosamente",
      "productos": [
        {
          "productName": "Nike Air Max 90",
          "finalPrice": "104.0000",
          "recommendationScore": 100,
          "reason": "Producto de alta prioridad según tus preferencias; Precio dentro de tu presupuesto ($104.0000); 🎉 En OFERTA: Ahorras $26.00; Promoción: 10% OFF - Clásicos con descuento; Excelente para uso casual diario"
        }
      ],
      "mejorOpcionId": "0a0e097f-29d9-44bd-b439-7731d124e1b0",
      "reasoning": "**🏆 RECOMENDACIÓN: Nike Air Max 90**\n\n💰 **PRECIO ESPECIAL:**\n   Antes: ~~$130.00~~\n   Ahora: **$104.00**\n   ¡Ahorras: $26.00!\n   🎁 10% OFF - Clásicos con descuento\n\n**✅ Por qué es ideal para ti:**\n   • Producto de alta prioridad según tus preferencias\n   • Precio dentro de tu presupuesto ($104.0000)\n   • 🎉 En OFERTA: Ahorras $26.00\n   • Promoción: 10% OFF - Clásicos con descuento\n   • Excelente para uso casual diario\n\n🎯 Este modelo está específicamente diseñado para **Uso casual diario, caminar por la ciudad**.\n⏰ La promoción es por tiempo limitado, ¡aprovecha hoy!",
      "siguientePaso": "confirmar_compra"
    }
  }
}
```

### ✅ Resumen

| Campo | Valor |
|-------|-------|
| Producto | Nike Air Max 90 |
| Precio Original | $130.00 |
| Precio Final | $104.00 |
| Descuento | 10% ($26.00) |
| Score | 100/100 |
| Siguiente Paso | confirmar_compra |

---

## 🧪 Caso 2.2: Múltiples Productos (Comparación)

### Query

```graphql
mutation ProcesarGuionMultiplesProductos {
  procesarGuionAgente2(
    guion: {
      sessionId: "test-session-002"
      productos: [
        {
          codigoBarras: "7501234567891"
          nombreDetectado: "Nike Air Max 90"
          prioridad: "alta"
          motivoSeleccion: "Zapatilla clásica, buen precio"
        }
        {
          codigoBarras: "7501234567895"
          nombreDetectado: "Nike Air Force 1"
          prioridad: "media"
          motivoSeleccion: "Muy popular, estilo icónico"
        }
        {
          codigoBarras: "7501234567894"
          nombreDetectado: "Nike Court Vision Low"
          prioridad: "baja"
          motivoSeleccion: "Alternativa económica con descuento"
        }
      ]
      preferencias: {
        estiloComunicacion: "neutral"
        presupuestoMaximo: 150
        urgencia: "baja"
        usoPrevisto: "Regalo para hermano de 25 años"
        buscaOfertas: true
      }
      contexto: {
        tipoEntrada: "imagen"
        intencionPrincipal: "comparar"
        necesitaRecomendacion: true
      }
      textoOriginalUsuario: "Mostré una foto de zapatillas Nike y necesito ayuda para elegir"
      resumenAnalisis: "Usuario comparando 3 modelos Nike lifestyle para regalo"
      confianzaProcesamiento: 0.88
    }
  ) {
    success
    mensaje
    productos {
      productName
      finalPrice
      recommendationScore
      reason
      isOnSale
      discountPercent
    }
    mejorOpcionId
    reasoning
    siguientePaso
  }
}
```

### Respuesta

```json
{
  "data": {
    "procesarGuionAgente2": {
      "success": true,
      "mensaje": "Recomendación generada exitosamente",
      "productos": [
        {
          "productName": "Nike Air Max 90",
          "finalPrice": "104.0000",
          "recommendationScore": 85,
          "reason": "Producto de alta prioridad según tus preferencias; Precio dentro de tu presupuesto ($104.0000); 🎉 En OFERTA: Ahorras $26.00; Promoción: 10% OFF - Clásicos con descuento",
          "isOnSale": true,
          "discountPercent": "10.00"
        },
        {
          "productName": "Nike Court Vision Low",
          "finalPrice": "45.0000",
          "recommendationScore": 65,
          "reason": "Precio dentro de tu presupuesto ($45.0000); 🎉 En OFERTA: Ahorras $30.00; Promoción: 20% OFF - Oferta especial lifestyle",
          "isOnSale": true,
          "discountPercent": "20.00"
        },
        {
          "productName": "Nike Air Force 1 '07",
          "finalPrice": "110.00",
          "recommendationScore": 55,
          "reason": "Precio dentro de tu presupuesto ($110.00)",
          "isOnSale": false,
          "discountPercent": null
        }
      ],
      "mejorOpcionId": "0a0e097f-29d9-44bd-b439-7731d124e1b0",
      "reasoning": "**🏆 RECOMENDACIÓN: Nike Air Max 90**\n\n💰 **PRECIO ESPECIAL:**\n   Antes: ~~$130.00~~\n   Ahora: **$104.00**\n   ¡Ahorras: $26.00!\n   🎁 10% OFF - Clásicos con descuento\n\n**✅ Por qué es ideal para ti:**\n   • Producto de alta prioridad según tus preferencias\n   • Precio dentro de tu presupuesto ($104.0000)\n   • 🎉 En OFERTA: Ahorras $26.00\n   • Promoción: 10% OFF - Clásicos con descuento\n\n**📊 Comparación con otras opciones:**\n   • vs Nike Court Vision Low:\n     - Inviertes $59.00 más\n     - Vale la diferencia por: Producto de alta prioridad según tus preferencias, Precio dentro de tu presupuesto ($104.0000)\n   • vs Nike Air Force 1 '07:\n     - Ahorras $6.00\n     - 30 puntos mejor según tus preferencias\n\n🎯 Este modelo está específicamente diseñado para **Regalo para hermano de 25 años**.\n⏰ La promoción es por tiempo limitado, ¡aprovecha hoy!",
      "siguientePaso": "confirmar_compra"
    }
  }
}
```

### ✅ Resumen de Comparación

| Producto | Precio | Descuento | Score | En Oferta |
|----------|--------|-----------|-------|-----------|
| 🏆 Nike Air Max 90 | $104.00 | 10% | 85 | ✅ |
| Nike Court Vision Low | $45.00 | 20% | 65 | ✅ |
| Nike Air Force 1 '07 | $110.00 | - | 55 | ❌ |

**Mejor opción:** Nike Air Max 90 (Score: 85)

---

## 🧪 Caso 2.3: Producto con Promoción Activa

### Query

```graphql
mutation ProcesarGuionConPromocion {
  procesarGuionAgente2(
    guion: {
      sessionId: "test-session-003"
      productos: [
        {
          codigoBarras: "8884071234567"
          nombreDetectado: "Calcetines Nike Crew Performance"
          prioridad: "alta"
          motivoSeleccion: "Accesorio complementario"
        }
      ]
      preferencias: {
        estiloComunicacion: "cuencano"
        presupuestoMaximo: 20
        urgencia: "alta"
        usoPrevisto: "Necesito para entrenamiento de mañana"
        buscaOfertas: true
      }
      contexto: {
        tipoEntrada: "texto"
        intencionPrincipal: "compra_directa"
        necesitaRecomendacion: false
      }
      textoOriginalUsuario: "Necesito calcetines para correr urgentemente"
      resumenAnalisis: "Usuario busca calcetines running con urgencia"
      confianzaProcesamiento: 0.95
    }
  ) {
    success
    mensaje
    productos {
      productName
      finalPrice
      unitCost
      isOnSale
      discountPercent
    }
    mejorOpcionId
    reasoning
    siguientePaso
  }
}
```

### Respuesta

```json
{
  "data": {
    "procesarGuionAgente2": {
      "success": true,
      "mensaje": "Recomendación generada exitosamente",
      "productos": [
        {
          "productName": "Calcetines Nike Crew Performance (Pack x3)",
          "finalPrice": "7.5000",
          "unitCost": "15.00",
          "isOnSale": true,
          "discountPercent": "25.00"
        }
      ],
      "mejorOpcionId": "fc441033-917c-47f1-8f70-080b36305b8e",
      "reasoning": "**🏆 RECOMENDACIÓN: Calcetines Nike Crew Performance (Pack x3)**\n\n💰 **PRECIO ESPECIAL:**\n   Antes: ~~$15.00~~\n   Ahora: **$7.50**\n   ¡Ahorras: $7.50!\n   🎁 25% OFF - 2x1 en accesorios\n\n**✅ Por qué es ideal para ti:**\n   • Producto de alta prioridad según tus preferencias\n   • Precio dentro de tu presupuesto ($7.5000)\n   • 🎉 En OFERTA: Ahorras $7.50\n   • Promoción: 25% OFF - 2x1 en accesorios\n\n🎯 Este modelo está específicamente diseñado para **Necesito para entrenamiento de mañana**.\n⏰ La promoción es por tiempo limitado, ¡aprovecha hoy!",
      "siguientePaso": "confirmar_compra"
    }
  }
}
```

### ✅ Resumen

| Campo | Valor |
|-------|-------|
| Producto | Calcetines Nike Crew Performance (Pack x3) |
| Precio Original | $15.00 |
| Precio Final | $7.50 |
| Descuento | 25% ($7.50) |
| Ahorro Total | 50% del precio original |
| Siguiente Paso | confirmar_compra |

---

## 📦 Listado Completo de Productos

### Query

```graphql
query ListarProductos {
  listProducts(limit: 50) {
    id
    productName
    barcode
    brand
    category
    unitCost
    finalPrice
    quantityAvailable
    stockStatus
    isOnSale
    discountPercent
    savingsAmount
    promotionDescription
    warehouseLocation
  }
}
```

### Respuesta

#### 🏃 Running (12 productos)

| # | Producto | Marca | Precio | Final | Desc. | Stock | Bodega |
|---|----------|-------|--------|-------|-------|-------|--------|
| 1 | Nike Air Zoom Pegasus 40 | Nike | $120.00 | $120.00 | - | 15 | Cuenca |
| 2 | Nike React Infinity Run 4 | Nike | $145.00 | $145.00 | - | 12 | Cuenca |
| 3 | Nike ZoomX Vaporfly 3 | Nike | $250.00 | $250.00 | - | 8 | Cuenca |
| 4 | Nike Revolution 7 | Nike | $65.00 | $45.50 | 15% | 30 | Quito |
| 5 | Nike Downshifter 12 | Nike | $70.00 | $70.00 | - | 28 | Cuenca |
| 6 | Adidas Ultraboost Light | Adidas | $180.00 | $180.00 | - | 18 | Cuenca |
| 7 | Adidas Supernova 3 | Adidas | $110.00 | $70.40 | 18% | 22 | Cuenca |
| 8 | Adidas Duramo SL | Adidas | $60.00 | $36.00 | 20% | 25 | Cuenca |
| 9 | Puma Velocity Nitro 2 | Puma | $95.00 | $76.00 | 10% | 20 | Quito |
| 10 | Puma Deviate Nitro Elite 2 | Puma | $220.00 | $220.00 | - | 7 | Cuenca |
| 11 | New Balance Fresh Foam X 1080v13 | New Balance | $160.00 | $128.00 | 10% | 14 | Cuenca |
| 12 | New Balance FuelCell SuperComp Elite v4 | New Balance | $275.00 | $275.00 | - | 5 | Cuenca |

#### 👟 Lifestyle (13 productos)

| # | Producto | Marca | Precio | Final | Desc. | Stock | Bodega |
|---|----------|-------|--------|-------|-------|-------|--------|
| 1 | Nike Air Max 90 | Nike | $130.00 | $104.00 | 10% | 20 | Cuenca |
| 2 | Nike Court Vision Low | Nike | $75.00 | $45.00 | 20% | 25 | Quito |
| 3 | Nike Air Force 1 '07 | Nike | $110.00 | $110.00 | - | 35 | Quito |
| 4 | Nike Blazer Mid '77 | Nike | $105.00 | $79.80 | 12% | 18 | Quito |
| 5 | Adidas Stan Smith | Adidas | $85.00 | $85.00 | - | 40 | Quito |
| 6 | Adidas Samba OG | Adidas | $100.00 | $100.00 | - | 35 | Quito |
| 7 | Adidas Forum Low | Adidas | $95.00 | $66.50 | 15% | 20 | Quito |
| 8 | Adidas Gazelle | Adidas | $90.00 | $90.00 | - | 30 | Quito |
| 9 | Puma Suede Classic XXI | Puma | $70.00 | $49.00 | 15% | 32 | Quito |
| 10 | Puma RS-X Efekt | Puma | $115.00 | $115.00 | - | 15 | Cuenca |
| 11 | Puma Caven 2.0 | Puma | $65.00 | $49.40 | 12% | 28 | Quito |
| 12 | New Balance 574 Core | New Balance | $80.00 | $80.00 | - | 45 | Quito |
| 13 | New Balance 327 | New Balance | $95.00 | $66.50 | 15% | 38 | Quito |

#### 🎯 Otras Categorías (7 productos)

| # | Producto | Marca | Categoría | Precio | Final | Desc. | Stock |
|---|----------|-------|-----------|--------|-------|-------|-------|
| 1 | Nike Metcon 9 | Nike | Training | $140.00 | $140.00 | - | 10 |
| 2 | Adidas Terrex Swift R3 GTX | Adidas | Outdoor | $160.00 | $128.00 | 10% | 12 |
| 3 | Puma Clyde All-Pro | Puma | Basketball | $125.00 | $125.00 | - | 14 |
| 4 | Calcetines Nike Crew Performance | Nike | Accesorios | $15.00 | $7.50 | 25% | 60 |
| 5 | Plantillas Ortopédicas Dr. Scholl's | Dr. Scholl's | Accesorios | $25.00 | $25.00 | - | 40 |
| 6 | Spray Impermeabilizante Crep Protect | Crep Protect | Accesorios | $18.00 | $14.40 | 10% | 50 |
| 7 | Cordones de Repuesto Premium | Generic | Accesorios | $8.00 | $8.00 | - | 80 |

---

## 📈 Estadísticas del Catálogo

| Métrica | Valor |
|---------|-------|
| **Total Productos** | 32 |
| **Productos en Oferta** | 15 |
| **Marcas** | 5 (Nike, Adidas, Puma, New Balance, Genéricos) |
| **Categorías** | 6 (Running, Lifestyle, Training, Outdoor, Basketball, Accesorios) |

### Ofertas por Marca

| Marca | Productos en Oferta |
|-------|---------------------|
| Nike | 5 |
| Adidas | 4 |
| Puma | 3 |
| New Balance | 2 |
| Otros | 1 |

### Mejores Descuentos

| Producto | Descuento | Ahorro |
|----------|-----------|--------|
| Calcetines Nike Crew | 25% | $7.50 |
| Nike Court Vision Low | 20% | $30.00 |
| Adidas Duramo SL | 20% | $24.00 |
| Adidas Supernova 3 | 18% | $39.60 |

---

*Documento generado: Febrero 2026*
