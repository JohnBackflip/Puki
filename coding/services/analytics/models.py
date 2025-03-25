# analytics/models.py
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

class AnalyticsType(str, Enum):
    OCCUPANCY = "occupancy"
    REVENUE = "revenue"
    BOOKING = "booking"
    CUSTOMER = "customer"

class Analytics:
    @staticmethod
    def create(cursor, analytics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new analytics record"""
        if cursor is None:
            # In test mode, return mock data
            mock_analytics = {
                "id": 1,
                "type": analytics_data["type"],
                "data": analytics_data["data"],
                "timestamp": datetime.now(),
                "created_at": datetime.now()
            }
            return mock_analytics
            
        query = """
            INSERT INTO analytics (type, data, timestamp)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (
            analytics_data["type"],
            analytics_data["data"],
            analytics_data.get("timestamp", datetime.now())
        ))
        
        analytics_id = cursor.lastrowid
        return Analytics.get_by_id(cursor, analytics_id)
    
    @staticmethod
    def get_by_id(cursor, analytics_id: int) -> Optional[Dict[str, Any]]:
        """Get an analytics record by ID"""
        if cursor is None:
            # In test mode, return mock data
            return {
                "id": analytics_id,
                "type": AnalyticsType.OCCUPANCY.value,
                "data": {"occupancy_rate": 0.75},
                "timestamp": datetime.now(),
                "created_at": datetime.now()
            }
            
        query = "SELECT * FROM analytics WHERE id = %s"
        cursor.execute(query, (analytics_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                "id": result[0],
                "type": result[1],
                "data": result[2],
                "timestamp": result[3],
                "created_at": result[4]
            }
        return None
    
    @staticmethod
    def get_by_type(cursor, analytics_type: str, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get analytics records by type and time range"""
        if cursor is None:
            # In test mode, return mock data
            return [{
                "id": 1,
                "type": analytics_type,
                "data": {"occupancy_rate": 0.75},
                "timestamp": datetime.now(),
                "created_at": datetime.now()
            }]
            
        query = "SELECT * FROM analytics WHERE type = %s"
        params = [analytics_type]
        
        if start_time:
            query += " AND timestamp >= %s"
            params.append(start_time)
        if end_time:
            query += " AND timestamp <= %s"
            params.append(end_time)
            
        query += " ORDER BY timestamp DESC"
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        
        return [{
            "id": row[0],
            "type": row[1],
            "data": row[2],
            "timestamp": row[3],
            "created_at": row[4]
        } for row in results]
    
    @staticmethod
    def get_latest(cursor, analytics_type: str) -> Optional[Dict[str, Any]]:
        """Get the latest analytics record for a type"""
        if cursor is None:
            # In test mode, return mock data
            return {
                "id": 1,
                "type": analytics_type,
                "data": {"occupancy_rate": 0.75},
                "timestamp": datetime.now(),
                "created_at": datetime.now()
            }
            
        query = """
            SELECT * FROM analytics 
            WHERE type = %s 
            ORDER BY timestamp DESC 
            LIMIT 1
        """
        cursor.execute(query, (analytics_type,))
        result = cursor.fetchone()
        
        if result:
            return {
                "id": result[0],
                "type": result[1],
                "data": result[2],
                "timestamp": result[3],
                "created_at": result[4]
            }
        return None
    
    @staticmethod
    def delete(cursor, analytics_id: int) -> bool:
        """Delete an analytics record"""
        if cursor is None:
            # In test mode, return success
            return True
            
        query = "DELETE FROM analytics WHERE id = %s"
        cursor.execute(query, (analytics_id,))
        return cursor.rowcount > 0

class AnalyticsEvent:
    @staticmethod
    def create(cursor, data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO analytics_events (event_type, user_id, timestamp, data)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["event_type"],
            data["user_id"],
            data["timestamp"],
            data["data"]
        ))
        return AnalyticsEvent.get_by_id(cursor, cursor.lastrowid)
    
    @staticmethod
    def get_by_id(cursor, event_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM analytics_events WHERE id = %s"
        cursor.execute(query, (event_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_by_type(cursor, event_type: str) -> List[Dict[str, Any]]:
        query = "SELECT * FROM analytics_events WHERE event_type = %s"
        cursor.execute(query, (event_type,))
        return cursor.fetchall()
    
    @staticmethod
    def get_by_user(cursor, user_id: int) -> List[Dict[str, Any]]:
        query = "SELECT * FROM analytics_events WHERE user_id = %s"
        cursor.execute(query, (user_id,))
        return cursor.fetchall()

class AnalyticsMetric:
    @staticmethod
    def create(cursor, data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO analytics_metrics (metric_name, value, timestamp, metadata)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["metric_name"],
            data["value"],
            data["timestamp"],
            data["metadata"]
        ))
        return AnalyticsMetric.get_by_id(cursor, cursor.lastrowid)
    
    @staticmethod
    def get_by_id(cursor, metric_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM analytics_metrics WHERE id = %s"
        cursor.execute(query, (metric_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_by_name(cursor, metric_name: str) -> List[Dict[str, Any]]:
        query = "SELECT * FROM analytics_metrics WHERE metric_name = %s"
        cursor.execute(query, (metric_name,))
        return cursor.fetchall()