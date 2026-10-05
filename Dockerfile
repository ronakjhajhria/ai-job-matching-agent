FROM python:3.11-slim

WORKDIR /app

# Install system deps for pypdf and qdrant-client
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata first for layer caching
COPY pyproject.toml README.md ./
COPY alembic.ini ./

# Install all dependencies (no dev extras in production)
RUN pip install --no-cache-dir .

# Copy application code
COPY app/ ./app/
COPY evaluation/ ./evaluation/
COPY migrations/ ./migrations/

# Expose port
EXPOSE 8000

# Run with uvicorn (non-reload in production)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
