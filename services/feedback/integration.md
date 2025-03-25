# Feedback Service Integration Guide

## Overview
The Feedback Service integrates with multiple services in the hotel management system to provide a comprehensive feedback management solution.

## Service Dependencies

### 1. User Service
- **Purpose**: Authentication and user information
- **Integration Type**: REST API
- **Endpoints Used**:
  - `GET /users/{user_id}`: Get user details
  - `POST /token`: Authenticate requests

### 2. Booking Service
- **Purpose**: Link reviews to bookings
- **Integration Type**: Event-driven (RabbitMQ)
- **Events**:
  - Subscribes to: `booking.completed`
  - Data Format:
    ```json
    {
      "booking_id": 123,
      "user_id": 456,
      "room_id": 789,
      "check_out_date": "2025-03-22T10:00:00Z"
    }
    ```

### 3. ML Service
- **Purpose**: Sentiment analysis and analytics
- **Integration Type**: REST API
- **Endpoints Used**:
  - `POST /analyze/sentiment`: Analyze review text
  - Request Format:
    ```json
    {
      "text": "Great service and clean rooms!"
    }
    ```

### 4. Notification Service
- **Purpose**: Send feedback requests and notifications
- **Integration Type**: REST API
- **Endpoints Used**:
  - `POST /notifications/`: Send feedback request
  - Request Format:
    ```json
    {
      "user_id": 123,
      "type": "email",
      "template_id": "request_feedback",
      "data": {
        "booking_id": 456
      }
    }
    ```

### 5. Analytics Service
- **Purpose**: Review metrics and insights
- **Integration Type**: Event-driven (RabbitMQ)
- **Events Published**:
  ```json
  {
    "event": "review.metrics.updated",
    "data": {
      "average_rating": 4.5,
      "total_reviews": 100,
      "sentiment_score": 0.75
    }
  }
  ```

## Environment Variables
```env
DATABASE_URL=postgresql://user:password@localhost/feedback_db
RABBITMQ_URL=amqp://user:password@localhost:5672/
INTERNAL_API_KEY=your_internal_api_key
ML_SERVICE_URL=http://ml:8000
NOTIFICATION_SERVICE_URL=http://notification:8000
USER_SERVICE_URL=http://user:8000
```

## Event Schema

### Published Events

#### review.created
```json
{
  "review_id": 123,
  "booking_id": 456,
  "rating": "FIVE",
  "timestamp": "2025-03-22T09:00:00Z"
}
```

#### review.responded
```json
{
  "review_id": 123,
  "response_id": 789,
  "staff_id": 456,
  "timestamp": "2025-03-22T10:00:00Z"
}
```

## Error Handling
1. Service Unavailability
   - Implement circuit breakers for external service calls
   - Queue failed events for retry
   - Log service failures for monitoring

2. Data Consistency
   - Validate booking existence before creating review
   - Ensure user permissions before processing requests
   - Handle duplicate review submissions

## Deployment Dependencies
```yaml
version: '3'
services:
  feedback:
    build: .
    depends_on:
      - postgres
      - rabbitmq
    environment:
      - DATABASE_URL=postgresql://user:password@postgres:5432/feedback_db
      - RABBITMQ_URL=amqp://user:password@rabbitmq:5672/
```

## Monitoring
1. Metrics to Track:
   - Review submission rate
   - Average response time
   - Service integration success rate
   - Event processing latency

2. Health Checks:
   - Database connectivity
   - RabbitMQ connection
   - External service availability