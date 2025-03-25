from fastapi import FastAPI, Depends, HTTPException, Security, BackgroundTasks
from typing import List
import httpx
import json
import os
from prometheus_client import Counter, Histogram, start_http_server

from application import models, schemas, database
from configuration.events import event_publisher, event_consumer
from middleware.auth import require_auth
from monitoring.tracing import setup_tracing

# Initialize database
database.init_db()

# Prometheus metrics
REVIEW_COUNT = Counter(
    'review_total',
    'Total number of reviews',
    ['rating']
)

RESPONSE_TIME = Histogram(
    'review_response_time_seconds',
    'Time taken to respond to reviews',
    ['endpoint']
)

SENTIMENT_SCORE = Histogram(
    'review_sentiment_score',
    'Distribution of review sentiment scores'
)

app = FastAPI(title="Feedback Service")

# Setup tracing
setup_tracing(app, "feedback-service")

# Start Prometheus metrics server
start_http_server(8000)

@app.post("/reviews/", response_model=schemas.Review)
@require_auth()
@RESPONSE_TIME.time()
async def create_review(
    review: schemas.ReviewCreate,
    background_tasks: BackgroundTasks,
    cursor = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Create review
    db_review = models.Review.create(
        cursor,
        review.booking_id,
        user_data["user_id"],
        review.rating,
        review.comment
    )
    
    # Update metrics
    REVIEW_COUNT.labels(rating=review.rating).inc()
    
    # Get sentiment score
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://ml:8000/analyze/sentiment",
            json={"text": review.comment},
            headers={"Authorization": f"Bearer {user_data['token']}"}
        )
        sentiment_data = response.json()
        SENTIMENT_SCORE.observe(sentiment_data["score"])
        
        # Save sentiment score
        models.ReviewMetrics.create(cursor, db_review["id"], sentiment_data["score"])
    
    # Publish event
    background_tasks.add_task(
        event_publisher.publish,
        "review.created",
        {
            "review_id": db_review["id"],
            "rating": db_review["rating"],
            "sentiment_score": sentiment_data["score"]
        }
    )
    
    return db_review

@app.get("/reviews/", response_model=List[schemas.Review])
@require_auth()
@RESPONSE_TIME.time()
async def list_reviews(
    skip: int = 0,
    limit: int = 100,
    cursor = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    reviews = models.Review.list_reviews(cursor, skip, limit)
    return reviews

@app.post("/reviews/{review_id}/respond", response_model=schemas.Response)
@require_auth(roles=["staff", "admin"])
@RESPONSE_TIME.time()
async def create_response(
    review_id: int,
    response: schemas.ResponseCreate,
    background_tasks: BackgroundTasks,
    cursor = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Check if review exists
    review = models.Review.get_by_id(cursor, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Create response
    db_response = models.Response.create(
        cursor,
        review_id,
        user_data["user_id"],
        response.comment
    )
    
    # Publish event
    background_tasks.add_task(
        event_publisher.publish,
        "review.responded",
        {
            "review_id": review_id,
            "response_id": db_response["id"],
            "staff_id": user_data["user_id"]
        }
    )
    
    return db_response

@app.get("/metrics/", response_model=schemas.ReviewMetrics)
@require_auth(roles=["staff", "admin"])
@RESPONSE_TIME.time()
async def get_metrics(
    cursor = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    metrics = models.ReviewMetrics.get_aggregate_metrics(cursor)
    return metrics

@app.get("/reviews/{review_id}/sentiment")
@require_auth()
async def get_review_sentiment(
    review_id: int,
    cursor = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    review = models.Review.get_by_id(cursor, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Call ML service for sentiment analysis
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://ml:8000/analyze/sentiment",
            json={"text": review.comment},
            headers={"Authorization": f"Bearer {user_data['token']}"}
        )
        return response.json()

# Event handlers
async def handle_booking_completed(data: dict):
    # Send notification to user requesting feedback
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://notification:8000/notifications/",
            json={
                "user_id": data["user_id"],
                "type": "email",
                "template_id": "request_feedback",
                "data": {"booking_id": data["booking_id"]}
            },
            headers={"Authorization": f"Bearer {os.getenv('INTERNAL_API_KEY')}"}
        )

@app.on_event("startup")
async def startup_event():
    # Subscribe to booking completed events
    await event_consumer.subscribe("booking.completed", handle_booking_completed)