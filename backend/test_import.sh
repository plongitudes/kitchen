#!/bin/bash

# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=demo1234" | jq -r '.access_token')

echo "Token: $TOKEN"
echo ""

# Test import preview
echo "Testing recipe import..."
curl -X POST http://localhost:8000/recipes/import-preview \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/"}' | jq '.'
