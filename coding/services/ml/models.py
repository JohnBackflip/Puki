# ml/models.py
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum

class ModelType(str, Enum):
    PRICE_PREDICTION = "price_prediction"
    OCCUPANCY_PREDICTION = "occupancy_prediction"
    CUSTOMER_SEGMENTATION = "customer_segmentation"
    ANOMALY_DETECTION = "anomaly_detection"

class ModelStatus(str, Enum):
    TRAINING = "training"
    READY = "ready"
    FAILED = "failed"
    DEPRECATED = "deprecated"

class MLModel:
    @staticmethod
    def create(cursor, model_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new ML model record"""
        if cursor is None:
            # In test mode, return mock data
            mock_model = {
                "id": 1,
                "name": model_data["name"],
                "type": model_data["type"],
                "version": model_data["version"],
                "status": ModelStatus.TRAINING.value,
                "parameters": model_data.get("parameters", {}),
                "metrics": model_data.get("metrics", {}),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            return mock_model
            
        query = """
            INSERT INTO ml_models (name, type, version, status, parameters, metrics)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (
            model_data["name"],
            model_data["type"],
            model_data["version"],
            ModelStatus.TRAINING.value,
            model_data.get("parameters", {}),
            model_data.get("metrics", {})
        ))
        
        model_id = cursor.lastrowid
        return MLModel.get_by_id(cursor, model_id)
    
    @staticmethod
    def get_by_id(cursor, model_id: int) -> Optional[Dict[str, Any]]:
        """Get an ML model by ID"""
        if cursor is None:
            # In test mode, return mock data
            return {
                "id": model_id,
                "name": "Test Model",
                "type": ModelType.PRICE_PREDICTION.value,
                "version": "1.0.0",
                "status": ModelStatus.READY.value,
                "parameters": {"learning_rate": 0.01},
                "metrics": {"accuracy": 0.95},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
        query = "SELECT * FROM ml_models WHERE id = %s"
        cursor.execute(query, (model_id,))
        result = cursor.fetchone()
        
        if result:
            return {
                "id": result[0],
                "name": result[1],
                "type": result[2],
                "version": result[3],
                "status": result[4],
                "parameters": result[5],
                "metrics": result[6],
                "created_at": result[7],
                "updated_at": result[8]
            }
        return None
    
    @staticmethod
    def get_latest_by_type(cursor, model_type: str) -> Optional[Dict[str, Any]]:
        """Get the latest ready model of a specific type"""
        if cursor is None:
            # In test mode, return mock data
            return {
                "id": 1,
                "name": "Test Model",
                "type": model_type,
                "version": "1.0.0",
                "status": ModelStatus.READY.value,
                "parameters": {"learning_rate": 0.01},
                "metrics": {"accuracy": 0.95},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
        query = """
            SELECT * FROM ml_models 
            WHERE type = %s AND status = %s
            ORDER BY version DESC 
            LIMIT 1
        """
        cursor.execute(query, (model_type, ModelStatus.READY.value))
        result = cursor.fetchone()
        
        if result:
            return {
                "id": result[0],
                "name": result[1],
                "type": result[2],
                "version": result[3],
                "status": result[4],
                "parameters": result[5],
                "metrics": result[6],
                "created_at": result[7],
                "updated_at": result[8]
            }
        return None
    
    @staticmethod
    def update_status(cursor, model_id: int, status: str, metrics: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Update model status and optionally metrics"""
        if cursor is None:
            # In test mode, return mock data
            return {
                "id": model_id,
                "name": "Test Model",
                "type": ModelType.PRICE_PREDICTION.value,
                "version": "1.0.0",
                "status": status,
                "parameters": {"learning_rate": 0.01},
                "metrics": metrics or {"accuracy": 0.95},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
        query = """
            UPDATE ml_models 
            SET status = %s, metrics = %s, updated_at = NOW()
            WHERE id = %s
        """
        cursor.execute(query, (status, metrics or {}, model_id))
        
        if cursor.rowcount > 0:
            return MLModel.get_by_id(cursor, model_id)
        return None
    
    @staticmethod
    def delete(cursor, model_id: int) -> bool:
        """Delete an ML model"""
        if cursor is None:
            # In test mode, return success
            return True
            
        query = "DELETE FROM ml_models WHERE id = %s"
        cursor.execute(query, (model_id,))
        return cursor.rowcount > 0

class Prediction:
    @staticmethod
    def create(cursor, data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO predictions (model_version, input_data, prediction, confidence)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (
            data["model_version"],
            data["input_data"],
            data["prediction"],
            data["confidence"]
        ))
        return Prediction.get_by_id(cursor, cursor.lastrowid)
    
    @staticmethod
    def get_by_id(cursor, prediction_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM predictions WHERE id = %s"
        cursor.execute(query, (prediction_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_by_model_version(cursor, model_version: str) -> List[Dict[str, Any]]:
        query = "SELECT * FROM predictions WHERE model_version = %s"
        cursor.execute(query, (model_version,))
        return cursor.fetchall()

class TrainingData:
    @staticmethod
    def create(cursor, data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO training_data (input_data, target_data)
            VALUES (%s, %s)
        """
        cursor.execute(query, (
            data["input_data"],
            data["target_data"]
        ))
        return TrainingData.get_by_id(cursor, cursor.lastrowid)
    
    @staticmethod
    def get_by_id(cursor, data_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM training_data WHERE id = %s"
        cursor.execute(query, (data_id,))
        return cursor.fetchone()

class ModelVersion:
    @staticmethod
    def create(cursor, data: Dict[str, Any]) -> Dict[str, Any]:
        query = """
            INSERT INTO model_versions (version, model_path, metrics)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (
            data["version"],
            data["model_path"],
            data["metrics"]
        ))
        return ModelVersion.get_by_id(cursor, cursor.lastrowid)
    
    @staticmethod
    def get_by_id(cursor, version_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM model_versions WHERE id = %s"
        cursor.execute(query, (version_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_by_version(cursor, version: str) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM model_versions WHERE version = %s"
        cursor.execute(query, (version,))
        return cursor.fetchone()