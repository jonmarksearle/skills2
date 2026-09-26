#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///

from __future__ import annotations

import argparse
import ctypes
import getpass
import os
import subprocess
import sys
from pathlib import Path
from ctypes import wintypes


SERVICE_NAME = "OpenRouter_JevMCP"
ACCOUNT_NAME = "OPENROUTER_API_KEY"
SERVER_COMMAND = "npx.cmd -y @jkudish/jev-mcp"
TARGET_NAME = f"{SERVICE_NAME}:{ACCOUNT_NAME}"


class _Credential(ctypes.Structure):
    _fields_ = [
        ("Flags", wintypes.DWORD),
        ("Type", wintypes.DWORD),
        ("TargetName", wintypes.LPWSTR),
        ("Comment", wintypes.LPWSTR),
        ("LastWritten", wintypes.FILETIME),
        ("CredentialBlobSize", wintypes.DWORD),
        ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
        ("Persist", wintypes.DWORD),
        ("AttributeCount", wintypes.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wintypes.LPWSTR),
        ("UserName", wintypes.LPWSTR),
    ]


def _credential_api():
    if os.name != "nt":
        raise RuntimeError("Windows Credential Manager is available only on Windows.")
    advapi = ctypes.WinDLL("Advapi32.dll", use_last_error=True)
    advapi.CredWriteW.argtypes = [ctypes.POINTER(_Credential), wintypes.DWORD]
    advapi.CredWriteW.restype = wintypes.BOOL
    advapi.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                 ctypes.POINTER(ctypes.POINTER(_Credential))]
    advapi.CredReadW.restype = wintypes.BOOL
    advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
    advapi.CredDeleteW.restype = wintypes.BOOL
    advapi.CredFree.argtypes = [ctypes.c_void_p]
    advapi.CredFree.restype = None
    return advapi


def read_key_file(path: Path) -> str:
    lines = tuple(line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
    if len(lines) != 1:
        raise ValueError("Key file must contain one non-empty line.")
    value = lines[0]
    if value.startswith(f"{ACCOUNT_NAME}="):
        value = value.partition("=")[2].strip().strip("\"'")
    if not value.startswith("sk-or-"):
        raise ValueError("Key file does not contain an OpenRouter key.")
    return value


def save_key(secret: str) -> None:
    if not secret.startswith("sk-or-"):
        raise ValueError("The value is not an OpenRouter key.")
    try:
        encoded = secret.encode("utf-8")
        blob = (ctypes.c_ubyte * len(encoded)).from_buffer_copy(encoded)
        credential = _Credential(
            Type=1,
            TargetName=TARGET_NAME,
            CredentialBlobSize=len(encoded),
            CredentialBlob=ctypes.cast(blob, ctypes.POINTER(ctypes.c_ubyte)),
            Persist=2,
            UserName=ACCOUNT_NAME,
        )
        api = _credential_api()
        if not api.CredWriteW(ctypes.byref(credential), 0):
            raise RuntimeError(f"Windows credential write failed (error {ctypes.get_last_error()}).")
        stored_secret = get_key()
    except Exception as error:
        detail = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        raise RuntimeError(f"Credential Manager operation failed ({detail}).") from None
    if stored_secret != secret:
        raise RuntimeError("Credential Manager verification failed.")
    print("OpenRouter key stored in the Windows credential store.")


def get_key() -> str:
    api = _credential_api()
    credential = ctypes.POINTER(_Credential)()
    if not api.CredReadW(TARGET_NAME, 1, 0, ctypes.byref(credential)):
        code = ctypes.get_last_error()
        raise RuntimeError(f"No readable OpenRouter credential is stored (Windows error {code}).")
    try:
        raw = ctypes.string_at(credential.contents.CredentialBlob,
                               credential.contents.CredentialBlobSize)
        return raw.decode("utf-8")
    finally:
        api.CredFree(credential)


def run_server() -> int:
    if os.name != "nt":
        raise RuntimeError("The Jev keyring launcher is configured for Windows.")
    environment = os.environ.copy()
    environment[ACCOUNT_NAME] = get_key()
    environment["JEV_PROVIDER"] = "openrouter"
    return subprocess.run(
        ["cmd.exe", "/d", "/c", SERVER_COMMAND],
        env=environment,
        check=False,
    ).returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the Jev MCP OpenRouter credential.")
    commands = parser.add_subparsers(dest="command", required=True)
    file_command = commands.add_parser("store-file", help="Read a key file into Windows Credential Manager.")
    file_command.add_argument("path", type=Path)
    commands.add_parser("store-prompt", help="Prompt for a key without echoing it.")
    commands.add_parser("delete", help="Remove the stored key.")
    commands.add_parser("serve", help="Start Jev MCP with the key loaded from Credential Manager.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "store-file":
        save_key(read_key_file(args.path))
    elif args.command == "store-prompt":
        save_key(getpass.getpass("OpenRouter API key: "))
    elif args.command == "delete":
        api = _credential_api()
        if not api.CredDeleteW(TARGET_NAME, 1, 0):
            raise RuntimeError("No OpenRouter key is stored for Jev MCP.")
        print("Stored Jev MCP OpenRouter key removed.")
    else:
        return run_server()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        message = str(error) if isinstance(error, RuntimeError) else type(error).__name__
        print(f"Credential operation failed ({message}).", file=sys.stderr)
        raise SystemExit(1) from None
