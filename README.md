# Dev Problem Solving

Portfolio de ingeniería de software con casos técnicos reconstruidos desde cero
y datos sintéticos. La documentación está en español; los nombres de archivos
y directorios, en inglés. No son módulos extraídos de proyectos privados.

Cada caso explica el problema, el análisis, las alternativas, la implementación
y la validación. Los ejemplos no requieren servicios remotos ni datos de
usuarios.

## Casos

| Caso | Problema técnico | Qué demuestra |
|---|---|---|
| [Arquitectura modular](./software-architecture/README.md) | Mantener la orquestación independiente del backend y limitar el fallback a fallos esperados. | Contratos explícitos, inversión de dependencias y pruebas de rutas de error. |
| [Integración de LLM local](./llm-integration/README.md) | Integrar formatos de chat distintos sin enviar peticiones fuera del equipo local. | Adaptación de APIs, validación de payload/respuesta y manejo de errores de transporte. |
| [Preparación de modelos ONNX](./machine-learning/README.md) | Evitar publicar una cuantización incompleta o inválida. | Cuantización dinámica, validación ONNX y reemplazo atómico del artefacto. |

No se incluyen casos de limpieza de datasets ni fine-tuning: la auditoría no
encontró evidencia suficiente para describirlos sin inventar resultados.

## Requisitos

- Python 3.10 o posterior para los casos de arquitectura e integración local.
- Las dependencias ONNX específicas del caso de Machine Learning, indicadas en
  [requirements.txt](./machine-learning/requirements.txt).

## Ejecutar las pruebas

Desde la raíz del repositorio:

```powershell
python -m unittest discover -s software-architecture/examples -p "test_*.py"
python -m unittest discover -s llm-integration/examples -p "test_*.py"
python -m pip install -r machine-learning/requirements.txt
python -m unittest discover -s machine-learning/examples -p "test_*.py"
```

Las suites suman **17 pruebas**. Usan dobles de transporte y un modelo ONNX
sintético; no descargan modelos ni contactan servicios de inferencia. Las
pruebas de arquitectura e integración usan solo la biblioteca estándar.

## Alcance y privacidad

Los ejemplos son implementaciones nuevas de patrones generales. No contienen
prompts, conversaciones, identificadores de modelos privados, credenciales,
rutas locales ni artefactos de modelos.
