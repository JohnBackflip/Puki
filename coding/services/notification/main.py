# notification/main.py
from fastapi import FastAPI, Depends, HTTPException, Security, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict
import httpx
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
import os

from . import models, schemas, database, events
from .database import engine
from middleware.auth import require_auth
from .providers.sms import SMSProvider
from .providers.push import PushNotificationProvider

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
event_publisher = events.EventPublisher()
event_consumer = events.EventConsumer()

sms_provider = SMSProvider()
push_provider = PushNotificationProvider()

async def send_email(notification: models.Notification, recipient_email: str):
    try:
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        
        # Create email message
        msg = MIMEText(notification.data["body"])
        msg["Subject"] = notification.data["subject"]
        msg["From"] = smtp_user
        msg["To"] = recipient_email
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        return True
    
    except Exception as e:
        return False

async def send_notification(notification_id: int, db: Session):
    notification = db.query(models.Notification).filter(
        models.Notification.id == notification_id
    ).first()
    
    if not notification:
        return
    
    try:
        # Get user contact info from auth service
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"http://auth:8000/users/{notification.user_id}",
                headers={"Authorization": f"Bearer {os.getenv('INTERNAL_API_KEY')}"}
            )
            user_data = response.json()
        
        success = False
        if notification.type == models.NotificationType.EMAIL:
            success = await send_email(notification, user_data["email"])
        elif notification.type == models.NotificationType.SMS:
            success = await sms_provider.send_sms(
                user_data["phone"],
                notification.data["message"]
            )
        elif notification.type == models.NotificationType.PUSH:
            success = await push_provider.send_push(
                user_data["push_token"],
                notification.data["title"],
                notification.data["message"],
                notification.data.get("extra_data")
            )
        
        if success:
            notification.status = models.NotificationStatus.SENT
            notification.sent_at = datetime.now()
        else:
            notification.status = models.NotificationStatus.FAILED
            notification.error = "Failed to send notification"
        
    except Exception as e:
        notification.status = models.NotificationStatus.FAILED
        notification.error = str(e)
    
    db.commit()

@app.on_event("startup")
async def startup_event():
    await event_consumer.connect()
    
    async def handle_booking_confirmed(data: dict):
        db = next(database.get_db())
        notification = models.Notification(
            user_id=data["user_id"],
            type=models.NotificationType.EMAIL,
            template_id="booking_confirmation",
            data={
                "subject": "Booking Confirmation",
                "body": f"Your booking #{data['booking_id']} has been confirmed."
            }
        )
        db.add(notification)
        db.commit()
        
        background_tasks = BackgroundTasks()
        background_tasks.add_task(send_notification, notification.id, db)
    
    await event_consumer.subscribe("booking.confirmed", handle_booking_confirmed)

@app.post("/notifications/", response_model=schemas.NotificationResponse)
@require_auth(roles=["staff", "admin"])
async def create_notification(
    notification: schemas.NotificationCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    db_notification = models.Notification(**notification.dict())
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    
    if notification.type == schemas.NotificationType.EMAIL:
        background_tasks.add_task(send_notification, db_notification.id, db)
    
    return db_notification

@app.post("/notifications/bulk", response_model=List[schemas.NotificationResponse])
@require_auth(roles=["staff", "admin"])
async def create_bulk_notifications(
    notifications: List[schemas.NotificationCreate],
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    db_notifications = []
    for notification in notifications:
        db_notification = models.Notification(**notification.dict())
        db.add(db_notification)
        db_notifications.append(db_notification)
    
    db.commit()
    
    for notification in db_notifications:
        background_tasks.add_task(send_notification, notification.id, db)
    
    return db_notifications

@app.post("/notifications/template", response_model=schemas.NotificationResponse)
@require_auth(roles=["staff", "admin"])
async def send_template_notification(
    template_id: str,
    user_id: int,
    data: Dict,
    notification_type: schemas.NotificationType,
    background_tasks: BackgroundTasks,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Get template
    templates = {
        "booking_confirmation": {
            "email": {
                "subject": "Booking Confirmation",
                "body": "Your booking #{booking_id} has been confirmed."
            },
            "sms": {
                "message": "Your booking #{booking_id} at our hotel has been confirmed."
            },
            "push": {
                "title": "Booking Confirmed",
                "message": "Your booking #{booking_id} has been confirmed."
            }
        },
        "check_in_reminder": {
            "email": {
                "subject": "Check-in Reminder",
                "body": "Your check-in for booking #{booking_id} is tomorrow."
            },
            "sms": {
                "message": "Reminder: Your check-in is tomorrow for booking #{booking_id}."
            },
            "push": {
                "title": "Check-in Tomorrow",
                "message": "Your check-in for booking #{booking_id} is tomorrow."
            }
        }
    }
    
    template = templates.get(template_id, {}).get(notification_type)
    if not template:
        raise HTTPException(status_code=400, detail="Template not found")
    
    # Create notification with template
    notification = models.Notification(
        user_id=user_id,
        type=notification_type,
        template_id=template_id,
        data={**template, **data}
    )
    
    db.add(notification)
    db.commit()
    db.refresh(notification)
    
    background_tasks.add_task(send_notification, notification.id, db)
    return notification