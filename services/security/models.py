# security/models.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from .database import Base
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

class DigitalKey:
    @staticmethod
    def create(cursor, key_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new digital key"""
        if cursor is None:
            # In test mode, return mock data
            mock_key = {
                "id": 1,
                "booking_id": key_data["booking_id"],
                "room_id": key_data["room_id"],
                "key_hash": key_data["key_hash"],
                "valid_from": key_data["valid_from"],
                "valid_until": key_data["valid_until"],
                "is_active": key_data.get("is_active", True),
                "created_at": datetime.now()
            }
            return mock_key
            
        query = """
            INSERT INTO digital_keys (booking_id, room_id, key_hash, valid_from, valid_until, is_active)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            key_data["booking_id"],
            key_data["room_id"],
            key_data["key_hash"],
            key_data["valid_from"],
            key_data["valid_until"],
            key_data.get("is_active", True)
        ))
        
        key_id = cursor.lastrowid
        return DigitalKey.get_by_id(cursor, key_id)
    
    @staticmethod
    def get_by_id(cursor, key_id: int) -> Optional[Dict[str, Any]]:
        """Get a digital key by ID"""
        if cursor is None:
            # In test mode, return mock data
            return {
                "id": key_id,
                "booking_id": 1,
                "room_id": 1,
                "key_hash": "test_hash",
                "valid_from": datetime.now(),
                "valid_until": datetime.now(),
                "is_active": True,
                "created_at": datetime.now()
            }
            
        query = "SELECT * FROM digital_keys WHERE id = %s"
        cursor.execute(query, (key_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                "id": result[0],
                "booking_id": result[1],
                "room_id": result[2],
                "key_hash": result[3],
                "valid_from": result[4],
                "valid_until": result[5],
                "is_active": result[6],
                "created_at": result[7]
            }
        return None
    
    @staticmethod
    def get_by_booking(cursor, booking_id: int) -> List[Dict[str, Any]]:
        """Get all digital keys for a booking"""
        if cursor is None:
            # In test mode, return mock data
            return [{
                "id": 1,
                "booking_id": booking_id,
                "room_id": 1,
                "key_hash": "test_hash",
                "valid_from": datetime.now(),
                "valid_until": datetime.now(),
                "is_active": True,
                "created_at": datetime.now()
            }]
            
        query = "SELECT * FROM digital_keys WHERE booking_id = %s ORDER BY created_at DESC"
        cursor.execute(query, (booking_id,))
        results = cursor.fetchall()
        
        return [{
            "id": row[0],
            "booking_id": row[1],
            "room_id": row[2],
            "key_hash": row[3],
            "valid_from": row[4],
            "valid_until": row[5],
            "is_active": row[6],
            "created_at": row[7]
        } for row in results]
    
    @staticmethod
    def get_by_room(cursor, room_id: int) -> List[Dict[str, Any]]:
        """Get all digital keys for a room"""
        if cursor is None:
            # In test mode, return mock data
            return [{
                "id": 1,
                "booking_id": 1,
                "room_id": room_id,
                "key_hash": "test_hash",
                "valid_from": datetime.now(),
                "valid_until": datetime.now(),
                "is_active": True,
                "created_at": datetime.now()
            }]
            
        query = "SELECT * FROM digital_keys WHERE room_id = %s ORDER BY created_at DESC"
        cursor.execute(query, (room_id,))
        results = cursor.fetchall()
        
        return [{
            "id": row[0],
            "booking_id": row[1],
            "room_id": row[2],
            "key_hash": row[3],
            "valid_from": row[4],
            "valid_until": row[5],
            "is_active": row[6],
            "created_at": row[7]
        } for row in results]
    
    @staticmethod
    def update_status(cursor, key_id: int, is_active: bool) -> Optional[Dict[str, Any]]:
        """Update digital key status"""
        if cursor is None:
            # In test mode, return mock data
            return {
                "id": key_id,
                "booking_id": 1,
                "room_id": 1,
                "key_hash": "test_hash",
                "valid_from": datetime.now(),
                "valid_until": datetime.now(),
                "is_active": is_active,
                "created_at": datetime.now()
            }
            
        query = "UPDATE digital_keys SET is_active = %s WHERE id = %s"
        cursor.execute(query, (is_active, key_id))
        
        if cursor.rowcount > 0:
            return DigitalKey.get_by_id(cursor, key_id)
        return None
    
    @staticmethod
    def delete(cursor, key_id: int) -> bool:
        """Delete a digital key"""
        if cursor is None:
            # In test mode, return success
            return True
            
        query = "DELETE FROM digital_keys WHERE id = %s"
        cursor.execute(query, (key_id,))
        return cursor.rowcount > 0

class SecurityEventType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    PROFILE_UPDATE = "profile_update"
    ACCESS_DENIED = "access_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

class SecurityEvent:
    @staticmethod
    def create(cursor, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new security event"""
        if cursor is None:
            # In test mode, return mock data
            mock_event = {
                "id": 1,
                "user_id": event_data["user_id"],
                "type": event_data["type"],
                "ip_address": event_data.get("ip_address"),
                "user_agent": event_data.get("user_agent"),
                "details": event_data.get("details", {}),
                "created_at": datetime.now()
            }
            return mock_event
            
        query = """
            INSERT INTO security_events (user_id, type, ip_address, user_agent, details)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            event_data["user_id"],
            event_data["type"],
            event_data.get("ip_address"),
            event_data.get("user_agent"),
            event_data.get("details", {})
        ))
        
        event_id = cursor.lastrowid
        return SecurityEvent.get_by_id(cursor, event_id)
    
    @staticmethod
    def get_by_id(cursor, event_id: int) -> Optional[Dict[str, Any]]:
        """Get a security event by ID"""
        if cursor is None:
            # In test mode, return mock data
            return {
                "id": event_id,
                "user_id": 1,
                "type": SecurityEventType.LOGIN.value,
                "ip_address": "127.0.0.1",
                "user_agent": "Mozilla/5.0",
                "details": {},
                "created_at": datetime.now()
            }
            
        query = "SELECT * FROM security_events WHERE id = %s"
        cursor.execute(query, (event_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                "id": result[0],
                "user_id": result[1],
                "type": result[2],
                "ip_address": result[3],
                "user_agent": result[4],
                "details": result[5],
                "created_at": result[6]
            }
        return None
    
    @staticmethod
    def get_by_user(cursor, user_id: int) -> List[Dict[str, Any]]:
        """Get all security events for a user"""
        if cursor is None:
            # In test mode, return mock data
            return [{
                "id": 1,
                "user_id": user_id,
                "type": SecurityEventType.LOGIN.value,
                "ip_address": "127.0.0.1",
                "user_agent": "Mozilla/5.0",
                "details": {},
                "created_at": datetime.now()
            }]
            
        query = "SELECT * FROM security_events WHERE user_id = %s ORDER BY created_at DESC"
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        
        return [{
            "id": row[0],
            "user_id": row[1],
            "type": row[2],
            "ip_address": row[3],
            "user_agent": row[4],
            "details": row[5],
            "created_at": row[6]
        } for row in results]
    
    @staticmethod
    def get_by_type(cursor, event_type: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get security events by type and time range"""
        if cursor is None:
            # In test mode, return mock data
            return [{
                "id": 1,
                "user_id": 1,
                "type": event_type,
                "ip_address": "127.0.0.1",
                "user_agent": "Mozilla/5.0",
                "details": {},
                "created_at": datetime.now()
            }]
            
        query = "SELECT * FROM security_events WHERE type = %s"
        params = [event_type]
        
        if start_time:
            query += " AND created_at >= %s"
            params.append(start_time)
        if end_time:
            query += " AND created_at <= %s"
            params.append(end_time)
            
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        
        return [{
            "id": row[0],
            "user_id": row[1],
            "type": row[2],
            "ip_address": row[3],
            "user_agent": row[4],
            "details": row[5],
            "created_at": row[6]
        } for row in results]
    
    @staticmethod
    def delete(cursor, event_id: int) -> bool:
        """Delete a security event"""
        if cursor is None:
            # In test mode, return success
            return True
            
        query = "DELETE FROM security_events WHERE id = %s"
        cursor.execute(query, (event_id,))
        return cursor.rowcount > 0