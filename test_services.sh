#!/bin/bash

# Exit on error
set -e

echo "🚀 Starting test process..."

# Install required dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov

# Start required services
echo "🏗️ Starting services..."
docker-compose -f docker-compose.yaml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Function to run tests for a service
run_service_tests() {
    local service=$1
    echo "🧪 Testing $service service..."
    cd services/$service
    pytest tests/ -v --cov=. --cov-report=term-missing
    cd ../..
}

# Run tests for each service
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
    "a"
)

for service in "${services[@]}"; do
    if [ -d "services/$service/tests" ]; then
        run_service_tests $service
    else
        echo "⚠️ No tests found for $service service"
    fi
done

echo "✅ Test process completed!"

# Optional: Stop services
# echo "🛑 Stopping services..."
# docker-compose -f docker-compose.yaml down 