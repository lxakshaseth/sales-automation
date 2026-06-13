# syntax=docker/dockerfile:1

# Python 3.11 slim keeps the runtime small while staying compatible with FastAPI,
# Celery, Redis clients, Groq, Twilio, and the rest of the backend stack.
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install only the system packages needed for building common Python wheels and
# for the container healthcheck. Remove apt metadata to keep the image smaller.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies before copying the app so Docker can cache this layer when
# application code changes but requirements.txt does not.
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the backend source into the image.
COPY app ./app

# Create writable runtime directories and run as a non-root user for production
# safety. The numeric UID/GID keeps file ownership predictable in Linux hosts.
RUN addgroup --system --gid 1001 appgroup \
    && adduser --system --uid 1001 --ingroup appgroup appuser \
    && mkdir -p /app/data /app/logs \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Docker marks the app unhealthy if FastAPI stops responding.
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/ || exit 1

# docker-compose overrides this for development hot reload. This default is a
# production-friendly uvicorn process.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
