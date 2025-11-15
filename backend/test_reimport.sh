#!/bin/bash

# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=demo1234" | jq -r '.access_token')

echo "Token: $TOKEN"
echo ""

# First, let's list recipes to find one with a source_url
echo "Finding recipes with source URLs..."
RECIPE_ID=$(curl -s -X GET "http://localhost:8000/recipes" \
  -H "Authorization: Bearer $TOKEN" | jq -r '[.[] | select(.source_url != null)] | .[0].id')

if [ "$RECIPE_ID" = "null" ] || [ -z "$RECIPE_ID" ]; then
  echo "No recipes with source_url found. Creating one from import..."

  # Import a recipe first
  RECIPE_ID=$(curl -s -X POST http://localhost:8000/recipes/import-preview \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"url": "https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/"}' | \
    jq -r '{
      name: .name,
      recipe_type: .recipe_type,
      description: .description,
      prep_time_minutes: .prep_time_minutes,
      cook_time_minutes: .cook_time_minutes,
      source_url: .source_url,
      ingredients: [.ingredients[] | {ingredient_name, quantity, unit, order: 0}],
      instructions: [.instructions[] | {step_number, description}]
    }' | \
    curl -s -X POST http://localhost:8000/recipes \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d @- | jq -r '.id')

  echo "Created recipe: $RECIPE_ID"
fi

echo "Recipe ID: $RECIPE_ID"
echo ""

# Test re-import
echo "Testing re-import for recipe $RECIPE_ID..."
curl -X POST "http://localhost:8000/recipes/$RECIPE_ID/reimport" \
  -H "Authorization: Bearer $TOKEN" | jq '.'
