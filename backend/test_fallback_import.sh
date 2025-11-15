#!/bin/bash

# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=demo1234" | jq -r '.access_token')

echo "Testing fallback import with unsupported site..."
echo "Token: $TOKEN"
echo ""

# Try a smaller recipe site that likely isn't in the supported list
# This site should have schema.org markup but not be explicitly supported
echo "Test 1: Trying a smaller recipe blog with schema.org markup..."
curl -X POST http://localhost:8000/recipes/import-preview \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "https://www.budgetbytes.com/one-pot-chili-pasta/"}' | jq '.'

echo ""
echo "Test 2: Trying another site..."
curl -X POST http://localhost:8000/recipes/import-preview \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url": "https://www.delish.com/cooking/recipe-ideas/a25638053/easy-chili-recipe/"}' | jq '.'
