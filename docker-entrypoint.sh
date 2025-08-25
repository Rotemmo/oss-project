#!/usr/bin/env sh
set -e

ollama serve >/tmp/ollama.log 2>&1 &

sleep 2

export OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

exec "$@"
