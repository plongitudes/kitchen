# Stage 1: Builder - compile dependencies
FROM python:3.11.10-slim AS builder

WORKDIR /build

# Install build dependencies
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and build wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# Stage 2: Runtime - minimal production image
FROM python:3.11.10-slim

WORKDIR /app

# Install only runtime system dependencies
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy pre-built wheels from builder stage and install
COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && \
    rm -rf /wheels

# Copy entrypoint script
COPY --chown=appuser:appuser entrypoint.sh /entrypoint.sh

# Copy application code
COPY --chown=appuser:appuser . .

# Make entrypoint executable
RUN chmod +x /entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Run the application via entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
