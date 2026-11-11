# Arquitectura de generación modular

## 1. Contexto

Una aplicación puede ofrecer una respuesta generada por un backend reemplazable
y conservar un resultado determinista cuando ese backend informa un fallo
esperado. La orquestación no debería conocer los detalles de transporte de cada
proveedor.

## 2. Problema

Si la lógica de negocio construye peticiones específicas del proveedor y también
interpreta sus fallos, cambiar de backend suele propagar cambios por varias
partes del sistema y dificulta probar el comportamiento sin red.

Este caso presenta ese desafío como un ejemplo general; no atribuye un incidente
histórico ni una métrica que no pueda verificarse públicamente.

## 3. Análisis

El diseño separa cuatro responsabilidades: el contrato de solicitud/resultado,
la orquestación, el backend sustituible y la política de recuperación. Esto
permite probar el flujo sin inicializar un modelo ni abrir una conexión. El caso
no afirma cuál fue el primer incidente histórico que motivó este tipo de diseño.

## 4. Alternativas

- Acoplar la orquestación a una implementación concreta: menos abstracción
  inicial, pero pruebas y sustitución de proveedor más difíciles.
- Definir una interfaz pequeña y pasar el backend como dependencia: permite
  sustituirlo por un doble de prueba y mantiene el flujo principal independiente.
- Tratar cualquier excepción como un error del backend: oculta defectos de
  programación; el ejemplo limita el fallback a un error esperado y tipado.

## 5. Implementación

El archivo [generation_pipeline.py](./examples/generation_pipeline.py) define
solicitud, resultado, protocolo de backend y orquestador. El fallback es una
dependencia explícita. El contenido y la configuración del servicio quedan
fuera del pipeline.

## 6. Validación

Las pruebas [test_generation_pipeline.py](./examples/test_generation_pipeline.py)
cubren la ruta normal, el fallback ante un error de backend conocido, respuestas
vacías o de tipo incorrecto y la propagación de errores inesperados. Se ejecutan
con `unittest` y no requieren dependencias externas. Resultado local:
**6 pruebas aprobadas**.

## 7. Aprendizajes

- Aplicar inversión de dependencias con una interfaz mínima.
- Mantener explícitos el origen del resultado y el límite de recuperación.
- Probar políticas de orquestación sin inicializar un modelo ni abrir una
  conexión.
