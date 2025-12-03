#!/bin/sh
set -e

# Inject runtime config directly into index.html
echo "Injecting runtime config into index.html..."
sed -i "s|<script src=\"/config.js\"></script>|<script>window.APP_CONFIG = { API_URL: '${API_URL:-http://localhost:8000}' };</script>|g" /usr/share/nginx/html/index.html

echo "Starting nginx..."
exec nginx -g "daemon off;"
