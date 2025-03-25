import pytest
from datetime import datetime
from ..models import Payment, PaymentStatus, PaymentMethod

def test_payment_creation(mock_cursor):
    # Test data
    payment_data = {
        "booking_id": 1,
        "amount": 100.00,
        "currency": "USD",
        "status": PaymentStatus.PENDING.value,
        "payment_method": PaymentMethod.CREDIT_CARD.value,
        "transaction_id": None,
        "payment_details": {"card_last4": "4242"}
    }
    
    # Create payment
    payment = Payment.create(mock_cursor, payment_data)
    
    # Assertions
    assert payment["id"] == 1
    assert payment["booking_id"] == payment_data["booking_id"]
    assert payment["amount"] == payment_data["amount"]
    assert payment["currency"] == payment_data["currency"]
    assert payment["status"] == payment_data["status"]
    assert payment["payment_method"] == payment_data["payment_method"]
    assert payment["payment_details"] == payment_data["payment_details"]

def test_payment_retrieval(mock_cursor):
    # Create test payment
    payment_data = {
        "booking_id": 1,
        "amount": 100.00,
        "currency": "USD",
        "status": PaymentStatus.PENDING.value,
        "payment_method": PaymentMethod.CREDIT_CARD.value,
        "transaction_id": None,
        "payment_details": {"card_last4": "4242"}
    }
    payment = Payment.create(mock_cursor, payment_data)
    
    # Test retrieval
    retrieved_payment = Payment.get_by_id(mock_cursor, payment["id"])
    assert retrieved_payment == payment

def test_payment_status_update(mock_cursor):
    # Create test payment
    payment_data = {
        "booking_id": 1,
        "amount": 100.00,
        "currency": "USD",
        "status": PaymentStatus.PENDING.value,
        "payment_method": PaymentMethod.CREDIT_CARD.value,
        "transaction_id": None,
        "payment_details": {"card_last4": "4242"}
    }
    payment = Payment.create(mock_cursor, payment_data)
    
    # Update status
    updated_payment = Payment.update_status(
        mock_cursor,
        payment["id"],
        PaymentStatus.COMPLETED.value,
        "test_transaction_id"
    )
    assert updated_payment["status"] == PaymentStatus.COMPLETED.value
    assert updated_payment["transaction_id"] == "test_transaction_id"

def test_payment_by_booking(mock_cursor):
    # Create test payments
    payments = [
        Payment.create(mock_cursor, {
            "booking_id": 1,
            "amount": 100.00,
            "currency": "USD",
            "status": PaymentStatus.PENDING.value,
            "payment_method": PaymentMethod.CREDIT_CARD.value,
            "transaction_id": None,
            "payment_details": {"card_last4": "4242"}
        }),
        Payment.create(mock_cursor, {
            "booking_id": 2,
            "amount": 200.00,
            "currency": "USD",
            "status": PaymentStatus.COMPLETED.value,
            "payment_method": PaymentMethod.DEBIT_CARD.value,
            "transaction_id": "test_id",
            "payment_details": {"card_last4": "8888"}
        })
    ]
    
    # Test retrieval by booking
    booking_payments = Payment.get_by_booking(mock_cursor, 1)
    assert len(booking_payments) == 1
    assert booking_payments[0]["booking_id"] == 1 