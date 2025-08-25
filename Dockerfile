# ---------- Base Python ----------
FROM python:3.11-slim AS app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://ollama.com/install.sh | sh

WORKDIR /app
COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
RUN pip install -e .
ENV PYTHONPATH=/app/src
RUN (ollama serve & sleep 3) && ollama pull gemma3:1b


COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENV OLLAMA_URL="http://localhost:11434"

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["llm-analyzer", "--help"]
