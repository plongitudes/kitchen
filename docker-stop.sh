#!/bin/bash
# Stop and remove Kitchen stack containers

echo "Stopping containers..."
docker stop kitchen-frontend kitchen-backend kitchen-postgres 2>/dev/null || true

echo "Removing containers..."
docker rm kitchen-frontend kitchen-backend kitchen-postgres 2>/dev/null || true

echo "Removing network..."
docker network rm kitchen-network 2>/dev/null || true

echo ""
echo "✅ Kitchen stack stopped and removed!"
echo ""
echo "Note: Data volumes in ${APPDATA_PATH:-./data} are preserved"
echo "To completely clean up, run:"
echo "  rm -rf ${APPDATA_PATH:-./data}"
