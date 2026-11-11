# Preparación reproducible de modelos ONNX

## 1. Contexto

Un modelo ONNX se puede cuantizar para reducir el coste de inferencia en CPU.
La salida debe validarse antes de reemplazar un artefacto existente.

## 2. Problema

Una descarga incompleta, una cuantización interrumpida o una salida ONNX
inválida no deberían dejar publicada una versión parcial ni destruir la última
versión válida.

## 3. Análisis

La salida se escribe primero en un temporal, se valida con ONNX y solo entonces
reemplaza el destino. Así, un fallo durante la cuantización no publica un
artefacto parcial. El caso usa un grafo sintético para probar la propiedad sin
incluir pesos ni datos de inferencia.

## 4. Alternativas

- Sobrescribir el destino durante la conversión: simple, pero puede perder el
  artefacto válido si el proceso falla.
- Preparar en un temporal del mismo directorio, validar y reemplazar al final:
  mantiene el destino previo hasta completar el proceso.
- Cuantizar sin verificar la salida: reduce pasos, pero deja fallos de formato
  para el runtime consumidor.

## 5. Implementación

[quantize_onnx.py](./examples/quantize_onnx.py) utiliza ONNX Runtime para
cuantización dinámica de pesos a `QUInt8`, comprueba el archivo con ONNX y
publica el resultado mediante reemplazo atómico. La ubicación temporal se crea
junto al destino para evitar mover el archivo entre sistemas de archivos.

Las dependencias están fijadas en
[requirements.txt](./requirements.txt). Para usar el script con un modelo real:

```powershell
python -m pip install -r machine-learning/requirements.txt
python machine-learning/examples/quantize_onnx.py input.onnx output.onnx
```

El caso no incluye un modelo de muestra. La prueba genera un grafo sintético
localmente y no descarga artefactos.

El script identifica la salida mediante SHA-256, pero no verifica la
procedencia del modelo de entrada. Antes de usar un modelo real, quien lo ejecute
debe validar su origen y su hash por un canal de confianza.

## 6. Validación

[test_quantize_onnx.py](./examples/test_quantize_onnx.py) verifica la
cuantización de un grafo pequeño y que un fallo de conversión conserve el
destino anterior, que la salida puede ejecutarse en CPU con una tolerancia
numérica explícita y que no queden temporales al fallar. Resultado local:
**2 pruebas aprobadas**. No se reportan mejoras de velocidad, memoria o calidad:
no se hizo un benchmark en este portfolio. ONNX Runtime emitió su aviso de que
el preprocesamiento puede ser conveniente; el ejemplo no lo automatiza porque
depende del modelo.

## 7. Aprendizajes

- Validar las salidas y fijar dependencias antes de distribuir herramientas de ML.
- Separar preparación temporal, validación y publicación.
- Usar pruebas sintéticas para comprobar propiedades de formato y fallo seguro.
- No presentar cuantización como fine-tuning ni como una métrica de rendimiento.
