# Mande

## Prueba 1

```json
query {                                                                                                                                                                        
    semanticSearch(query: "Dime los horarios de atencion de sus tiendas locales") {                                                                                                           
      answer                                                                                                                                                                     
      query                                                                                                                                                                      
    }                                                                                                                                                                            
  }   
```

y recibi

```json
{
  "data": {
    "semanticSearch": {
      "answer": "Hola, entiendo que quieres saber los horarios de atención de nuestras tiendas físicas.\n\nComo soy un asistente virtual, no tengo acceso directo a los horarios específicos de cada tienda en tiempo real. Lo más preciso es que consultes nuestra página web oficial en la sección \"Tiendas\" o \"Localizador de Tiendas\". Allí podrás encontrar la información más actualizada, incluyendo direcciones y horarios de cada sucursal.\n\n¿Hay algo más en lo que pueda ayudarte con nuestros productos o quizás tienes alguna pregunta sobre un modelo en particular?",
      "query": "Dime los horarios de atencion de sus tiendas locales"
    }
  }
}
```

## Prueba 2

```json
query {                                                                                                                                                                        
    semanticSearch(query: "Che bro, mostrame algo copado tipo Puma") {                                                                                                           
      answer                                                                                                                                                                     
      query                                                                                                                                                                      
    }                                                                                                                                                                            
  }     
```

y recibi

```json
{
  "data": {
    "semanticSearch": {
      "answer": "¡Qué onda, bro! 👋 Claro que sí, Puma tiene cosas re zarpadas. Si buscas algo *copado* y de alto rendimiento, te tengo que mostrar los **Puma Deviate Nitro 2**.\n\nEstos son una locura, tipo, vienen con tecnología **NITROFOAM™** que te da una amortiguación brutal y un retorno de energía que te hace sentir que volás. ¡Y la placa de fibra de carbono **PWRPLATE** te impulsa como un cohete! 🚀 Son re duraderos, pensados para darle con todo, ya sea que corras maratones o solo quieras algo top para tus entrenos.\n\nLa calidad, che, se siente apenas los agarrás. No son los típicos tenis que se te deshacen a los dos meses. Estos están hechos para aguantar y darte el máximo performance por un buen tiempo.\n\n¿Qué te parece? ¿Para qué tipo de uso los buscás más o menos? Así te doy más detalles y vemos tu talla. 😉",
      "query": "Che bro, mostrame algo copado tipo Puma"
    }
  }
}
```

## Prueba 3

```json
query {                                                                                                                                                                        
    semanticSearch(query: "A que hora abren?") {                                                                                                           
      answer                                                                                                                                                                     
      query                                                                                                                                                                      
    }                                                                                                                                                                            
  }     
```

y recibi

```json
{
  "data": {
    "semanticSearch": {
      "answer": "¡Hola! Abrimos de lunes a sábado de 10:00 a 20:00 y los domingos de 11:00 a 19:00.\n\n¿Hay algún modelo en particular que te interese o buscas algo específico? ¡Estoy aquí para ayudarte a encontrar el calzado perfecto!",
      "query": "A que hora abren?"
    }
  }
}
```
