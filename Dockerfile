# Multi-stage build for Python FastAPI application
FROM python:3.13-alpine AS builder


# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apk update && apk add --no-cache \
    build-base \
    curl

# Install Poetry
RUN pip install poetry==1.7.1

# Configure Poetry
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VENV_IN_PROJECT=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

# Copy poetry files
WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry config virtualenvs.in-project true && \
    poetry install --only=main --no-root && \
    rm -rf $POETRY_CACHE_DIR

# Production stage
FROM python:3.13-alpine AS production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# Install system dependencies for runtime
RUN apk update && apk add --no-cache \
    libpq

# Create app user
RUN addgroup -g 1000 app \
    && adduser -u 1000 -G app -s /bin/sh -D app

# Copy virtual environment from builder stage
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Copy application code
WORKDIR /app
COPY --chown=app:app pyproject.toml README.md ./
COPY --chown=app:app src/ ./src/
COPY --chown=app:app static/ ./static/
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app migrations/ ./migrations/

# Install the application
RUN pip install -e .

# Switch to app user
USER app

# Create data directory for SQLite (if using SQLite)
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["uvicorn", "image_definitions.main:app", "--host", "0.0.0.0", "--port", "8000"]
