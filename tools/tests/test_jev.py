import json

import pytest

from tools.jev import parse_request, resolve_key, send_request


def test__parse_request__rejects_invalid_json__fail() -> None:
    with pytest.raises(ValueError, match=r"valid JSON"):
        parse_request(b"{")


def test__parse_request__rejects_oversized_input__fail() -> None:
    with pytest.raises(ValueError, match=r"64 KiB"):
        parse_request(b" " * 65537)


def test__parse_request__rejects_non_jev_model__fail() -> None:
    request = {
        "model": "expensive/other",
        "state": "x",
        "questions": {"q": {"type": "noul", "instructions": "Is x?"}},
    }
    with pytest.raises(ValueError, match=r"Jev model"):
        parse_request(json.dumps(request).encode())


def test__resolve_key__rejects_missing_key__fail() -> None:
    with pytest.raises(ValueError, match=r"OPENROUTER_API_KEY"):
        resolve_key(None, None)


def test__send_request__redacts_transport_error__fail() -> None:
    def failing_post(url: str, data: bytes, headers: dict[str, str]) -> bytes:
        raise RuntimeError("secret-token-in-error")

    with pytest.raises(RuntimeError, match=r"Decisions API request failed") as error:
        send_request(
            {"model": "typesafe/jev-1.13", "state": "x", "questions": {}},
            "secret-token",
            failing_post,
        )
    assert "secret-token" not in str(error.value)


def test__parse_request__accepts_typed_questions__success() -> None:
    request = {
        "model": "typesafe/jev-1.13",
        "state": "x",
        "questions": {"q": {"type": "noul", "instructions": "Is x?"}},
    }
    assert parse_request(json.dumps(request).encode()) == request


def test__resolve_key__prefers_process_environment__success() -> None:
    assert resolve_key("process-key", "user-key") == "process-key"


def test__send_request__posts_once_and_returns_response__success() -> None:
    calls: list[tuple[str, bytes, dict[str, str]]] = []

    def post(url: str, data: bytes, headers: dict[str, str]) -> bytes:
        calls.append((url, data, headers))
        return b'{"answers": {}, "usage": {"cost": 0}}'

    assert (
        send_request(
            {"model": "typesafe/jev-1.13", "state": "x", "questions": {}},
            "secret-token",
            post,
        )["usage"]["cost"]
        == 0
    )
    assert len(calls) == 1 and calls[0][2]["Authorization"] == "Bearer secret-token"
