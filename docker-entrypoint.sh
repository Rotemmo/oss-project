#!/usr/bin/env sh
set -e

# Start Ollama daemon in background
ollama serve >/tmp/ollama.log 2>&1 &

# המתנה קצרה עד שהפורט פתוח
# אם רוצים להקשיח, אפשר לעשות לופ שמוודא שהפורט 11434 פתוח
sleep 2

# Default OLLAMA_URL בתוך הקונטיינר
export OLLAMA_URL="${OLLAMA_URL:-http://localhost:11434}"

# Run the given command (CLI)
exec "$@"
