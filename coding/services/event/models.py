import enum
from datetime import datetime
from typing import Optional, List, Dict, Any

class EventType(str, enum.Enum):
    CONFERENCE = "conference"
    CONCERT = "concert"
    SPORTS = "sports"
    FESTIVAL = "festival"
    HOLIDAY = "holiday"

class PriceAdjustmentType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"

class Event:
    @staticmethod
    def create(cursor, name: str, description: str, event_type: str, start_date: datetime, end_date: datetime, location: str) -> Dict[str, Any]:
        cursor.execute("""
            INSERT INTO events (name, description, event_type, start_date, end_date, location)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (name, description, event_type, start_date, end_date, location))
        event_id = cursor.lastrowid
        
        cursor.execute("""
            SELECT * FROM events WHERE id = %s
        """, (event_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_by_id(cursor, event_id: int) -> Optional[Dict[str, Any]]:
        cursor.execute("""
            SELECT * FROM events WHERE id = %s
        """, (event_id,))
        return cursor.fetchone()
    
    @staticmethod
    def list_events(cursor, event_type: Optional[str] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM events WHERE 1=1"
        params = []
        
        if event_type:
            query += " AND event_type = %s"
            params.append(event_type)
        
        if start_date:
            query += " AND start_date >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND end_date <= %s"
            params.append(end_date)
        
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    
    @staticmethod
    def update(cursor, event_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        if not kwargs:
            return None
        
        set_clause = ", ".join(f"{key} = %s" for key in kwargs.keys())
        query = f"UPDATE events SET {set_clause} WHERE id = %s"
        params = list(kwargs.values()) + [event_id]
        
        cursor.execute(query, tuple(params))
        
        if cursor.rowcount > 0:
            return Event.get_by_id(cursor, event_id)
        return None
    
    @staticmethod
    def delete(cursor, event_id: int) -> bool:
        cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
        return cursor.rowcount > 0

class PriceAdjustment:
    @staticmethod
    def create(cursor, event_id: int, adjustment_type: str, value: float) -> Dict[str, Any]:
        cursor.execute("""
            INSERT INTO price_adjustments (event_id, adjustment_type, value)
            VALUES (%s, %s, %s)
        """, (event_id, adjustment_type, value))
        adjustment_id = cursor.lastrowid
        
        cursor.execute("""
            SELECT * FROM price_adjustments WHERE id = %s
        """, (adjustment_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_by_id(cursor, adjustment_id: int) -> Optional[Dict[str, Any]]:
        cursor.execute("""
            SELECT * FROM price_adjustments WHERE id = %s
        """, (adjustment_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_by_event(cursor, event_id: int) -> List[Dict[str, Any]]:
        cursor.execute("""
            SELECT * FROM price_adjustments WHERE event_id = %s
        """, (event_id,))
        return cursor.fetchall()
    
    @staticmethod
    def update(cursor, adjustment_id: int, **kwargs) -> Optional[Dict[str, Any]]:
        if not kwargs:
            return None
        
        set_clause = ", ".join(f"{key} = %s" for key in kwargs.keys())
        query = f"UPDATE price_adjustments SET {set_clause} WHERE id = %s"
        params = list(kwargs.values()) + [adjustment_id]
        
        cursor.execute(query, tuple(params))
        
        if cursor.rowcount > 0:
            return PriceAdjustment.get_by_id(cursor, adjustment_id)
        return None
    
    @staticmethod
    def delete(cursor, adjustment_id: int) -> bool:
        cursor.execute("DELETE FROM price_adjustments WHERE id = %s", (adjustment_id,))
        return cursor.rowcount > 0 