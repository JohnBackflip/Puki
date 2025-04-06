#!/bin/bash

echo "=== Testing API Endpoints ==="

# 1. Test Price/Events API
echo -e "\n1. Testing Price/Events API"
PRICE_RESULT=$(curl -s http://localhost:5003/price/events)
echo "$PRICE_RESULT" | head -10
if [[ "$PRICE_RESULT" == *"promotions"* ]]; then
  echo "✅ Price/Events API is working"
else
  echo "❌ Price/Events API failed"
fi

# 2. Test Room API
echo -e "\n2. Testing Room API"
ROOM_RESULT=$(curl -s http://localhost:5008/room)
echo "$ROOM_RESULT" | head -10
if [[ "$ROOM_RESULT" == *"rooms"* ]]; then
  echo "✅ Room API is working"
else
  echo "❌ Room API failed"
fi

# 3. Test Room Available API (POST)
echo -e "\n3. Testing Room Available API (POST)"
AVAILABLE_RESULT=$(curl -s -X POST -H "Content-Type: application/json" -d '{"date":"2025-04-10","availability":{"single":5,"double":3,"family":2}}' http://localhost:5008/room/available)
echo "$AVAILABLE_RESULT"
if [[ "$AVAILABLE_RESULT" == *"updated successfully"* ]]; then
  echo "✅ Room Available API is working"
else
  echo "❌ Room Available API failed"
fi

# 4. Test Roster API
echo -e "\n4. Testing Roster API"
TODAY=$(date +%Y-%m-%d)
ROSTER_RESULT=$(curl -s http://localhost:5009/roster/$TODAY)
echo "$ROSTER_RESULT" | head -10
if [[ "$ROSTER_RESULT" == *"roster"* ]] || [[ "$ROSTER_RESULT" == *"code"* ]]; then
  echo "✅ Roster API is working"
else
  echo "❌ Roster API failed"
fi

# 5. Test Admin Frontend 
echo -e "\n5. Testing Admin Frontend Accessibility"
ADMIN_RESULT=$(curl -s -I http://localhost:8888 | head -1)
echo "$ADMIN_RESULT"
if [[ "$ADMIN_RESULT" == *"200 OK"* ]]; then
  echo "✅ Admin Frontend is accessible"
else
  echo "❌ Admin Frontend is not accessible (Status code: $ADMIN_STATUS)"
  echo "Attempting direct connection to admin-frontend container..."
  docker_status=$(docker ps | grep admin-frontend)
  echo "Admin Frontend Container Status: $docker_status"
fi

# 6. Test Frontend
echo -e "\n6. Testing Frontend Accessibility"
FRONTEND_RESULT=$(curl -s -I http://localhost:8080 | head -1)
echo "$FRONTEND_RESULT"
if [[ "$FRONTEND_RESULT" == *"200 OK"* ]]; then
  echo "✅ Frontend is accessible"
else
  echo "❌ Frontend is not accessible (Status code: $FRONTEND_STATUS)"
  echo "Attempting direct connection to frontend container..."
  docker_status=$(docker ps | grep frontend)
  echo "Frontend Container Status: $docker_status"
fi

echo -e "\n=== Testing Complete! ===" 