# payment/payment_providers/stripe_provider.py
import stripe
from fastapi import HTTPException
import os

stripe.api_key = os.getenv("STRIPE_API_KEY")

async def create_payment_intent(amount: float, currency: str):
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(amount * 100),  # Convert to cents
            currency=currency,
            automatic_payment_methods={"enabled": True}
        )
        return intent
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

async def confirm_payment(payment_intent_id: str):
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        return intent.status == "succeeded"
    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))