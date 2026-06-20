#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v streamlit >/dev/null 2>&1; then
    echo "Error: Streamlit is not installed or not in PATH."
    echo "Run: pip install -r requirements.txt"
    exit 1
fi

if ! command -v codex >/dev/null 2>&1; then
    echo "Error: Codex CLI is not installed or not in PATH."
    exit 1
fi

exec streamlit run app.py "$@"
