#!/bin/bash

# Test script for start-on-arbitrary-week feature
set -e

BASE_URL="http://localhost:8000"

echo "============================================="
echo "Start on Arbitrary Week Test"
echo "============================================="
echo ""

# Login with existing test user
echo "=== 1. Login ==="
LOGIN_RESPONSE=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=scheduletest&password=password123")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "Got token: ${TOKEN:0:50}..."
echo ""

# Get existing sequence (from previous test runs)
echo "=== 2. List Schedules ==="
SCHEDULES=$(curl -s -X GET $BASE_URL/schedules \
  -H "Authorization: Bearer $TOKEN")
echo "$SCHEDULES" | python3 -m json.tool
echo ""

SEQUENCE_ID=$(echo "$SCHEDULES" | python3 -c "import sys, json; schedules = json.load(sys.stdin); print(schedules[0]['id'] if schedules else '')")

if [ -z "$SEQUENCE_ID" ]; then
  echo "No schedules found. Please run test_schedules_api.sh first to create test data."
  exit 1
fi

echo "Using sequence: $SEQUENCE_ID"
echo ""

# Get sequence details with templates
echo "=== 3. Get Sequence Details ==="
SEQUENCE=$(curl -s -X GET $BASE_URL/schedules/$SEQUENCE_ID \
  -H "Authorization: Bearer $TOKEN")
echo "$SEQUENCE" | python3 -m json.tool
echo ""

# Extract template info for starting
TEMPLATE_ID=$(echo "$SEQUENCE" | python3 -c "
import sys, json
seq = json.load(sys.stdin)
mappings = seq.get('week_mappings', [])
if mappings:
    # Get second template if available, otherwise first
    template = mappings[1] if len(mappings) > 1 else mappings[0]
    print(template['week_template_id'])
")

POSITION=$(echo "$SEQUENCE" | python3 -c "
import sys, json
seq = json.load(sys.stdin)
mappings = seq.get('week_mappings', [])
if mappings:
    # Get second template if available, otherwise first
    template = mappings[1] if len(mappings) > 1 else mappings[0]
    print(template['position'])
")

echo "Will start on Week $POSITION (Template: $TEMPLATE_ID)"
echo ""

# Start schedule on arbitrary week
echo "=== 4. Start on Arbitrary Week ==="
START_RESPONSE=$(curl -s -X POST "$BASE_URL/meal-plans/start-on-week?sequence_id=$SEQUENCE_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"week_template_id\": \"$TEMPLATE_ID\",
    \"position\": $POSITION
  }")

echo "$START_RESPONSE" | python3 -m json.tool
echo ""

# Get current meal plan instance to verify
echo "=== 5. Get Current Meal Plan Instance ==="
CURRENT=$(curl -s -X GET "$BASE_URL/meal-plans/current?sequence_id=$SEQUENCE_ID" \
  -H "Authorization: Bearer $TOKEN")
echo "$CURRENT" | python3 -m json.tool
echo ""

# Test switching to a different week
if [ -n "$POSITION" ] && [ "$POSITION" != "1" ]; then
  echo "=== 6. Switch to Week 1 (Testing Mid-Week Switch) ==="

  # Get first template
  FIRST_TEMPLATE_ID=$(echo "$SEQUENCE" | python3 -c "
import sys, json
seq = json.load(sys.stdin)
mappings = seq.get('week_mappings', [])
if mappings:
    print(mappings[0]['week_template_id'])
")

  SWITCH_RESPONSE=$(curl -s -X POST "$BASE_URL/meal-plans/start-on-week?sequence_id=$SEQUENCE_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
      \"week_template_id\": \"$FIRST_TEMPLATE_ID\",
      \"position\": 1
    }")

  echo "$SWITCH_RESPONSE" | python3 -m json.tool
  echo ""

  # Verify the switch
  echo "=== 7. Verify Switch to Week 1 ==="
  CURRENT_AFTER=$(curl -s -X GET "$BASE_URL/meal-plans/current?sequence_id=$SEQUENCE_ID" \
    -H "Authorization: Bearer $TOKEN")
  echo "$CURRENT_AFTER" | python3 -m json.tool
  echo ""
fi

echo "============================================="
echo "Start on Arbitrary Week Test Completed!"
echo "============================================="
