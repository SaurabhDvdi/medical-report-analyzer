# Production Worker Dockerfile for OCR & Medical Report Analysis
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TORCH_HOME=/app/.cache/torch

WORKDIR /app

# Install system native dependencies for Poppler, Tesseract OCR, PyMuPDF, EasyOCR & OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    libglib2.0-0 \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Copy backend source code into worker container
COPY backend/ .

# Ensure storage directories exist
RUN mkdir -p uploads charts logs .cache/torch

# Create non-root system user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

CMD ["python", "worker.py"]
