# monitoring/prometheus.py
from prometheus_client import Counter, Gauge
from functools import wraps

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

ACTIVE_BOOKINGS = Gauge(
    'active_bookings',
    'Number of active bookings'
)

def track_request(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            response = await func(*args, **kwargs)
            REQUEST_COUNT.labels(
                method=kwargs.get('request', args[0]).method,
                endpoint=kwargs.get('request', args[0]).url.path,
                status=response.status_code
            ).inc()
            return response
        except Exception as e:
            REQUEST_COUNT.labels(
                method=kwargs.get('request', args[0]).method,
                endpoint=kwargs.get('request', args[0]).url.path,
                status=500
            ).inc()
            raise
    return wrapper