"""Cliente pequeño para APIs de chat locales compatibles con JSON."""

import json
import socket
from http.client import HTTPException
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import (
    HTTPRedirectHandler,
    ProxyHandler,
    Request,
    build_opener,
)


class LocalBackendError(Exception):
    """Error de configuración, transporte o respuesta del backend."""


class _RejectRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, file, code, message, headers, new_url):
        raise HTTPError(
            request.full_url, code, "Redirecciones desactivadas", headers, file
        )


def _validate_endpoint(endpoint: str) -> None:
    if not isinstance(endpoint, str) or not endpoint.strip():
        raise ValueError("endpoint debe ser una URL no vacía")
    parsed = urlparse(endpoint)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("endpoint debe ser una URL HTTP completa")
    if parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
        raise ValueError("endpoint debe apuntar al equipo local")
    if parsed.username or parsed.password:
        raise ValueError("No se permiten credenciales en la URL")


def _post_json(
    endpoint: str,
    payload: dict,
    timeout: float,
    max_response_bytes: int,
) -> dict:
    request = Request(
        endpoint,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    opener = build_opener(ProxyHandler({}), _RejectRedirects())
    with opener.open(request, timeout=timeout) as response:
        body = response.read(max_response_bytes + 1)
        if len(body) > max_response_bytes:
            raise LocalBackendError("La respuesta excede el límite de bytes.")
        return json.loads(body)


class LocalChatClient:
    def __init__(
        self,
        endpoint: str,
        model: str,
        *,
        api: str = "ollama",
        timeout: float = 30,
        max_request_bytes: int = 256_000,
        max_response_bytes: int = 1_000_000,
        transport: Callable[[str, dict, float], dict] | None = None,
    ):
        _validate_endpoint(endpoint)
        if not isinstance(model, str) or not model.strip():
            raise ValueError("model debe ser un identificador no vacío")
        if api not in ("ollama", "openai-compatible"):
            raise ValueError("api debe ser ollama u openai-compatible")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
            raise ValueError("timeout debe ser numérico")
        if timeout <= 0:
            raise ValueError("timeout debe ser mayor que cero")
        if type(max_request_bytes) is not int or max_request_bytes <= 0:
            raise ValueError("max_request_bytes debe ser un entero positivo")
        if type(max_response_bytes) is not int or max_response_bytes <= 0:
            raise ValueError("max_response_bytes debe ser un entero positivo")
        if transport is not None and not callable(transport):
            raise TypeError("transport debe ser callable")

        self._endpoint = endpoint
        self._model = model
        self._api = api
        self._timeout = timeout
        self._max_request_bytes = max_request_bytes
        self._max_response_bytes = max_response_bytes
        self._transport = transport

    def chat(self, messages: list[dict[str, str]]) -> str:
        normalized = self._validate_messages(messages)
        payload = self._build_payload(normalized)
        body_size = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        if body_size > self._max_request_bytes:
            raise LocalBackendError("La petición excede el límite de bytes.")

        try:
            if self._transport is None:
                response = _post_json(
                    self._endpoint,
                    payload,
                    self._timeout,
                    self._max_response_bytes,
                )
            else:
                response = self._transport(
                    self._endpoint, payload, self._timeout
                )
        except HTTPError as error:
            raise LocalBackendError(
                f"El backend respondió HTTP {error.code}."
            ) from error
        except (TimeoutError, socket.timeout) as error:
            raise LocalBackendError("Timeout al consultar el backend local.") from error
        except URLError as error:
            if isinstance(error.reason, (TimeoutError, socket.timeout)):
                raise LocalBackendError(
                    "Timeout al consultar el backend local."
                ) from error
            raise LocalBackendError(
                "No se pudo conectar con el backend local."
            ) from error
        except HTTPException as error:
            raise LocalBackendError(
                "Falló la comunicación con el backend local."
            ) from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise LocalBackendError(
                "El backend local devolvió JSON inválido."
            ) from error

        return self._parse_response(response)

    def _validate_messages(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        if not isinstance(messages, list) or not messages:
            raise ValueError("messages debe ser una lista no vacía")
        normalized = []
        for message in messages:
            if not isinstance(message, dict):
                raise ValueError("Cada mensaje debe ser un diccionario")
            role = message.get("role")
            content = message.get("content")
            if role not in ("system", "user", "assistant"):
                raise ValueError("Rol de mensaje no admitido")
            if not isinstance(content, str) or not content.strip():
                raise ValueError("El contenido del mensaje no puede estar vacío")
            normalized.append({"role": role, "content": content})
        return normalized

    def _build_payload(self, messages: list[dict[str, str]]) -> dict:
        return {"model": self._model, "messages": messages, "stream": False}

    def _parse_response(self, response: dict) -> str:
        if not isinstance(response, dict):
            raise LocalBackendError("Respuesta del backend inválida.")

        if self._api == "ollama":
            message = response.get("message")
            text = message.get("content") if isinstance(message, dict) else None
            valid = response.get("done") is True
        else:
            choices = response.get("choices")
            choice = choices[0] if isinstance(choices, list) and choices else None
            message = choice.get("message") if isinstance(choice, dict) else None
            text = message.get("content") if isinstance(message, dict) else None
            valid = True

        if not valid or not isinstance(text, str) or not text.strip():
            raise LocalBackendError("El backend no devolvió texto válido.")
        return text
