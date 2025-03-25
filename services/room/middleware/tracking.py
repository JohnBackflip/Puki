from functools import wraps
from fastapi import Request, Depends
import httpx
import os

MONITORING_SERVICE_URL = os.getenv("MONITORING_SERVICE_URL", "http://localhost:8001")
TESTING = os.getenv("TESTING") == "true"

def track_request():
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Skip monitoring service call during testing
            if not TESTING:
                # Track request via monitoring service
                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{MONITORING_SERVICE_URL}/metrics/request_count",
                        json={
                            "method": request.method,
                            "endpoint": request.url.path,
                            "count": 1
                        }
                    )
            
            return await func(request=request, *args, **kwargs)
        return wrapper
    return decorator 