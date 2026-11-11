# Problemas y soluciones de desarrollo

En este repositorio comparto problemas técnicos que encuentro durante el desarrollo de distintos proyectos y las soluciones que implemento para resolverlos.

La idea es mostrar el razonamiento detrás de cada solución, las decisiones técnicas que tomo y las pruebas utilizadas para comprobar su funcionamiento.

Algunos casos nacieron durante el desarrollo de proyectos privados que siguen en curso. Para compartir lo aprendido, presento implementaciones independientes y simplificadas: no publico código fuente privado, datos personales, prompts, arquitecturas completas, credenciales ni configuraciones sensibles.

## Cómo trabajo

1. Identifico un problema concreto y defino qué resultado permitiría comprobar una mejora.
2. Analizo las posibles soluciones y sus limitaciones.
3. Implemento una solución acotada, procurando separar responsabilidades.
4. Pruebo casos normales, errores y condiciones límite.
5. Documento las decisiones técnicas y verifico que los cambios no introduzcan regresiones.

## Casos

| Caso | Problema técnico | Qué demuestra |
|---|---|---|
| [Arquitectura modular](./software-architecture/README.md) | Mantener la orquestación independiente del backend y limitar el fallback a fallos esperados. | Contratos explícitos, inversión de dependencias y pruebas de rutas de error. |
| [Integración de LLM local](./llm-integration/README.md) | Integrar formatos de chat distintos sin enviar peticiones fuera del equipo local. | Adaptación de APIs, validación de payload/respuesta y manejo de errores de transporte. |
| [Preparación de modelos ONNX](./machine-learning/README.md) | Evitar publicar una cuantización incompleta o inválida. | Cuantización dinámica, validación ONNX y reemplazo atómico del artefacto. |
| [Persistencia y gestión de datos con SQLite](./database-persistence/README.md) | Guardar conversaciones y mensajes con relaciones e integridad referencial. | Diseño relacional, consultas SQL, transacciones y persistencia en archivo. |

## Pruebas

Cada caso incluye pruebas automatizadas para verificar su comportamiento, contemplando situaciones normales, entradas inválidas y condiciones límite.

Para ejecutar las pruebas desde la raíz del repositorio:

```powershell
python -m unittest discover -s software-architecture/examples -p "test_*.py"
python -m unittest discover -s llm-integration/examples -p "test_*.py"
python -m unittest discover -s database-persistence -p "test_*.py"
python -m pip install -r machine-learning/requirements.txt
python -m unittest discover -s machine-learning/examples -p "test_*.py"
```

Las suites suman **28 pruebas**. Usan dobles de transporte, un modelo ONNX sintético y una base SQLite temporal; no descargan modelos ni contactan servicios de inferencia.

Los casos de arquitectura, integración y persistencia utilizan únicamente la biblioteca estándar de Python.

## Herramientas y prácticas

Python · SQLite · integración con LLM · Ollama · ONNX Runtime · pruebas automatizadas · diseño modular · validación de datos · manejo de errores · persistencia de información · optimización de modelos.

> Los ejemplos publicados son implementaciones independientes y simplificadas, desarrolladas para este portfolio. Su objetivo es demostrar criterios de diseño, resolución de problemas y validación técnica sin revelar código, datos ni detalles internos de los proyectos privados.