#!/bin/bash

KONG_ADMIN_URL=http://localhost:8021

declare -A services=(
  [housekeeping-service]="http://housekeeping_service:8000"
  [auth-service]="http://auth_service:8000"
  [checkin-service]="http://checkin_service:8000"
  [payment-service]="http://payment_service:8000"
  [security-service]="http://security_service:8000"
  [notification-service]="http://notification_service:8000"
  [price-service]="http://price_service:8000"
  [roster-service]="http://roster_service:8000"
  [booking-service]="http://booking_service:8000"
  [room-service]="http://room_service:8000"
  [guest-service]="http://guest_service:8000"
)

for service in "${!services[@]}"; do
  url="${services[$service]}"
  route_name="${service//service/route}"
  path="/${service%%-*}"

  # Check if service exists
  if curl -s -o /dev/null -w "%{http_code}" "$KONG_ADMIN_URL/services/$service" | grep -q 200; then
    echo "🔁 Skipping existing: $service"
    continue
  fi

  echo "Registering $service at $url"

  # Create service
  curl -s -X POST "$KONG_ADMIN_URL/services" \
    --data name="$service" \
    --data url="$url"

  # Create route
  curl -s -X POST "$KONG_ADMIN_URL/services/$service/routes" \
    --data name="$route_name" \
    --data paths[]="$path" \
    --data strip_path=true

  echo "✅ Registered: $service → $path"
done
