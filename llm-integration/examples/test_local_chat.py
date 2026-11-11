import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request
from unittest.mock import patch

from local_chat import LocalBackendError, LocalChatClient, _RejectRedirects


class FakeTransport:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def __call__(self, endpoint, payload, timeout):
        self.calls.append((endpoint, payload, timeout))
        if self.error is not None:
            raise self.error
        return self.response


class LocalChatTests(unittest.TestCase):
    def test_ollama_format_and_response(self):
        transport = FakeTransport(
            {"done": True, "message": {"content": "respuesta sintética"}}
        )
        client = LocalChatClient(
            "http://127.0.0.1:11434/api/chat",
            "modelo-local",
            transport=transport,
        )

        text = client.chat([{"role": "user", "content": "mensaje sintético"}])

        self.assertEqual(text, "respuesta sintética")
        endpoint, payload, timeout = transport.calls[0]
        self.assertEqual(endpoint, "http://127.0.0.1:11434/api/chat")
        self.assertEqual(payload["model"], "modelo-local")
        self.assertFalse(payload["stream"])
        self.assertEqual(timeout, 30)

    def test_openai_compatible_response(self):
        transport = FakeTransport(
            {"choices": [{"message": {"content": "respuesta sintética"}}]}
        )
        client = LocalChatClient(
            "http://localhost:1234/v1/chat/completions",
            "modelo-local",
            api="openai-compatible",
            transport=transport,
        )

        self.assertEqual(
            client.chat([{"role": "user", "content": "consulta"}]),
            "respuesta sintética",
        )

    def test_rejects_non_local_endpoint_before_transport(self):
        with self.assertRaises(ValueError):
            LocalChatClient("https://example.com/chat", "modelo")

    def test_rejects_oversized_request_before_transport(self):
        transport = FakeTransport({"done": True, "message": {"content": "ok"}})
        client = LocalChatClient(
            "http://localhost:11434/api/chat",
            "modelo-local",
            max_request_bytes=10,
            transport=transport,
        )

        with self.assertRaises(LocalBackendError):
            client.chat([{"role": "user", "content": "mensaje largo"}])
        self.assertEqual(transport.calls, [])

    def test_rejects_oversized_response_with_bounded_read(self):
        class FakeResponse:
            def __init__(self):
                self.requested_bytes = None

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc_value, traceback):
                return False

            def read(self, size):
                self.requested_bytes = size
                return b"x" * size

        class FakeOpener:
            def __init__(self, response):
                self.response = response

            def open(self, request, timeout):
                return self.response

        response = FakeResponse()
        client = LocalChatClient(
            "http://localhost:11434/api/chat",
            "modelo-local",
            max_response_bytes=16,
        )

        with patch("local_chat.build_opener", return_value=FakeOpener(response)):
            with self.assertRaisesRegex(LocalBackendError, "respuesta"):
                client.chat([{"role": "user", "content": "consulta"}])

        self.assertEqual(response.requested_bytes, 17)

    def test_invalid_response_is_not_treated_as_success(self):
        client = LocalChatClient(
            "http://localhost:11434/api/chat",
            "modelo-local",
            transport=FakeTransport({"done": False, "message": {"content": "x"}}),
        )

        with self.assertRaises(LocalBackendError):
            client.chat([{"role": "user", "content": "consulta"}])

    def test_transport_error_is_normalized(self):
        client = LocalChatClient(
            "http://localhost:11434/api/chat",
            "modelo-local",
            transport=FakeTransport(error=URLError("apagado")),
        )

        with self.assertRaisesRegex(LocalBackendError, "No se pudo conectar"):
            client.chat([{"role": "user", "content": "consulta"}])

    def test_timeout_wrapped_by_url_error_is_reported_as_timeout(self):
        client = LocalChatClient(
            "http://localhost:11434/api/chat",
            "modelo-local",
            transport=FakeTransport(error=URLError(TimeoutError("timeout"))),
        )

        with self.assertRaisesRegex(LocalBackendError, "Timeout"):
            client.chat([{"role": "user", "content": "consulta"}])

    def test_redirect_handler_rejects_redirect(self):
        request = Request("http://localhost:11434/api/chat")

        with self.assertRaises(HTTPError):
            _RejectRedirects().redirect_request(
                request,
                None,
                302,
                "Found",
                None,
                "http://example.com/chat",
            )


if __name__ == "__main__":
    unittest.main()
