# housekeeping/main.py
from fastapi import FastAPI, Depends, HTTPException, Security, BackgroundTasks
from typing import List, Optional
from datetime import datetime
import json
import aio_pika
import os
from prometheus_client import make_asgi_app

from . import models, schemas
from .database import get_db, init_db, run_migrations
from middleware.auth import require_auth
from monitoring.prometheus import track_request, REQUEST_COUNT, TASK_STATUS_GAUGE
from monitoring.tracing import setup_tracing

app = FastAPI(title="Housekeeping Service")
setup_tracing(app, "housekeeping-service")

# Add prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# RabbitMQ configuration
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
RABBITMQ_PASS = os.getenv("RABBITMQ_PASS", "guest")

# Initialize database
init_db()
run_migrations()

# RabbitMQ connection and channel
connection = None
channel = None

async def get_rabbitmq_channel():
    global connection, channel
    if not connection or connection.is_closed:
        connection = await aio_pika.connect_robust(
            host=RABBITMQ_HOST,
            login=RABBITMQ_USER,
            password=RABBITMQ_PASS
        )
        channel = await connection.channel()
        await channel.declare_exchange("housekeeping_events", aio_pika.ExchangeType.TOPIC)
    return channel

async def publish_event(routing_key: str, message: dict):
    channel = await get_rabbitmq_channel()
    exchange = await channel.get_exchange("housekeeping_events")
    await exchange.publish(
        aio_pika.Message(body=json.dumps(message).encode()),
        routing_key=routing_key
    )

@app.on_event("startup")
async def startup_event():
    # Initialize RabbitMQ connection
    await get_rabbitmq_channel()
    
    # Initialize task status metrics
    cursor = next(get_db())
    for status in models.CleaningStatus:
        cursor.execute(
            "SELECT COUNT(*) as count FROM cleaning_tasks WHERE status = %s",
            (status.value,)
        )
        count = cursor.fetchone()["count"]
        TASK_STATUS_GAUGE.labels(status=status.value).set(count)

@app.on_event("shutdown")
async def shutdown_event():
    if connection and not connection.is_closed:
        await connection.close()

@app.post("/tasks/", response_model=schemas.CleaningTask)
@require_auth(roles=["staff", "admin"])
@track_request()
async def create_task(
    task: schemas.CleaningTaskCreate,
    background_tasks: BackgroundTasks,
    cursor = Depends(get_db),
    user_data: dict = Security(require_auth())
):
    db_task = models.CleaningTask.create(
        cursor,
        task.room_id,
        task.scheduled_at,
        task.notes
    )
    
    # Update metrics
    TASK_STATUS_GAUGE.labels(status="pending").inc()
    
    # Publish task created event
    background_tasks.add_task(
        publish_event,
        "task.created",
        {
            "task_id": db_task["id"],
            "room_id": db_task["room_id"],
            "scheduled_at": db_task["scheduled_at"].isoformat()
        }
    )
    
    return db_task

@app.get("/tasks/", response_model=List[schemas.CleaningTask])
@require_auth()
@track_request()
async def list_tasks(
    skip: int = 0,
    limit: int = 100,
    status: Optional[models.CleaningStatus] = None,
    staff_id: Optional[int] = None,
    cursor = Depends(get_db),
    user_data: dict = Security(require_auth())
):
    if staff_id:
        return models.CleaningTask.list_by_staff(cursor, staff_id, skip, limit)
    elif status:
        return models.CleaningTask.list_by_status(cursor, status, skip, limit)
    else:
        return models.CleaningTask.list_all(cursor, skip, limit)

@app.get("/tasks/{task_id}", response_model=schemas.CleaningTask)
@require_auth()
@track_request()
async def get_task(
    task_id: int,
    cursor = Depends(get_db),
    user_data: dict = Security(require_auth())
):
    task = models.CleaningTask.get_by_id(cursor, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}/status", response_model=schemas.CleaningTask)
@require_auth(roles=["staff"])
@track_request()
async def update_task_status(
    task_id: int,
    status: models.CleaningStatus,
    background_tasks: BackgroundTasks,
    cursor = Depends(get_db),
    user_data: dict = Security(require_auth())
):
    task = models.CleaningTask.get_by_id(cursor, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    updated_task = models.CleaningTask.update_status(
        cursor,
        task_id,
        status,
        user_data.get("id") if status == models.CleaningStatus.IN_PROGRESS else None
    )
    
    if not updated_task:
        raise HTTPException(status_code=400, detail="Failed to update task status")
    
    # Update metrics
    TASK_STATUS_GAUGE.labels(status=task["status"]).dec()
    TASK_STATUS_GAUGE.labels(status=status.value).inc()
    
    # Publish status updated event
    background_tasks.add_task(
        publish_event,
        "task.status_updated",
        {
            "task_id": updated_task["id"],
            "room_id": updated_task["room_id"],
            "status": updated_task["status"],
            "staff_id": updated_task["staff_id"]
        }
    )
    
    return updated_task

@app.put("/tasks/{task_id}/notes", response_model=schemas.CleaningTask)
@require_auth(roles=["staff"])
@track_request()
async def update_task_notes(
    task_id: int,
    notes: str,
    cursor = Depends(get_db),
    user_data: dict = Security(require_auth())
):
    task = models.CleaningTask.get_by_id(cursor, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    updated_task = models.CleaningTask.update_notes(cursor, task_id, notes)
    if not updated_task:
        raise HTTPException(status_code=400, detail="Failed to update task notes")
    
    return updated_task