import unittest

from generation_pipeline import (
    BackendError,
    GenerationPipeline,
    GenerationRequest,
)


class StubBackend:
    def __init__(self, result=None, error=None):
        self.result = result
        self.error = error
        self.calls = []

    def generate(self, request):
        self.calls.append(request)
        if self.error is not None:
            raise self.error
        return self.result


class GenerationPipelineTests(unittest.TestCase):
    def test_returns_backend_result(self):
        request = GenerationRequest("mensaje sintético")
        backend = StubBackend(result="respuesta sintética")

        result = GenerationPipeline(backend, "respuesta de respaldo").generate(
            request
        )

        self.assertEqual(result.text, "respuesta sintética")
        self.assertEqual(result.origin, "backend")
        self.assertEqual(backend.calls, [request])

    def test_uses_fallback_for_expected_backend_error(self):
        backend = StubBackend(error=BackendError("servicio no disponible"))

        result = GenerationPipeline(backend, "respuesta de respaldo").generate(
            GenerationRequest("mensaje sintético")
        )

        self.assertEqual(result.text, "respuesta de respaldo")
        self.assertEqual(result.origin, "fallback")

    def test_uses_fallback_for_empty_backend_response(self):
        backend = StubBackend(result=" ")

        result = GenerationPipeline(backend, "respuesta de respaldo").generate(
            GenerationRequest("mensaje sintético")
        )

        self.assertEqual(result.text, "respuesta de respaldo")
        self.assertEqual(result.origin, "fallback")

    def test_uses_fallback_for_non_string_backend_response(self):
        backend = StubBackend(result=42)

        result = GenerationPipeline(backend, "respuesta de respaldo").generate(
            GenerationRequest("mensaje sintético")
        )

        self.assertEqual(result.text, "respuesta de respaldo")
        self.assertEqual(result.origin, "fallback")

    def test_unexpected_error_is_not_hidden_by_fallback(self):
        backend = StubBackend(error=RuntimeError("defecto de programación"))

        with self.assertRaisesRegex(RuntimeError, "defecto de programación"):
            GenerationPipeline(backend, "respuesta de respaldo").generate(
                GenerationRequest("mensaje sintético")
            )

    def test_rejects_empty_message(self):
        with self.assertRaises(ValueError):
            GenerationPipeline(StubBackend(result="ok"), "respaldo").generate(
                GenerationRequest(" ")
            )


if __name__ == "__main__":
    unittest.main()
