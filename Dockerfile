FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Env flags: don't write .pyc, stream logs immediately (critical for Cloud Run)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install dependencies first (layer cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source (.env is excluded via .dockerignore)
COPY app.py .
COPY google_services.py .
COPY templates/ templates/

# Cloud Run injects PORT env variable; default 8080
EXPOSE 8080

# Healthcheck so Cloud Run knows the container is ready
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/health')" || exit 1

# Production WSGI server:
#   --workers 1   : Cloud Run scales via instances, not workers
#   --threads 8   : handle concurrent requests within one worker
#   --timeout 120 : generous timeout for Gemini API calls
#   --preload     : load app before forking → faster cold starts
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "8", "--timeout", "120", "--preload", "app:app"]
