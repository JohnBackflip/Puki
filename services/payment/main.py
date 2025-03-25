# payment/main.py
from fastapi import FastAPI, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List
import stripe
from . import models, schemas, database, events
from .database import engine
from .payment_providers import stripe_provider
from middleware.auth import require_auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
event_publisher = events.EventPublisher()

@app.post("/payments/", response_model=schemas.PaymentResponse)
@require_auth()
async def create_payment(
    payment: schemas.PaymentCreate,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Create payment intent with Stripe
    if payment.payment_method == schemas.PaymentMethod.STRIPE:
        intent = await stripe_provider.create_payment_intent(
            payment.amount,
            payment.currency
        )
        
        # Create payment record
        db_payment = models.Payment(
            booking_id=payment.booking_id,
            amount=payment.amount,
            currency=payment.currency,
            status=models.PaymentStatus.PENDING,
            payment_method=payment.payment_method,
            payment_intent_id=intent.id
        )
        
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        
        # Publish payment created event
        await event_publisher.publish(
            "payment.created",
            {
                "payment_id": db_payment.id,
                "booking_id": db_payment.booking_id,
                "status": db_payment.status.value
            }
        )
        
        return db_payment

@app.post("/payments/{payment_id}/confirm")
@require_auth()
async def confirm_payment(
    payment_id: int,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    if payment.payment_method == schemas.PaymentMethod.STRIPE:
        success = await stripe_provider.confirm_payment(payment.payment_intent_id)
        if success:
            payment.status = models.PaymentStatus.COMPLETED
            db.commit()
            
            # Publish payment confirmed event
            await event_publisher.publish(
                "payment.confirmed",
                {
                    "payment_id": payment.id,
                    "booking_id": payment.booking_id
                }
            )
            
            return {"status": "success"}
    
    raise HTTPException(status_code=400, detail="Payment confirmation failed")