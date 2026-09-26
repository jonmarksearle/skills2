#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

"""Submit one bounded Jev Decisions API request without exposing its key."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from urllib.request import Request, urlopen

ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
DEFAULT_MODEL = "typesafe/jev-1.13"
MAX_REQUEST_BYTES = 64 * 1024
type Post = Callable[[str, bytes, dict[str, str]], bytes]


def parse_request(raw: bytes) -> dict[str, object]:
    """Validate a bounded typed request before any network access."""
    if len(raw) > MAX_REQUEST_BYTES:
        raise ValueError("Request exceeds 64 KiB.")
    try:
        request = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError("Request must be valid JSON.") from error
    if (
        not isinstance(request, dict)
        or "state" not in request
        or not isinstance(request.get("questions"), dict)
        or not request["questions"]
    ):
        raise ValueError("Request needs state and nonempty typed questions.")
    model = request.get("model", DEFAULT_MODEL)
    if not isinstance(model, str) or not model.startswith(
        ("typesafe/jev-", "~typesafe/jev-")
    ):
        raise ValueError("Request must select a Jev model.")
    return {**request, "model": model}


def resolve_key(process_key: str | None, user_key: str | None) -> str:
    """Choose a key without exposing it in diagnostics."""
    key = process_key or user_key
    if not key:
        raise ValueError("OPENROUTER_API_KEY is unavailable.")
    return key


def read_user_key() -> str:
    """Read the Windows user environment value into this process only."""
    command = "[Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY','User')"
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def post_json(url: str, data: bytes, headers: dict[str, str]) -> bytes:
    """Send one HTTP request with a bounded timeout."""
    request = Request(url, data=data, headers=headers, method="POST")
    with urlopen(request, timeout=20) as response:
        return response.read()


def safe_post(post: Post, data: bytes, headers: dict[str, str]) -> bytes:
    """Keep transport errors and credentials out of diagnostics."""
    try:
        return post(ENDPOINT, data, headers)
    except (OSError, RuntimeError):
        raise RuntimeError("Decisions API request failed.") from None


def send_request(
    request: dict[str, object], key: str, post: Post = post_json
) -> dict[str, object]:
    """Send one typed request and return the JSON response."""
    data = json.dumps(request, ensure_ascii=False).encode("utf-8")
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    response = json.loads(safe_post(post, data, headers))
    if not isinstance(response, dict) or "answers" not in response:
        raise ValueError("Decisions API response lacks answers.")
    return response


def run(path: Path, post: Post = post_json) -> dict[str, object]:
    """Read one request, resolve the user key, and submit it once."""
    request = parse_request(path.read_bytes())
    process_key = os.environ.get("OPENROUTER_API_KEY")
    key = resolve_key(process_key, "" if process_key else read_user_key())
    return send_request(request, key, post)


def run_cli() -> int:
    """Print one response or a credential-free error."""
    if len(sys.argv) != 2:
        print("Usage: jev.sh REQUEST.json", file=sys.stderr)
        return 2
    try:
        result = run(Path(sys.argv[1]))
    except (OSError, ValueError, RuntimeError):
        print(
            "Jev request failed; check input, user key, and service.", file=sys.stderr
        )
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
