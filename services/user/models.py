# services/user/models.py
from datetime import datetime
from typing import Optional, Dict, Any, List

class User:
    @staticmethod
    def create(cursor, username: str, email: str, hashed_password: str) -> Dict[str, Any]:
        query = """
            INSERT INTO users (username, email, hashed_password)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (username, email, hashed_password))
        cursor.execute("SELECT LAST_INSERT_ID()")
        user_id = cursor.fetchone()["LAST_INSERT_ID()"]
        
        # Add default guest role
        Role.add_user_role(cursor, user_id, "guest")
        
        return User.get_by_id(cursor, user_id)
    
    @staticmethod
    def get_by_id(cursor, user_id: int) -> Optional[Dict[str, Any]]:
        query = """
            SELECT u.*, GROUP_CONCAT(r.name) as roles
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            WHERE u.id = %s
            GROUP BY u.id
        """
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        if user:
            user["roles"] = user["roles"].split(",") if user["roles"] else []
        return user
    
    @staticmethod
    def get_by_username(cursor, username: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT u.*, GROUP_CONCAT(r.name) as roles
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            WHERE u.username = %s
            GROUP BY u.id
        """
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        if user:
            user["roles"] = user["roles"].split(",") if user["roles"] else []
        return user
    
    @staticmethod
    def get_by_email(cursor, email: str) -> Optional[Dict[str, Any]]:
        query = """
            SELECT u.*, GROUP_CONCAT(r.name) as roles
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            WHERE u.email = %s
            GROUP BY u.id
        """
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        if user:
            user["roles"] = user["roles"].split(",") if user["roles"] else []
        return user
    
    @staticmethod
    def list_users(cursor, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        query = """
            SELECT u.*, GROUP_CONCAT(r.name) as roles
            FROM users u
            LEFT JOIN user_roles ur ON u.id = ur.user_id
            LEFT JOIN roles r ON ur.role_id = r.id
            GROUP BY u.id
            LIMIT %s OFFSET %s
        """
        cursor.execute(query, (limit, skip))
        users = cursor.fetchall()
        for user in users:
            user["roles"] = user["roles"].split(",") if user["roles"] else []
        return users

class Role:
    @staticmethod
    def create(cursor, name: str) -> Dict[str, Any]:
        query = "INSERT INTO roles (name) VALUES (%s)"
        cursor.execute(query, (name,))
        cursor.execute("SELECT LAST_INSERT_ID()")
        role_id = cursor.fetchone()["LAST_INSERT_ID()"]
        return Role.get_by_id(cursor, role_id)
    
    @staticmethod
    def get_by_id(cursor, role_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM roles WHERE id = %s"
        cursor.execute(query, (role_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_by_name(cursor, name: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM roles WHERE name = %s"
        cursor.execute(query, (name,))
        return cursor.fetchone()
    
    @staticmethod
    def add_user_role(cursor, user_id: int, role_name: str) -> bool:
        role = Role.get_by_name(cursor, role_name)
        if not role:
            return False
        
        query = """
            INSERT IGNORE INTO user_roles (user_id, role_id)
            VALUES (%s, %s)
        """
        cursor.execute(query, (user_id, role["id"]))
        return cursor.rowcount > 0
    
    @staticmethod
    def remove_user_role(cursor, user_id: int, role_name: str) -> bool:
        role = Role.get_by_name(cursor, role_name)
        if not role:
            return False
        
        query = """
            DELETE FROM user_roles
            WHERE user_id = %s AND role_id = %s
        """
        cursor.execute(query, (user_id, role["id"]))
        return cursor.rowcount > 0