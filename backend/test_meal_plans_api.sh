#!/bin/bash

# Test script for Meal Plans API endpoints
set -e  # Exit on error

BASE_URL="http://localhost:8000"

echo "============================================="
echo "Meal Plans API Test Suite"
echo "============================================="
echo ""

# Step 1: Login
echo "=== 1. Login ==="
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=scheduletest&password=password123")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "Got token: ${TOKEN:0:50}..."
echo ""

# Step 2: Get list of schedules to find one to use
echo "=== 2. Get Schedules ==="
SCHEDULES=$(curl -s -X GET $BASE_URL/schedules \
  -H "Authorization: Bearer $TOKEN")

SEQUENCE_ID=$(echo "$SCHEDULES" | python3 -c "import sys, json; schedules = json.load(sys.stdin); print(schedules[0]['id'] if schedules else '')")

if [ -z "$SEQUENCE_ID" ]; then
    echo "No sequences found. Creating one..."

    # Create a schedule with weeks first
    USER_ID=$(curl -s -X GET $BASE_URL/me \
      -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

    SEQUENCE_RESPONSE=$(curl -s -X POST $BASE_URL/schedules \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Test Meal Rotation",
        "advancement_day_of_week": 0,
        "advancement_time": "08:00"
      }')

    SEQUENCE_ID=$(echo "$SEQUENCE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

    # Create test recipe
    RECIPE_RESPONSE=$(curl -s -X POST $BASE_URL/recipes \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"name\": \"Test Recipe\",
        \"recipe_type\": \"dinner\",
        \"owner_id\": \"$USER_ID\",
        \"ingredients\": [],
        \"instructions\": []
      }")

    RECIPE_ID=$(echo "$RECIPE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

    # Create week 1
    curl -s -X POST $BASE_URL/schedules/$SEQUENCE_ID/weeks \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"theme_name\": \"Week 1 - Italian\",
        \"assignments\": [
          {
            \"day_of_week\": 1,
            \"assigned_user_id\": \"$USER_ID\",
            \"action\": \"cook\",
            \"recipe_id\": \"$RECIPE_ID\",
            \"order\": 0
          }
        ]
      }" > /dev/null

    # Create week 2
    curl -s -X POST $BASE_URL/schedules/$SEQUENCE_ID/weeks \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d "{
        \"theme_name\": \"Week 2 - Mexican\",
        \"assignments\": []
      }" > /dev/null

    echo "Created sequence: $SEQUENCE_ID"
fi

echo "Using sequence: $SEQUENCE_ID"
echo ""

# Step 3: Advance week (creates first instance)
echo "=== 3. Advance Week (Create First Instance) ==="
ADVANCE_RESPONSE=$(curl -s -X POST $BASE_URL/meal-plans/advance-week \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"sequence_id\": \"$SEQUENCE_ID\"}")
echo "$ADVANCE_RESPONSE" | python3 -m json.tool
echo ""

INSTANCE_ID=$(echo "$ADVANCE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['new_instance']['id'])")
echo "Created instance: $INSTANCE_ID"
echo ""

# Step 4: Get current meal plan
echo "=== 4. Get Current Meal Plan ==="
curl -s -X GET "$BASE_URL/meal-plans/current?sequence_id=$SEQUENCE_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Step 5: List all meal plans
echo "=== 5. List All Meal Plans ==="
curl -s -X GET $BASE_URL/meal-plans \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Step 6: Get specific meal plan instance
echo "=== 6. Get Specific Meal Plan Instance ==="
curl -s -X GET $BASE_URL/meal-plans/$INSTANCE_ID \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Step 7: Advance week again (should loop to next week)
echo "=== 7. Advance Week Again (Should Go to Week 2) ==="
ADVANCE2_RESPONSE=$(curl -s -X POST $BASE_URL/meal-plans/advance-week \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"sequence_id\": \"$SEQUENCE_ID\"}")
echo "$ADVANCE2_RESPONSE" | python3 -m json.tool
echo ""

# Step 8: Verify current week changed
echo "=== 8. Verify Current Week Changed ==="
curl -s -X GET "$BASE_URL/meal-plans/current?sequence_id=$SEQUENCE_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Step 9: Advance week one more time (should loop back to week 1)
echo "=== 9. Advance Week Third Time (Should Loop Back to Week 1) ==="
ADVANCE3_RESPONSE=$(curl -s -X POST $BASE_URL/meal-plans/advance-week \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"sequence_id\": \"$SEQUENCE_ID\"}")
echo "$ADVANCE3_RESPONSE" | python3 -m json.tool

NEW_WEEK_NUM=$(echo "$ADVANCE3_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['new_week_number'])")
echo ""
echo "New week number after loop: $NEW_WEEK_NUM (should be 1)"
echo ""

# Step 10: List all instances to see history
echo "=== 10. List All Instances (Should Show 3) ==="
curl -s -X GET $BASE_URL/meal-plans \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "============================================="
echo "All Tests Completed Successfully!"
echo "============================================="
