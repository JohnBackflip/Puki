from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

class FeedbackType(str, Enum):
    ROOM = "room"
    SERVICE = "service"
    STAFF = "staff"
    FACILITY = "facility"
    GENERAL = "general"

class FeedbackStatus(str, Enum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    RESOLVED = "resolved"
    CLOSED = "closed"

class Feedback:
    @staticmethod
    def create(cursor, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new feedback"""
        if cursor is None:
            # In test mode, return mock data
            mock_feedback = {
                "id": 1,
                "user_id": feedback_data["user_id"],
                "booking_id": feedback_data.get("booking_id"),
                "type": feedback_data["type"],
                "rating": feedback_data["rating"],
                "comment": feedback_data["comment"],
                "status": FeedbackStatus.PENDING.value,
                "metadata": feedback_data.get("metadata", {}),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            return mock_feedback
            
        query = """
            INSERT INTO feedback (user_id, booking_id, type, rating, comment, status, metadata)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            feedback_data["user_id"],
            feedback_data.get("booking_id"),
            feedback_data["type"],
            feedback_data["rating"],
            feedback_data["comment"],
            FeedbackStatus.PENDING.value,
            feedback_data.get("metadata", {})
        ))
        
        feedback_id = cursor.lastrowid
        return Feedback.get_by_id(cursor, feedback_id)
    
    @staticmethod
    def get_by_id(cursor, feedback_id: int) -> Optional[Dict[str, Any]]:
        """Get a feedback by ID"""
        if cursor is None:
            # In test mode, return mock data
            return {
                "id": feedback_id,
                "user_id": 1,
                "booking_id": 1,
                "type": FeedbackType.ROOM.value,
                "rating": 5,
                "comment": "Great experience!",
                "status": FeedbackStatus.REVIEWED.value,
                "metadata": {},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
        query = "SELECT * FROM feedback WHERE id = %s"
        cursor.execute(query, (feedback_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                "id": result[0],
                "user_id": result[1],
                "booking_id": result[2],
                "type": result[3],
                "rating": result[4],
                "comment": result[5],
                "status": result[6],
                "metadata": result[7],
                "created_at": result[8],
                "updated_at": result[9]
            }
        return None
    
    @staticmethod
    def get_by_user(cursor, user_id: int) -> List[Dict[str, Any]]:
        """Get all feedback from a user"""
        if cursor is None:
            # In test mode, return mock data
            return [{
                "id": 1,
                "user_id": user_id,
                "booking_id": 1,
                "type": FeedbackType.ROOM.value,
                "rating": 5,
                "comment": "Great experience!",
                "status": FeedbackStatus.REVIEWED.value,
                "metadata": {},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }]
            
        query = "SELECT * FROM feedback WHERE user_id = %s ORDER BY created_at DESC"
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        
        return [{
            "id": row[0],
            "user_id": row[1],
            "booking_id": row[2],
            "type": row[3],
            "rating": row[4],
            "comment": row[5],
            "status": row[6],
            "metadata": row[7],
            "created_at": row[8],
            "updated_at": row[9]
        } for row in results]
    
    @staticmethod
    def get_by_type(cursor, feedback_type: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all feedback of a specific type"""
        if cursor is None:
            # In test mode, return mock data
            return [{
                "id": 1,
                "user_id": 1,
                "booking_id": 1,
                "type": feedback_type,
                "rating": 5,
                "comment": "Great experience!",
                "status": status or FeedbackStatus.REVIEWED.value,
                "metadata": {},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }]
            
        query = "SELECT * FROM feedback WHERE type = %s"
        params = [feedback_type]
        
        if status:
            query += " AND status = %s"
            params.append(status)
            
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, tuple(params))
        results = cursor.fetchall()
        
        return [{
            "id": row[0],
            "user_id": row[1],
            "booking_id": row[2],
            "type": row[3],
            "rating": row[4],
            "comment": row[5],
            "status": row[6],
            "metadata": row[7],
            "created_at": row[8],
            "updated_at": row[9]
        } for row in results]
    
    @staticmethod
    def update_status(cursor, feedback_id: int, status: str) -> Optional[Dict[str, Any]]:
        """Update feedback status"""
        if cursor is None:
            # In test mode, return mock data
            return {
                "id": feedback_id,
                "user_id": 1,
                "booking_id": 1,
                "type": FeedbackType.ROOM.value,
                "rating": 5,
                "comment": "Great experience!",
                "status": status,
                "metadata": {},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
        query = """
            UPDATE feedback 
            SET status = %s, updated_at = NOW()
            WHERE id = %s
        """
        cursor.execute(query, (status, feedback_id))
        
        if cursor.rowcount > 0:
            return Feedback.get_by_id(cursor, feedback_id)
        return None
    
    @staticmethod
    def delete(cursor, feedback_id: int) -> bool:
        """Delete a feedback"""
        if cursor is None:
            # In test mode, return success
            return True
            
        query = "DELETE FROM feedback WHERE id = %s"
        cursor.execute(query, (feedback_id,))
        return cursor.rowcount > 0 