@echo off
REM ==============================================================================
REM Initialize Ollama Models for Medical Report Analyzer (Windows)
REM Pulls primary and fallback clinical models into persistent Ollama storage.
REM ==============================================================================

set OLLAMA_HOST=%OLLAMA_HOST%
if "%OLLAMA_HOST%"=="" set OLLAMA_HOST=localhost:11434

set PRIMARY_MODEL=%OLLAMA_MODEL%
if "%PRIMARY_MODEL%"=="" set PRIMARY_MODEL=qwen2.5:1.5b

set FALLBACK_MODEL=%OLLAMA_FALLBACK_MODEL%
if "%FALLBACK_MODEL%"=="" set FALLBACK_MODEL=qwen2.5:3b

echo [INFO] Pulling primary model: %PRIMARY_MODEL%...
curl -X POST "http://%OLLAMA_HOST%/api/pull" -d "{\"name\": \"%PRIMARY_MODEL%\"}"
echo.

echo [INFO] Pulling fallback model: %FALLBACK_MODEL%...
curl -X POST "http://%OLLAMA_HOST%/api/pull" -d "{\"name\": \"%FALLBACK_MODEL%\"}"
echo.

echo [SUCCESS] Ollama models ready!
