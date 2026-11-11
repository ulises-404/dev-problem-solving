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

- **[Diseño de una arquitectura modular](software-architecture/README.md)**  
  Separación de responsabilidades, manejo de errores y mecanismos de fallback en un flujo de generación.

- **[Integración con modelos de lenguaje locales](llm-integration/README.md)**  
  Comunicación HTTP, validación de solicitudes y respuestas, y control de límites para evitar consumos inesperados.

- **[Optimización de modelos de machine learning](machine-learning/README.md)**  
  Cuantización dinámica de modelos ONNX, validación de resultados y publicación segura de artefactos.

## Pruebas

Cada caso incluye pruebas automatizadas para verificar su comportamiento, contemplando situaciones normales, entradas inválidas y condiciones límite.

Para ejecutar las pruebas desde la raíz del repositorio:

```bash
python -m unittest discover -s software-architecture/examples
python -m unittest discover -s llm-integration/examples
python -m unittest discover -s machine-learning/examples
```

El módulo de machine learning requiere instalar las dependencias indicadas en su archivo `requirements.txt`.

## Herramientas y prácticas

Python · integración con LLM · Ollama · ONNX Runtime · pruebas automatizadas · diseño modular · validación de datos · manejo de errores · optimización de modelos.

> Los ejemplos publicados son implementaciones independientes y simplificadas, desarrolladas para este portfolio. Su objetivo es demostrar criterios de diseño, resolución de problemas y validación técnica sin revelar código, datos ni detalles internos de los proyectos privados.
