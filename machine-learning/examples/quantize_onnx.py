"""Cuantiza un modelo ONNX y publica solo una salida validada."""

import argparse
import hashlib
import os
from pathlib import Path
import tempfile


def quantize_model(source: Path, destination: Path) -> dict[str, object]:
    try:
        import onnx
        from onnxruntime.quantization import QuantType, quantize_dynamic
    except ImportError as error:
        raise RuntimeError(
            "Instalá las dependencias de machine-learning/requirements.txt."
        ) from error

    source = Path(source).resolve()
    destination = Path(destination).resolve()
    if not source.is_file():
        raise FileNotFoundError("No existe el modelo de entrada.")
    if source == destination:
        raise ValueError("El destino no puede sobrescribir la entrada")
    if not destination.parent.is_dir():
        raise FileNotFoundError("El directorio de destino debe existir")

    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".onnx",
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        quantize_dynamic(
            str(source),
            str(temporary),
            weight_type=QuantType.QUInt8,
            per_channel=True,
        )
        onnx.checker.check_model(str(temporary))
        hasher = hashlib.sha256()
        with temporary.open("rb") as model_file:
            for block in iter(lambda: model_file.read(1024 * 1024), b""):
                hasher.update(block)
        digest = hasher.hexdigest()
        size = temporary.stat().st_size
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)

    return {
        "destination": destination.name,
        "sha256": digest,
        "bytes": size,
        "weight_type": "QUInt8",
        "per_channel": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    result = quantize_model(arguments.source, arguments.destination)
    print(f"Modelo cuantizado: {result['destination']}")
    print(f"SHA-256: {result['sha256']}")
    print(f"Tamaño: {result['bytes']} bytes")


if __name__ == "__main__":
    main()
