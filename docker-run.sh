#!/bin/bash
# Run Kitchen stack using Docker CLI commands
# This is equivalent to running docker-compose up

set -e

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found. Copy .env.example to .env and configure it."
    exit 1
fi

# Check required environment variables
if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "Error: POSTGRES_PASSWORD not set in .env"
    exit 1
fi

if [ -z "$JWT_SECRET_KEY" ]; then
    echo "Error: JWT_SECRET_KEY not set in .env"
    exit 1
fi

# Set defaults for optional variables
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_PORT=${FRONTEND_PORT:-80}
APPDATA_PATH=${APPDATA_PATH:-./data}
API_URL=${API_URL:-http://localhost:8000}

# Create network
echo "Creating Docker network..."
docker network create kitchen-network 2>/dev/null || true

# Create data directories
echo "Creating data directories..."
mkdir -p "${APPDATA_PATH}/postgres"
mkdir -p "${APPDATA_PATH}/logs"

# Run PostgreSQL
echo "Starting PostgreSQL..."
docker run -d \
    --name kitchen-postgres \
    --network kitchen-network \
    --restart unless-stopped \
    -e POSTGRES_USER=admin \
    -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
    -e POSTGRES_DB=roanes_kitchen \
    -v "${PWD}/${APPDATA_PATH}/postgres:/var/lib/postgresql/data" \
    --health-cmd "pg_isready -U admin -d roanes_kitchen" \
    --health-interval 30s \
    --health-timeout 5s \
    --health-retries 5 \
    postgres:15.10-alpine

# Wait for postgres to be healthy
echo "Waiting for PostgreSQL to be healthy..."
until [ "$(docker inspect -f '{{.State.Health.Status}}' kitchen-postgres)" == "healthy" ]; do
    sleep 1
done
echo "PostgreSQL is healthy!"

# Run Backend
echo "Starting Backend..."
docker run -d \
    --name kitchen-backend \
    --network kitchen-network \
    --restart unless-stopped \
    -p "${BACKEND_PORT}:8000" \
    -e DATABASE_URL="postgresql+asyncpg://admin:${POSTGRES_PASSWORD}@kitchen-postgres:5432/roanes_kitchen" \
    -e JWT_SECRET_KEY="${JWT_SECRET_KEY}" \
    -e DEBUG=false \
    -e ENVIRONMENT=production \
    -e DISCORD_BOT_TOKEN="${DISCORD_BOT_TOKEN:-}" \
    -e DISCORD_NOTIFICATION_CHANNEL_ID="${DISCORD_NOTIFICATION_CHANNEL_ID:-}" \
    -e DISCORD_TEST_CHANNEL_ID="${DISCORD_TEST_CHANNEL_ID:-}" \
    -v "${PWD}/${APPDATA_PATH}/logs:/app/logs" \
    --health-cmd "python3 -c \"import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()\"" \
    --health-interval 30s \
    --health-timeout 10s \
    --health-retries 3 \
    --health-start-period 40s \
    plongitudex/kitchen-backend:latest

# Wait for backend to be healthy
echo "Waiting for Backend to be healthy..."
until [ "$(docker inspect -f '{{.State.Health.Status}}' kitchen-backend)" == "healthy" ]; do
    sleep 1
done
echo "Backend is healthy!"

# Run Frontend
echo "Starting Frontend..."
docker run -d \
    --name kitchen-frontend \
    --network kitchen-network \
    --restart unless-stopped \
    -p "${FRONTEND_PORT}:80" \
    -e API_URL="${API_URL}" \
    --health-cmd "curl -f http://localhost:80" \
    --health-interval 30s \
    --health-timeout 10s \
    --health-retries 3 \
    --health-start-period 10s \
    plongitudex/kitchen-frontend:latest

echo ""
echo "✅ Kitchen stack is running!"
echo ""
echo "Frontend: http://localhost:${FRONTEND_PORT}"
echo "Backend API: http://localhost:${BACKEND_PORT}"
echo ""
echo "To view logs:"
echo "  docker logs kitchen-backend"
echo "  docker logs kitchen-frontend"
echo "  docker logs kitchen-postgres"
echo ""
echo "To stop the stack:"
echo "  docker stop kitchen-frontend kitchen-backend kitchen-postgres"
echo "  docker rm kitchen-frontend kitchen-backend kitchen-postgres"
echo "  docker network rm kitchen-network"
