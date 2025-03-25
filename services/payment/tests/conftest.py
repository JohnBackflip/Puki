import pytest
from datetime import datetime
from typing import Dict, Any

class MockCursor:
    def __init__(self):
        self.payments = []
        self.refunds = []
        
    def execute(self, query: str, params: tuple = None):
        if "INSERT INTO payments" in query:
            payment_id = len(self.payments) + 1
            self.payments.append({
                "id": payment_id,
                "booking_id": params[0],
                "amount": params[1],
                "currency": params[2],
                "status": params[3],
                "payment_method": params[4],
                "transaction_id": params[5],
                "payment_details": params[6],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            self.lastrowid = payment_id
        elif "INSERT INTO refunds" in query:
            refund_id = len(self.refunds) + 1
            self.refunds.append({
                "id": refund_id,
                "payment_id": params[0],
                "amount": params[1],
                "reason": params[2],
                "status": params[3],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            self.lastrowid = refund_id
        elif "SELECT * FROM payments" in query:
            if "WHERE id = %s" in query:
                self._last_result = [p for p in self.payments if p["id"] == params[0]]
            elif "WHERE booking_id = %s" in query:
                self._last_result = [p for p in self.payments if p["booking_id"] == params[0]]
            else:
                self._last_result = self.payments
        elif "SELECT * FROM refunds" in query:
            if "WHERE id = %s" in query:
                self._last_result = [r for r in self.refunds if r["id"] == params[0]]
            elif "WHERE payment_id = %s" in query:
                self._last_result = [r for r in self.refunds if r["payment_id"] == params[0]]
            else:
                self._last_result = self.refunds
        elif "UPDATE payments" in query:
            for payment in self.payments:
                if payment["id"] == params[1]:
                    payment["status"] = params[0]
                    payment["transaction_id"] = params[2]
                    break
            self.rowcount = 1
        elif "UPDATE refunds" in query:
            for refund in self.refunds:
                if refund["id"] == params[1]:
                    refund["status"] = params[0]
                    break
            self.rowcount = 1
        elif "DELETE FROM payments" in query:
            self.payments = [p for p in self.payments if p["id"] != params[0]]
            self.rowcount = 1
        elif "DELETE FROM refunds" in query:
            self.refunds = [r for r in self.refunds if r["id"] != params[0]]
            self.rowcount = 1
    
    def fetchone(self):
        if hasattr(self, '_last_result'):
            return self._last_result[0] if self._last_result else None
        return None
    
    def fetchall(self):
        if hasattr(self, '_last_result'):
            return self._last_result
        return []

@pytest.fixture
def mock_cursor():
    return MockCursor()

@pytest.fixture
def auth_header():
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def mock_auth():
    return {
        "user_id": 1,
        "roles": ["user"]
    }

@pytest.fixture
def mock_rabbitmq():
    return {
        "exchange": "test_exchange",
        "routing_key": "test_routing_key",
        "message": {"test": "data"}
    } 