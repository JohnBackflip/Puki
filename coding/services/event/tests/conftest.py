import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

class MockSession:
    def __init__(self):
        self.events = []
        self.price_adjustments = []
        self.event_counter = 1
        self.adjustment_counter = 1
    
    def add(self, obj):
        if hasattr(obj, "__tablename__"):
            if obj.__tablename__ == "events":
                obj.id = self.event_counter
                self.events.append(obj)
                self.event_counter += 1
            elif obj.__tablename__ == "price_adjustments":
                obj.id = self.adjustment_counter
                self.price_adjustments.append(obj)
                self.adjustment_counter += 1
    
    def commit(self):
        pass
    
    def refresh(self, obj):
        pass
    
    def query(self, model):
        class MockQuery:
            def __init__(self, items):
                self.items = items
            
            def filter(self, *args):
                return self
            
            def first(self):
                return self.items[0] if self.items else None
            
            def all(self):
                return self.items
            
            def offset(self, n):
                return self
            
            def limit(self, n):
                return self
        
        if model.__tablename__ == "events":
            return MockQuery(self.events)
        elif model.__tablename__ == "price_adjustments":
            return MockQuery(self.price_adjustments)
        return MockQuery([])

@pytest.fixture
def mock_session():
    return MockSession()

@pytest.fixture
def mock_db(mock_session):
    def get_mock_db():
        yield mock_session
    return get_mock_db

@pytest.fixture
def auth_header():
    return {"Authorization": "Bearer test_token"}

@pytest.fixture
def mock_auth():
    return {
        "user_id": 1,
        "roles": ["admin"]
    }

@pytest.fixture
def mock_rabbitmq():
    return {
        "exchange": "test_exchange",
        "routing_key": "test_routing_key",
        "message": {"test": "data"}
    } 