"""Pipeline mínimo con backend sustituible y fallback explícito."""

from dataclasses import dataclass
from typing import Protocol


class BackendError(Exception):
    """Fallo esperado al solicitar una generación al backend."""


@dataclass(frozen=True)
class GenerationRequest:
    message: str


@dataclass(frozen=True)
class GenerationResult:
    text: str
    origin: str


class GenerationBackend(Protocol):
    def generate(self, request: GenerationRequest) -> str:
        """Genera texto o lanza BackendError si el servicio falla."""


class GenerationPipeline:
    def __init__(self, backend: GenerationBackend, fallback_text: str):
        if not fallback_text.strip():
            raise ValueError("fallback_text no puede estar vacío")
        self._backend = backend
        self._fallback_text = fallback_text

    def generate(self, request: GenerationRequest) -> GenerationResult:
        if not request.message.strip():
            raise ValueError("message no puede estar vacío")

        try:
            text = self._backend.generate(request)
            if not isinstance(text, str) or not text.strip():
                raise BackendError("El backend produjo una respuesta vacía")
        except BackendError:
            return GenerationResult(self._fallback_text, "fallback")

        return GenerationResult(text, "backend")
