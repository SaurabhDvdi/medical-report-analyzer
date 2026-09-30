#!/bin/sh
# ==============================================================================
# Initialize Ollama Models for Medical Report Analyzer
# Pulls primary and fallback clinical models into the persistent Ollama volume.
# Does not re-download if the models already exist.
# ==============================================================================

set -eu

OLLAMA_HOST="${OLLAMA_HOST:-ollama:11434}"
PRIMARY_MODEL="${OLLAMA_MODEL:-qwen2.5:1.5b}"
FALLBACK_MODEL="${OLLAMA_FALLBACK_MODEL:-qwen2.5:3b}"

echo "[INFO] Checking Ollama service readiness at ${OLLAMA_HOST}..."

connected=0
for i in $(seq 1 30); do
    if command -v ollama >/dev/null 2>&1; then
        if OLLAMA_HOST="${OLLAMA_HOST}" ollama list >/dev/null 2>&1; then
            connected=1
            break
        fi
    elif command -v curl >/dev/null 2>&1; then
        if curl -s "http://${OLLAMA_HOST}/api/tags" >/dev/null 2>&1; then
            connected=1
            break
        fi
    fi
    echo "[WAIT] Waiting for Ollama at ${OLLAMA_HOST}... attempt ${i}/30"
    sleep 2
done

if [ "$connected" -ne 1 ]; then
    echo "[ERROR] Ollama at ${OLLAMA_HOST} is not reachable after 60s."
    exit 1
fi

echo "[OK] Ollama is online."

pull_if_missing() {
    target_model="$1"
    echo "[INFO] Verifying model availability: '${target_model}'..."

    model_present=0
    if command -v ollama >/dev/null 2>&1; then
        if OLLAMA_HOST="${OLLAMA_HOST}" ollama list | grep -q "${target_model}"; then
            model_present=1
        fi
    elif command -v curl >/dev/null 2>&1; then
        tags_response=$(curl -s "http://${OLLAMA_HOST}/api/tags" 2>/dev/null || echo "")
        case "$tags_response" in
            *"${target_model}"*) model_present=1 ;;
        esac
    fi

    if [ "$model_present" -eq 1 ]; then
        echo "[OK] Model '${target_model}' is already downloaded. Skipping pull."
    else
        echo "[INFO] Model '${target_model}' not found. Downloading model to persistent volume..."
        if command -v ollama >/dev/null 2>&1; then
            OLLAMA_HOST="${OLLAMA_HOST}" ollama pull "${target_model}"
        elif command -v curl >/dev/null 2>&1; then
            curl -f -X POST "http://${OLLAMA_HOST}/api/pull" -d "{\"name\": \"${target_model}\", \"stream\": false}"
        fi
        echo "[SUCCESS] Model '${target_model}' pulled and verified."
    fi
}

pull_if_missing "${PRIMARY_MODEL}"
pull_if_missing "${FALLBACK_MODEL}"

echo "[SUCCESS] All clinical LLM models are ready in Ollama!"
