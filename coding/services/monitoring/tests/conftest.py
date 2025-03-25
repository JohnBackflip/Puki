import pytest
from prometheus_client import REGISTRY, Counter, Gauge

@pytest.fixture(autouse=True)
def clear_metrics():
    # Clear all metrics before each test
    collectors = list(REGISTRY._collector_to_names.keys())
    for collector in collectors:
        REGISTRY.unregister(collector)
    
    # Re-register the metrics
    Counter(
        'http_requests_total',
        'Total number of HTTP requests',
        ['method', 'endpoint']
    )
    Gauge(
        'room_availability',
        'Number of available rooms by type',
        ['room_type']
    ) 