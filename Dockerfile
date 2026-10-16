# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install production dependencies from builder
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
RUN chown -R appuser:appuser /app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python manage.py check --deploy || exit 1

# Switch to non-root user
USER appuser

# Run with gunicorn
CMD ["gunicorn", "taskmanager.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]
