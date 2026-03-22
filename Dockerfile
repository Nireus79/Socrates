# Multi-stage Dockerfile for Socrates API

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Set environment variables
ENV PATH=/root/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SOCRATES_API_HOST=0.0.0.0 \
    SOCRATES_API_PORT=8000

# Copy application code
COPY socrates-api/ /app/socrates-api/
COPY socratic_system/ /app/socratic_system/
COPY modules/ /app/modules/

# Install the API application in development mode
RUN cd /app/socrates-api && pip install --no-cache-dir -e .

# Create data directory
RUN mkdir -p /app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${SOCRATES_API_PORT}/health || exit 1

# Expose port
EXPOSE ${SOCRATES_API_PORT}

# Create non-root user for security
RUN useradd -m -u 1000 socrates && \
    chown -R socrates:socrates /app
USER socrates

# Run the API server
CMD ["socrates-api"]
