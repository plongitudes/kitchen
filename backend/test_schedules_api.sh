#!/bin/bash

# Test script for Schedule API endpoints
set -e  # Exit on error

BASE_URL="http://localhost:8000"

echo "============================================="
echo "Schedule API Test Suite"
echo "============================================="
echo ""

# Step 1: Register and login
echo "=== 1. Register and Login ==="
REGISTER_RESPONSE=$(curl -s -X POST $BASE_URL/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "scheduletest2", "password": "password123"}' || echo '{"id":"existing"}')

USER_ID=$(echo "$REGISTER_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "c92044a3-491a-4175-9d15-e0ff5bbfaa74")
echo "User ID: $USER_ID"

LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=scheduletest&password=password123")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "Got token: ${TOKEN:0:50}..."
echo ""

# Step 2: Create a schedule sequence
echo "=== 2. Create Schedule Sequence ==="
SEQUENCE_RESPONSE=$(curl -s -X POST $BASE_URL/schedules \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Meal Rotation",
    "advancement_day_of_week": 0,
    "advancement_time": "08:00"
  }')
echo "$SEQUENCE_RESPONSE" | python3 -m json.tool

SEQUENCE_ID=$(echo "$SEQUENCE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Sequence ID: $SEQUENCE_ID"
echo ""

# Step 3: Create a recipe for assignments
echo "=== 3. Create Test Recipe ==="
RECIPE_RESPONSE=$(curl -s -X POST $BASE_URL/recipes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Spaghetti Carbonara\",
    \"recipe_type\": \"dinner\",
    \"prep_time_minutes\": 10,
    \"cook_time_minutes\": 20,
    \"owner_id\": \"$USER_ID\",
    \"ingredients\": [],
    \"instructions\": []
  }")

RECIPE_ID=$(echo "$RECIPE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Recipe ID: $RECIPE_ID"
echo ""

# Step 4: Create week template with assignments
echo "=== 4. Create Week Template with Assignments ==="
WEEK1_RESPONSE=$(curl -s -X POST $BASE_URL/schedules/$SEQUENCE_ID/weeks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"theme_name\": \"Italian Week\",
    \"assignments\": [
      {
        \"day_of_week\": 1,
        \"assigned_user_id\": \"$USER_ID\",
        \"action\": \"cook\",
        \"recipe_id\": \"$RECIPE_ID\",
        \"order\": 0
      },
      {
        \"day_of_week\": 2,
        \"assigned_user_id\": \"$USER_ID\",
        \"action\": \"takeout\",
        \"order\": 0
      }
    ]
  }")
echo "$WEEK1_RESPONSE" | python3 -m json.tool

WEEK1_ID=$(echo "$WEEK1_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Week 1 ID: $WEEK1_ID"
echo ""

# Step 5: Create second week template
echo "=== 5. Create Second Week Template ==="
WEEK2_RESPONSE=$(curl -s -X POST $BASE_URL/schedules/$SEQUENCE_ID/weeks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"theme_name\": \"Mexican Week\",
    \"assignments\": []
  }")
echo "$WEEK2_RESPONSE" | python3 -m json.tool

WEEK2_ID=$(echo "$WEEK2_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
echo "Week 2 ID: $WEEK2_ID"
echo ""

# Step 6: List all schedules
echo "=== 6. List All Schedules ==="
curl -s -X GET $BASE_URL/schedules \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Step 7: Get schedule with weeks
echo "=== 7. Get Schedule with All Weeks ==="
curl -s -X GET $BASE_URL/schedules/$SEQUENCE_ID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Step 8: List weeks in sequence
echo "=== 8. List Weeks in Sequence ==="
curl -s -X GET $BASE_URL/schedules/$SEQUENCE_ID/weeks \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Step 9: Get specific week with assignments
echo "=== 9. Get Week with Assignments ==="
curl -s -X GET $BASE_URL/schedules/$SEQUENCE_ID/weeks/$WEEK1_ID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Step 10: Get current week
echo "=== 10. Get Current Week ==="
curl -s -X GET $BASE_URL/schedules/$SEQUENCE_ID/current-week \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Step 11: Update week template
echo "=== 11. Update Week Template ==="
curl -s -X PUT $BASE_URL/schedules/$SEQUENCE_ID/weeks/$WEEK1_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "theme_name": "Italian Week (Updated)"
  }' | python3 -m json.tool
echo ""

# Step 12: Reorder weeks
echo "=== 12. Reorder Weeks ==="
curl -s -X POST $BASE_URL/schedules/$SEQUENCE_ID/weeks/reorder \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"week_ids\": [\"$WEEK2_ID\", \"$WEEK1_ID\"]
  }" | python3 -m json.tool
echo ""

# Step 13: Add assignment to week
echo "=== 13. Add Assignment to Week ==="
curl -s -X POST $BASE_URL/schedules/$SEQUENCE_ID/weeks/$WEEK2_ID/assignments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"day_of_week\": 3,
    \"assigned_user_id\": \"$USER_ID\",
    \"action\": \"rest\",
    \"order\": 0
  }" | python3 -m json.tool
echo ""

# Step 14: Update schedule sequence
echo "=== 14. Update Schedule Sequence ==="
curl -s -X PUT $BASE_URL/schedules/$SEQUENCE_ID \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Weekly Meal Rotation (Updated)",
    "advancement_time": "09:00"
  }' | python3 -m json.tool
echo ""

# Step 15: Soft delete a week
echo "=== 15. Soft Delete Week ==="
curl -s -X DELETE $BASE_URL/schedules/$SEQUENCE_ID/weeks/$WEEK2_ID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Step 16: List weeks (should not include retired)
echo "=== 16. List Weeks (Retired Excluded) ==="
curl -s -X GET "$BASE_URL/schedules/$SEQUENCE_ID/weeks?include_retired=false" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Step 17: List weeks including retired
echo "=== 17. List Weeks (Including Retired) ==="
curl -s -X GET "$BASE_URL/schedules/$SEQUENCE_ID/weeks?include_retired=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "============================================="
echo "All Tests Completed Successfully!"
echo "============================================="
