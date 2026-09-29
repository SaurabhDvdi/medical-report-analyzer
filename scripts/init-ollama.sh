#!/usr/bin/env bash
# ==============================================================================
# Initialize Ollama Models for Medical Report Analyzer
# Pulls primary and fallback clinical models into the persistent Ollama volume.
# Does not re-download if the models already exist.
# ==============================================================================

set -euo pipefail

OLLAMA_HOST="${OLLAMA_HOST:-localhost:11434}"
PRIMARY_MODEL="${OLLAMA_MODEL:-qwen2.5:1.5b}"
FALLBACK_MODEL="${OLLAMA_FALLBACK_MODEL:-qwen2.5:3b}"

echo "[INFO] Checking Ollama service readiness at ${OLLAMA_HOST}..."
until curl -s "http://${OLLAMA_HOST}/api/tags" > /dev/null; do
    echo "[WAIT] Waiting for Ollama daemon to become ready..."
    sleep 3
done

echo "[OK] Ollama is online."

# Pull Primary Model
echo "[INFO] Pulling primary model: ${PRIMARY_MODEL}..."
curl -X POST "http://${OLLAMA_HOST}/api/pull" -d "{\"name\": \"${PRIMARY_MODEL}\"}"
echo ""

# Pull Fallback Model
echo "[INFO] Pulling fallback model: ${FALLBACK_MODEL}..."
curl -X POST "http://${OLLAMA_HOST}/api/pull" -d "{\"name\": \"${FALLBACK_MODEL}\"}"
echo ""

echo "[SUCCESS] All clinical LLM models are pulled and ready in Ollama!"
