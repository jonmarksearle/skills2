#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if command -v uv >/dev/null 2>&1; then
  uv_command="uv"
elif [[ -x /e/work/.uv/bin/uv.exe ]]; then
  uv_command="/e/work/.uv/bin/uv.exe"
else
  printf '%s\n' 'uv was not found in PATH or E:\work\.uv\bin.' >&2
  exit 1
fi

exec "$uv_command" run --script "$script_dir/jev_openrouter_mcp.py" "$@"
