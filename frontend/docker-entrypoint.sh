#!/bin/sh
set -e

# Generate config.js from template with runtime environment variables
echo "Generating runtime config..."
envsubst '${API_URL}' < /usr/share/nginx/html/config.js.template > /usr/share/nginx/html/config.js

echo "Starting nginx..."
exec nginx -g "daemon off;"
