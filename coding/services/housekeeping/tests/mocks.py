from unittest.mock import MagicMock
from functools import wraps
from fastapi import Security, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Mock Prometheus metrics
REQUEST_COUNT = MagicMock()
TASK_STATUS_GAUGE = MagicMock()

# Mock request tracking
def track_request(path=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)
        return wrapper
    if callable(path):
        return decorator(path)
    return decorator

# Mock tracing
def setup_tracing(app=None, name=None):
    pass

# Mock auth
oauth2_scheme = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(oauth2_scheme)):
    # Mock user data
    return {
        "id": "test_user_id",
        "roles": ["staff", "admin"]
    }

def require_auth(roles=None):
    if roles is None:
        return Depends(get_current_user)

    def verify_roles(user_data: dict = Depends(get_current_user)):
        if not any(role in user_data["roles"] for role in roles):
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user_data

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user_data = await get_current_user(None)
            if not any(role in user_data["roles"] for role in roles):
                raise HTTPException(status_code=403, detail="Not enough permissions")
            return await func(*args, **kwargs)
        return wrapper

    return decorator

# Mock database
class MockCursor:
    def __init__(self, dictionary=False):
        self.dictionary = dictionary
        self.rows = []
        self.current_row = 0
        
    def execute(self, query, params=None):
        return self
        
    def fetchone(self):
        if self.current_row < len(self.rows):
            row = self.rows[self.current_row]
            self.current_row += 1
            return row
        return None
        
    def fetchall(self):
        return self.rows
        
    def close(self):
        pass

class MockConnection:
    def __init__(self):
        self.is_connected_val = True
        
    def cursor(self, dictionary=False):
        return MockCursor(dictionary)
        
    def commit(self):
        pass
        
    def rollback(self):
        pass
        
    def close(self):
        self.is_connected_val = False
        
    def is_connected(self):
        return self.is_connected_val

def get_db():
    return MockConnection()

def init_db():
    pass

def run_migrations():
    pass 