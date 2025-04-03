#!/usr/local/bin/bash

# Kong proxy URL
KONG_PROXY_URL=http://localhost:8022

# Use associative array
declare -A services=(
  [housekeeping-service]="/housekeeping"
  [auth-service]="/auth"
  [checkin-service]="/checkin"
  [payment-service]="/payment"
  [security-service]="/security"
  [notification-service]="/notification"
  [price-service]="/price"
  [roster-service]="/roster"
  [booking-service]="/booking"
  [room-service]="/room"
  [guest-service]="/guest"
)

echo "🧪 Testing Kong routes..."

for service in "${!services[@]}"; do
  path="${services[$service]}"
  full_url="${KONG_PROXY_URL}${path}"

  echo -n "🔍 Testing $service (${full_url}) ... "

  status_code=$(curl -s -o /dev/null -w "%{http_code}" "$full_url")

  if [[ "$status_code" =~ ^2|3 ]]; then
    echo "✅ SUCCESS (HTTP $status_code)"
  else
    echo "❌ FAILED (HTTP $status_code)"
  fi
done

echo "🧪 Testing completed."
