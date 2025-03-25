# housekeeping/models.py
import enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from mysql.connector.pooling import MySQLConnectionPool

class CleaningStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    VERIFIED = "verified"

class CleaningTask:
    @staticmethod
    def create_table(cursor):
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cleaning_tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_id INT NOT NULL,
                staff_id INT,
                status ENUM('pending', 'in_progress', 'completed', 'verified') NOT NULL DEFAULT 'pending',
                scheduled_at DATETIME NOT NULL,
                started_at DATETIME,
                completed_at DATETIME,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_room_id (room_id),
                INDEX idx_staff_id (staff_id),
                INDEX idx_status (status)
            )
        """)

    @staticmethod
    def create(cursor, room_id: int, scheduled_at: datetime, notes: Optional[str] = None) -> Dict[str, Any]:
        query = """
            INSERT INTO cleaning_tasks (room_id, scheduled_at, notes)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (room_id, scheduled_at, notes))
        cursor.execute("SELECT LAST_INSERT_ID()")
        task_id = cursor.fetchone()["LAST_INSERT_ID()"]
        
        return CleaningTask.get_by_id(cursor, task_id)

    @staticmethod
    def get_by_id(cursor, task_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM cleaning_tasks WHERE id = %s"
        cursor.execute(query, (task_id,))
        result = cursor.fetchone()
        return result if result else None

    @staticmethod
    def list_all(cursor, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        query = "SELECT * FROM cleaning_tasks ORDER BY scheduled_at LIMIT %s OFFSET %s"
        cursor.execute(query, (limit, skip))
        return cursor.fetchall()

    @staticmethod
    def list_by_status(cursor, status: CleaningStatus, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        query = "SELECT * FROM cleaning_tasks WHERE status = %s ORDER BY scheduled_at LIMIT %s OFFSET %s"
        cursor.execute(query, (status.value, limit, skip))
        return cursor.fetchall()

    @staticmethod
    def list_by_staff(cursor, staff_id: int, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        query = "SELECT * FROM cleaning_tasks WHERE staff_id = %s ORDER BY scheduled_at LIMIT %s OFFSET %s"
        cursor.execute(query, (staff_id, limit, skip))
        return cursor.fetchall()

    @staticmethod
    def update_status(cursor, task_id: int, status: CleaningStatus, staff_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        now = datetime.now()
        update_fields = ["status = %s"]
        params = [status.value]
        
        if status == CleaningStatus.IN_PROGRESS:
            update_fields.extend(["started_at = %s", "staff_id = %s"])
            params.extend([now, staff_id])
        elif status == CleaningStatus.COMPLETED:
            update_fields.append("completed_at = %s")
            params.append(now)
        
        params.append(task_id)
        query = f"UPDATE cleaning_tasks SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, tuple(params))
        
        return CleaningTask.get_by_id(cursor, task_id) if cursor.rowcount > 0 else None

    @staticmethod
    def update_notes(cursor, task_id: int, notes: str) -> Optional[Dict[str, Any]]:
        query = "UPDATE cleaning_tasks SET notes = %s WHERE id = %s"
        cursor.execute(query, (notes, task_id))
        return CleaningTask.get_by_id(cursor, task_id) if cursor.rowcount > 0 else None