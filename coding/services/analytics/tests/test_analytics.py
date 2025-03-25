import pytest
from datetime import datetime
from services.analytics.models import AnalyticsEvent, AnalyticsMetric

def test_analytics_event_creation(mock_cursor):
    # Test data
    event_data = {
        "event_type": "booking_created",
        "user_id": 1,
        "timestamp": datetime.now(),
        "data": {"booking_id": 1, "amount": 100.00}
    }
    
    # Create event
    event = AnalyticsEvent.create(mock_cursor, event_data)
    
    # Assertions
    assert event["id"] == 1
    assert event["event_type"] == event_data["event_type"]
    assert event["user_id"] == event_data["user_id"]
    assert event["data"] == event_data["data"]

def test_analytics_event_retrieval(mock_cursor):
    # Create test event
    event_data = {
        "event_type": "booking_created",
        "user_id": 1,
        "timestamp": datetime.now(),
        "data": {"booking_id": 1, "amount": 100.00}
    }
    event = AnalyticsEvent.create(mock_cursor, event_data)
    
    # Test retrieval
    retrieved_event = AnalyticsEvent.get_by_id(mock_cursor, event["id"])
    assert retrieved_event == event

def test_analytics_event_filtering(mock_cursor):
    # Create test events
    events = [
        AnalyticsEvent.create(mock_cursor, {
            "event_type": "booking_created",
            "user_id": 1,
            "timestamp": datetime.now(),
            "data": {"booking_id": 1, "amount": 100.00}
        }),
        AnalyticsEvent.create(mock_cursor, {
            "event_type": "payment_completed",
            "user_id": 2,
            "timestamp": datetime.now(),
            "data": {"payment_id": 1, "amount": 100.00}
        })
    ]
    
    # Test filtering by event type
    booking_events = AnalyticsEvent.get_by_type(mock_cursor, "booking_created")
    assert len(booking_events) == 1
    assert booking_events[0]["event_type"] == "booking_created"
    
    # Test filtering by user
    user_events = AnalyticsEvent.get_by_user(mock_cursor, 1)
    assert len(user_events) == 1
    assert user_events[0]["user_id"] == 1

def test_analytics_metric_creation(mock_cursor):
    # Test data
    metric_data = {
        "metric_name": "total_bookings",
        "value": 100,
        "timestamp": datetime.now(),
        "metadata": {"period": "daily"}
    }
    
    # Create metric
    metric = AnalyticsMetric.create(mock_cursor, metric_data)
    
    # Assertions
    assert metric["id"] == 1
    assert metric["metric_name"] == metric_data["metric_name"]
    assert metric["value"] == metric_data["value"]
    assert metric["metadata"] == metric_data["metadata"]

def test_analytics_metric_retrieval(mock_cursor):
    # Create test metric
    metric_data = {
        "metric_name": "total_bookings",
        "value": 100,
        "timestamp": datetime.now(),
        "metadata": {"period": "daily"}
    }
    metric = AnalyticsMetric.create(mock_cursor, metric_data)
    
    # Test retrieval
    retrieved_metric = AnalyticsMetric.get_by_id(mock_cursor, metric["id"])
    assert retrieved_metric == metric

def test_analytics_metric_filtering(mock_cursor):
    # Create test metrics
    metrics = [
        AnalyticsMetric.create(mock_cursor, {
            "metric_name": "total_bookings",
            "value": 100,
            "timestamp": datetime.now(),
            "metadata": {"period": "daily"}
        }),
        AnalyticsMetric.create(mock_cursor, {
            "metric_name": "total_revenue",
            "value": 10000.00,
            "timestamp": datetime.now(),
            "metadata": {"period": "daily"}
        })
    ]
    
    # Test filtering by metric name
    booking_metrics = AnalyticsMetric.get_by_name(mock_cursor, "total_bookings")
    assert len(booking_metrics) == 1
    assert booking_metrics[0]["metric_name"] == "total_bookings" 