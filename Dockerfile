
# syntax=docker/dockerfile:1

# Python base image
FROM python:3.12-slim

# Install UV from the official image
COPY --from=ghcr.io/astral-sh/uv:0.13.7 /uv /uvx /bin/

WORKDIR /app

# Python and UV configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Copy dependency files first for Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies without installing the project itself
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Copy application source
COPY main.py ./main.py
COPY static/ ./static/

# Use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Application port
EXPOSE 8000

# Start FastAPI using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
