#!/bin/bash

# List of services
services=(
    "room"
    "feedback"
    "booking"
    "housekeeping"
    "monitoring"
    "notification"
    "analytics"
    "security"
    "ml"
    "payment"
    "user"
    "staff"
    "promotion"
    "auth"
)

# Copy Dockerfile and requirements.txt to each service
for service in "${services[@]}"; do
    if [ -d "services/$service" ]; then
        echo "Setting up $service service..."
        cp services/booking/Dockerfile services/$service/
        cp services/booking/requirements.txt services/$service/
    fi
done

echo "✅ Setup completed!" 