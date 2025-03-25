import pytest
from datetime import datetime
from ..models import Notification, NotificationType

def test_notification_creation(mock_cursor):
    # Test data
    notification_data = {
        "user_id": 1,
        "type": NotificationType.BOOKING_CONFIRMED.value,
        "title": "Booking Confirmed",
        "message": "Your booking has been confirmed",
        "is_read": False,
        "metadata": {"booking_id": 1}
    }
    
    # Create notification
    notification = Notification.create(mock_cursor, notification_data)
    
    # Assertions
    assert notification["id"] == 1
    assert notification["user_id"] == notification_data["user_id"]
    assert notification["type"] == notification_data["type"]
    assert notification["title"] == notification_data["title"]
    assert notification["message"] == notification_data["message"]
    assert notification["is_read"] == notification_data["is_read"]
    assert notification["metadata"] == notification_data["metadata"]

def test_notification_retrieval(mock_cursor):
    # Create test notification
    notification_data = {
        "user_id": 1,
        "type": NotificationType.BOOKING_CONFIRMED.value,
        "title": "Booking Confirmed",
        "message": "Your booking has been confirmed",
        "is_read": False,
        "metadata": {"booking_id": 1}
    }
    notification = Notification.create(mock_cursor, notification_data)
    
    # Test retrieval
    retrieved_notification = Notification.get_by_id(mock_cursor, notification["id"])
    assert retrieved_notification == notification

def test_notification_mark_read(mock_cursor):
    # Create test notification
    notification_data = {
        "user_id": 1,
        "type": NotificationType.BOOKING_CONFIRMED.value,
        "title": "Booking Confirmed",
        "message": "Your booking has been confirmed",
        "is_read": False,
        "metadata": {"booking_id": 1}
    }
    notification = Notification.create(mock_cursor, notification_data)
    
    # Mark as read
    updated_notification = Notification.mark_read(mock_cursor, notification["id"])
    assert updated_notification["is_read"] is True

def test_notification_by_user(mock_cursor):
    # Create test notifications
    notifications = [
        Notification.create(mock_cursor, {
            "user_id": 1,
            "type": NotificationType.BOOKING_CONFIRMED.value,
            "title": "Booking Confirmed",
            "message": "Your booking has been confirmed",
            "is_read": False,
            "metadata": {"booking_id": 1}
        }),
        Notification.create(mock_cursor, {
            "user_id": 2,
            "type": NotificationType.PAYMENT_SUCCESS.value,
            "title": "Payment Successful",
            "message": "Your payment has been processed",
            "is_read": False,
            "metadata": {"payment_id": 1}
        })
    ]
    
    # Test retrieval by user
    user_notifications = Notification.get_by_user(mock_cursor, 1)
    assert len(user_notifications) == 1
    assert user_notifications[0]["user_id"] == 1

def test_notification_by_type(mock_cursor):
    # Create test notifications
    notifications = [
        Notification.create(mock_cursor, {
            "user_id": 1,
            "type": NotificationType.BOOKING_CONFIRMED.value,
            "title": "Booking Confirmed",
            "message": "Your booking has been confirmed",
            "is_read": False,
            "metadata": {"booking_id": 1}
        }),
        Notification.create(mock_cursor, {
            "user_id": 2,
            "type": NotificationType.PAYMENT_SUCCESS.value,
            "title": "Payment Successful",
            "message": "Your payment has been processed",
            "is_read": False,
            "metadata": {"payment_id": 1}
        })
    ]
    
    # Test retrieval by type
    booking_notifications = Notification.get_by_type(mock_cursor, NotificationType.BOOKING_CONFIRMED.value)
    assert len(booking_notifications) == 1
    assert booking_notifications[0]["type"] == NotificationType.BOOKING_CONFIRMED.value 