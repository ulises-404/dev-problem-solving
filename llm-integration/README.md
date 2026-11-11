# Integración de LLM local

## 1. Contexto

Los servidores de inferencia locales pueden exponer formatos HTTP distintos,
aunque ambos acepten una secuencia de mensajes y devuelvan texto.

## 2. Problema

Una integración frágil puede construir payloads incompatibles, seguir una
redirección fuera del equipo local o dejar que errores de transporte se
confundan con respuestas válidas. Además, un límite de tamaño del cuerpo HTTP
no equivale al límite de tokens del modelo.

## 3. Análisis

El ejemplo distingue dos formatos de respuesta, valida contenido y restringe
el endpoint a loopback. Los dobles de transporte permiten probar esas rutas sin
red. No se midieron latencia ni calidad de generación.

## 4. Alternativas

- Un único formato fijo: menos código, pero no interoperable con otras APIs
  locales.
- Adaptadores pequeños detrás de un cliente común: preservan una interfaz
  estable y localizan las diferencias de payload y respuesta.
- Aceptar cualquier URL HTTP: permite despliegues remotos, pero no cumple el
  alcance local y amplía el riesgo de envío accidental de datos.

## 5. Implementación

[local_chat.py](./examples/local_chat.py) usa la biblioteca estándar para
construir el subconjunto de payload común a dos APIs locales y adaptar la
validación de sus respuestas. También exige una dirección loopback, desactiva
proxies y redirecciones en el transporte HTTP y limita el tamaño de la petición.
También lee como máximo un byte más que `max_response_bytes` (por defecto,
1.000.000) antes de rechazar una respuesta sobredimensionada. El límite de
petición se configura por separado mediante `max_request_bytes`. El transporte
se puede inyectar para probarlo sin red.

Los límites de bytes protegen los cuerpos HTTP; no estiman tokens. Una aplicación
real debe aplicar además el límite de contexto específico del modelo. El ejemplo
no incluye prompts, credenciales ni contenido de conversación.

## 6. Validación

[test_local_chat.py](./examples/test_local_chat.py) cubre los dos formatos,
endpoints no locales, respuestas inválidas, límites de tamaño de petición y
respuesta, y errores de transporte, incluido un timeout encapsulado por la
biblioteca HTTP. La prueba de respuesta grande verifica que la lectura se limita
a `max_response_bytes + 1`. Todos los casos usan dobles locales y no se conectan
a un servidor. Resultado local: **9 pruebas aprobadas**.

## 7. Aprendizajes

- Aislar diferencias de proveedor en adaptadores comprobables.
- Fallar explícitamente ante endpoints, payloads o respuestas inválidas.
- No confundir límites de bytes, tokens y ventana de contexto.
- Mantener pruebas de integración deterministas mediante inyección del
  transporte.
