# Feedback Service API Documentation

## Overview
The Feedback Service manages hotel guest reviews, staff responses, and feedback analytics. It integrates with the ML service for sentiment analysis and the notification service for automated feedback requests.

## Authentication
All endpoints require authentication using JWT tokens. Include the token in the Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### Create Review
```http
POST /reviews/
```

Creates a new review for a booking.

**Request Body:**
```json
{
  "booking_id": 1,
  "rating": "FIVE",
  "comment": "Excellent service and very clean rooms!"
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "booking_id": 1,
  "user_id": 123,
  "rating": "FIVE",
  "comment": "Excellent service and very clean rooms!",
  "status": "pending",
  "created_at": "2025-03-22T09:00:00Z",
  "updated_at": null,
  "responses": []
}
```

### List Reviews
```http
GET /reviews/
```

Lists all reviews with optional pagination.

**Query Parameters:**
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum number of records to return (default: 100)

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "booking_id": 1,
    "user_id": 123,
    "rating": "FIVE",
    "comment": "Excellent service!",
    "status": "pending",
    "created_at": "2025-03-22T09:00:00Z",
    "responses": []
  }
]
```

### Create Response
```http
POST /reviews/{review_id}/respond
```

Staff response to a review.

**Path Parameters:**
- `review_id`: ID of the review

**Request Body:**
```json
{
  "comment": "Thank you for your feedback! We're glad you enjoyed your stay."
}
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "review_id": 1,
  "staff_id": 456,
  "comment": "Thank you for your feedback!",
  "created_at": "2025-03-22T10:00:00Z"
}
```

### Get Review Metrics
```http
GET /metrics/
```

Retrieves aggregated review metrics.

**Response:** `200 OK`
```json
{
  "id": 1,
  "date": "2025-03-22",
  "average_rating": 4.5,
  "total_reviews": 100,
  "rating_distribution": "{\"1\":5,\"2\":10,\"3\":15,\"4\":30,\"5\":40}",
  "sentiment_score": 0.75
}
```

### Get Review Sentiment
```http
GET /reviews/{review_id}/sentiment
```

Gets sentiment analysis for a specific review.

**Path Parameters:**
- `review_id`: ID of the review

**Response:** `200 OK`
```json
{
  "sentiment": "positive",
  "score": 0.85,
  "keywords": ["excellent", "clean", "friendly"]
}
```

## Events

### Published Events
- `review.created`: When a new review is created
- `review.responded`: When staff responds to a review

### Subscribed Events
- `booking.completed`: Triggers feedback request notification

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid review data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Review not found"
}