Development Report: LLM-Driven C/C++ Vulnerability Analyzer
Project Overview- 

This project implements a CLI tool and Dockerized service that analyzes C/C++ source files for security vulnerabilities. The tool combines two complementary approaches:
Regex Rules – fast pattern-based detection of banned/unsafe functions (gets, strcpy, system, etc.).
LLM Reasoning – deeper vulnerability detection and fix suggestions using a local Large Language Model (LLM) via Ollama.
The system supports offline operation, flexible output formats (text, JSON), and can run both directly on a developer’s machine or inside a self-contained Docker image.

Key Challenges- 

LLM Integration – Selecting a local LLM runtime that works without cloud APIs.
Offline Support – Ensuring models are pre-downloaded or bundled in Docker.
Robustness – Combining rule-based scanning with LLM analysis for reliability.
Ease of Use – Exposing a single command-line interface (llm-analyzer).


Technology Decisions
Language: Python

Advantages:
Rich ecosystem for text processing, CLI libraries, JSON handling.
Easy to integrate with Ollama via REST API.
Well supported in Docker.

LLM Runtime: Ollama

Advantages
Runs models fully offline once downloaded.
Simple installation and ollama run API.
Supports multiple models (phi4, gemma3:1b).
Docker-friendly, easy to embed in images.


Architecture
High-Level Design
┌───────────────────────────┐
│        CLI Layer          │ ← User runs `llm-analyzer file.c`
├───────────────────────────┤
│   Output Formatter        │ ← Formats as text or JSON
├───────────────────────────┤
│ Vulnerability Analyzer    │ ← Combines heuristics + LLM findings
├───────────────────────────┤
│     Ollama Client         │ ← Sends code to model (phi4 / gemma3)
└───────────────────────────┘

Data Flow

Read C/C++ file, normalize input, add line numbers.
Run heuristic scan (regex rules).
Build structured prompt for the LLM.
Query LLM via Ollama REST API.
Parse response into structured findings.
Output results in chosen format (text or JSON).


Implementation Details & Decisions 

LLM runtime & model
Ollama is used so the tool can run fully offline once a model is available.
Default model: gemma3:1b (small, fast, good for laptops).
Optional: phi4 for stronger analysis.
The model is configurable with --model.

Handling long files (chunking)
Issue: with big files the LLM sometimes returns nothing (no error, no JSON).
Solution: split the file into chunks (~300–500 lines, with a small overlap), add line numbers, analyze each chunk, then merge & deduplicate findings.

Heuristics = baseline safety net
Even without the LLM, these rules still flag common issues and suggest safe fixes:

gets() → CWE-242 (use fgets)
sprintf() → CWE-785 (use snprintf)
strcpy() → CWE-120 (use strncpy/strlcpy)
printf non-constant format → CWE-134 (use printf("%s", x))
scanf("%s", …) without width → CWE-120 (add width, e.g., %64s)
system() → CWE-78 (avoid, or use exec*/APIs)
simple UAF/double-free hints (best-effort)

Offline & Docker
Two ways:
Pull at build: ollama pull gemma3:1b during Docker build (simple but heavy).
BYOM: copy pre-downloaded ~/.ollama/models into the image (fast, fully offline builds).
The image starts Ollama in the entrypoint, then runs the CLI.

Docker & ollama:

Why Docker?
Provides a reproducible environment.
Ensures Ollama + Python + tool are all installed consistently.
Simplifies usage: a single docker run command works on any machine.

Why Ollama?
Offline operation: once models are pulled, no internet required.
Unified interface for multiple models.
Easy integration in Docker images.

Offline Guarantee
By default, models are pulled once via ollama pull.
For full self-containment, models can be copied into the Docker image (COPY ollama_models/ /root/.ollama/models/) to avoid any internet dependency.