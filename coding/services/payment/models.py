# payment/models.py
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from decimal import Decimal

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class PaymentMethod(str, Enum):
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"

class Payment:
    @staticmethod
    def create(cursor, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new payment"""
        if cursor is None:
            # In test mode, return mock data
            mock_payment = {
                "id": 1,
                "booking_id": payment_data["booking_id"],
                "amount": str(payment_data["amount"]),
                "currency": payment_data["currency"],
                "method": payment_data["method"],
                "status": PaymentStatus.PENDING.value,
                "transaction_id": payment_data.get("transaction_id"),
                "metadata": payment_data.get("metadata", {}),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            return mock_payment
            
        query = """
            INSERT INTO payments (booking_id, amount, currency, method, status, transaction_id, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            payment_data["booking_id"],
            str(payment_data["amount"]),
            payment_data["currency"],
            payment_data["method"],
            PaymentStatus.PENDING.value,
            payment_data.get("transaction_id"),
            payment_data.get("metadata", {})
        ))
        
        payment_id = cursor.lastrowid
        return Payment.get_by_id(cursor, payment_id)
    
    @staticmethod
    def get_by_id(cursor, payment_id: int) -> Optional[Dict[str, Any]]:
        """Get a payment by ID"""
        if cursor is None:
            # In test mode, return mock data
            return {
                "id": payment_id,
                "booking_id": 1,
                "amount": "100.00",
                "currency": "USD",
                "method": PaymentMethod.CREDIT_CARD.value,
                "status": PaymentStatus.COMPLETED.value,
                "transaction_id": "test_transaction",
                "metadata": {},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
        query = "SELECT * FROM payments WHERE id = %s"
        cursor.execute(query, (payment_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                "id": result[0],
                "booking_id": result[1],
                "amount": result[2],
                "currency": result[3],
                "method": result[4],
                "status": result[5],
                "transaction_id": result[6],
                "metadata": result[7],
                "created_at": result[8],
                "updated_at": result[9]
            }
        return None
    
    @staticmethod
    def get_by_booking(cursor, booking_id: int) -> List[Dict[str, Any]]:
        """Get all payments for a booking"""
        if cursor is None:
            # In test mode, return mock data
            return [{
                "id": 1,
                "booking_id": booking_id,
                "amount": "100.00",
                "currency": "USD",
                "method": PaymentMethod.CREDIT_CARD.value,
                "status": PaymentStatus.COMPLETED.value,
                "transaction_id": "test_transaction",
                "metadata": {},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }]
            
        query = "SELECT * FROM payments WHERE booking_id = %s ORDER BY created_at DESC"
        cursor.execute(query, (booking_id,))
        results = cursor.fetchall()
        
        return [{
            "id": row[0],
            "booking_id": row[1],
            "amount": row[2],
            "currency": row[3],
            "method": row[4],
            "status": row[5],
            "transaction_id": row[6],
            "metadata": row[7],
            "created_at": row[8],
            "updated_at": row[9]
        } for row in results]
    
    @staticmethod
    def update_status(cursor, payment_id: int, status: str, transaction_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update payment status and transaction ID"""
        if cursor is None:
            # In test mode, return mock data
            return {
                "id": payment_id,
                "booking_id": 1,
                "amount": "100.00",
                "currency": "USD",
                "method": PaymentMethod.CREDIT_CARD.value,
                "status": status,
                "transaction_id": transaction_id or "test_transaction",
                "metadata": {},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
        query = """
            UPDATE payments 
            SET status = %s, transaction_id = %s, updated_at = NOW()
            WHERE id = %s
        """
        cursor.execute(query, (status, transaction_id, payment_id))
        
        if cursor.rowcount > 0:
            return Payment.get_by_id(cursor, payment_id)
        return None
    
    @staticmethod
    def delete(cursor, payment_id: int) -> bool:
        """Delete a payment"""
        if cursor is None:
            # In test mode, return success
            return True
            
        query = "DELETE FROM payments WHERE id = %s"
        cursor.execute(query, (payment_id,))
        return cursor.rowcount > 0