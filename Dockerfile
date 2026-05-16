# MAOS v5.0 - Dockerfile
# Production-ready Docker image for the Multi-Agent Orchestration System

# Use official Python base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MAOS_SYSTEM_NAME=MAOS \
    MAOS_VERSION=5.0.0 \
    MAOS_DEBUG=false \
    MAOS_API_HOST=0.0.0.0 \
    MAOS_API_PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better cache usage)
COPY pyproject.toml* ./

# Copy the MAOS package
COPY maos/ ./maos/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir fastapi uvicorn pydantic

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the API server
CMD ["python", "-c", "from maos.api import run_server; run_server(host='0.0.0.0', port=8000)"]
