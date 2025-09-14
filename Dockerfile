FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false && \
    poetry install --only=main --no-root

# Copy app code
COPY app/ ./app/

# Create logs directory
RUN mkdir -p /app/logs

# Set default environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV WORKERS=1

# Health check - use PORT environment variable
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health || exit 1

# Run app with environment variables
CMD uvicorn app.main:app --host ${HOST} --port ${PORT} --workers ${WORKERS}