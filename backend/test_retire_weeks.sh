#!/bin/bash
set -e

API_URL="http://localhost:8000"

echo "=== Testing Week Template Retire/Restore Functionality ==="
echo ""

# Step 1: Register and login
echo "1. Registering test user..."
REGISTER_RESPONSE=$(curl -s -X POST "$API_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"retiretest","password":"testpass123"}')
echo "Register response: $REGISTER_RESPONSE"
echo ""

echo "2. Logging in..."
TOKEN=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=retiretest&password=testpass123" | jq -r '.access_token')
echo "Token: ${TOKEN:0:20}..."
echo ""

# Step 2: Create a schedule sequence
echo "3. Creating schedule sequence..."
SEQUENCE=$(curl -s -X POST "$API_URL/schedules" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Retire Test Schedule",
    "advancement_day_of_week": 0,
    "advancement_time": "00:00"
  }')
SEQUENCE_ID=$(echo $SEQUENCE | jq -r '.id')
echo "Created sequence: $SEQUENCE_ID"
echo ""

# Step 3: Get current user ID
echo "4. Getting current user..."
USER=$(curl -s -X GET "$API_URL/me" \
  -H "Authorization: Bearer $TOKEN")
USER_ID=$(echo $USER | jq -r '.id')
echo "User ID: $USER_ID"
echo ""

# Step 4: Create a week template
echo "5. Creating week template..."
WEEK=$(curl -s -X POST "$API_URL/schedules/$SEQUENCE_ID/weeks" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"theme_name\": \"Test Week\",
    \"assignments\": [{
      \"day_of_week\": 0,
      \"assigned_user_id\": \"$USER_ID\",
      \"action\": \"rest\",
      \"order\": 0
    }]
  }")
WEEK_ID=$(echo $WEEK | jq -r '.id')
echo "Created week: $WEEK_ID"
echo "Week details: $(echo $WEEK | jq '.theme_name, .retired_at')"
echo ""

# Step 5: Retire the week
echo "6. Retiring week template..."
RETIRED_WEEK=$(curl -s -X DELETE "$API_URL/schedules/$SEQUENCE_ID/weeks/$WEEK_ID" \
  -H "Authorization: Bearer $TOKEN")
echo "Retired week details: $(echo $RETIRED_WEEK | jq '.theme_name, .retired_at')"
RETIRED_AT=$(echo $RETIRED_WEEK | jq -r '.retired_at')
if [ "$RETIRED_AT" != "null" ]; then
  echo "✓ Week successfully retired at: $RETIRED_AT"
else
  echo "✗ Week was NOT retired (retired_at is null)"
fi
echo ""

# Step 6: List weeks without retired
echo "7. Listing weeks (include_retired=false)..."
WEEKS_NO_RETIRED=$(curl -s -X GET "$API_URL/schedules/$SEQUENCE_ID/weeks?include_retired=false" \
  -H "Authorization: Bearer $TOKEN")
COUNT_NO_RETIRED=$(echo $WEEKS_NO_RETIRED | jq 'length')
echo "Number of active weeks: $COUNT_NO_RETIRED"
if [ "$COUNT_NO_RETIRED" == "0" ]; then
  echo "✓ Retired week is correctly excluded from active list"
else
  echo "✗ Retired week is still showing in active list"
fi
echo ""

# Step 7: List weeks with retired
echo "8. Listing weeks (include_retired=true)..."
WEEKS_WITH_RETIRED=$(curl -s -X GET "$API_URL/schedules/$SEQUENCE_ID/weeks?include_retired=true" \
  -H "Authorization: Bearer $TOKEN")
COUNT_WITH_RETIRED=$(echo $WEEKS_WITH_RETIRED | jq 'length')
echo "Number of total weeks: $COUNT_WITH_RETIRED"
if [ "$COUNT_WITH_RETIRED" == "1" ]; then
  echo "✓ Retired week is correctly included when requested"
else
  echo "✗ Expected 1 week, got $COUNT_WITH_RETIRED"
fi
echo ""

# Step 8: Restore the week
echo "9. Restoring week template..."
RESTORED_WEEK=$(curl -s -X POST "$API_URL/schedules/$SEQUENCE_ID/weeks/$WEEK_ID/restore" \
  -H "Authorization: Bearer $TOKEN")
echo "Restored week details: $(echo $RESTORED_WEEK | jq '.theme_name, .retired_at')"
RESTORED_AT=$(echo $RESTORED_WEEK | jq -r '.retired_at')
if [ "$RESTORED_AT" == "null" ]; then
  echo "✓ Week successfully restored (retired_at is null)"
else
  echo "✗ Week was NOT restored (retired_at is still set)"
fi
echo ""

# Step 9: List weeks after restore
echo "10. Listing weeks after restore (include_retired=false)..."
WEEKS_AFTER_RESTORE=$(curl -s -X GET "$API_URL/schedules/$SEQUENCE_ID/weeks?include_retired=false" \
  -H "Authorization: Bearer $TOKEN")
COUNT_AFTER_RESTORE=$(echo $WEEKS_AFTER_RESTORE | jq 'length')
echo "Number of active weeks: $COUNT_AFTER_RESTORE"
if [ "$COUNT_AFTER_RESTORE" == "1" ]; then
  echo "✓ Restored week is back in active list"
else
  echo "✗ Expected 1 week, got $COUNT_AFTER_RESTORE"
fi
echo ""

echo "=== Test Complete ==="
