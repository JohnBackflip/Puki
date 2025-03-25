import pytest
from datetime import datetime
from services.ml.models import Prediction, TrainingData, ModelVersion

def test_prediction_creation(mock_cursor):
    # Test data
    prediction_data = {
        "model_version": "1.0.0",
        "input_data": {"features": [1, 2, 3]},
        "prediction": {"class": "positive", "probability": 0.95},
        "confidence": 0.95
    }
    
    # Create prediction
    prediction = Prediction.create(mock_cursor, prediction_data)
    
    # Assertions
    assert prediction["id"] == 1
    assert prediction["model_version"] == prediction_data["model_version"]
    assert prediction["input_data"] == prediction_data["input_data"]
    assert prediction["prediction"] == prediction_data["prediction"]
    assert prediction["confidence"] == prediction_data["confidence"]

def test_prediction_retrieval(mock_cursor):
    # Create test prediction
    prediction_data = {
        "model_version": "1.0.0",
        "input_data": {"features": [1, 2, 3]},
        "prediction": {"class": "positive", "probability": 0.95},
        "confidence": 0.95
    }
    prediction = Prediction.create(mock_cursor, prediction_data)
    
    # Test retrieval
    retrieved_prediction = Prediction.get_by_id(mock_cursor, prediction["id"])
    assert retrieved_prediction == prediction

def test_prediction_by_model_version(mock_cursor):
    # Create test predictions
    predictions = [
        Prediction.create(mock_cursor, {
            "model_version": "1.0.0",
            "input_data": {"features": [1, 2, 3]},
            "prediction": {"class": "positive", "probability": 0.95},
            "confidence": 0.95
        }),
        Prediction.create(mock_cursor, {
            "model_version": "2.0.0",
            "input_data": {"features": [4, 5, 6]},
            "prediction": {"class": "negative", "probability": 0.85},
            "confidence": 0.85
        })
    ]
    
    # Test filtering by model version
    version_predictions = Prediction.get_by_model_version(mock_cursor, "1.0.0")
    assert len(version_predictions) == 1
    assert version_predictions[0]["model_version"] == "1.0.0"

def test_training_data_creation(mock_cursor):
    # Test data
    training_data = {
        "input_data": {"features": [1, 2, 3]},
        "target_data": {"label": "positive"}
    }
    
    # Create training data
    data = TrainingData.create(mock_cursor, training_data)
    
    # Assertions
    assert data["id"] == 1
    assert data["input_data"] == training_data["input_data"]
    assert data["target_data"] == training_data["target_data"]

def test_training_data_retrieval(mock_cursor):
    # Create test training data
    training_data = {
        "input_data": {"features": [1, 2, 3]},
        "target_data": {"label": "positive"}
    }
    data = TrainingData.create(mock_cursor, training_data)
    
    # Test retrieval
    retrieved_data = TrainingData.get_by_id(mock_cursor, data["id"])
    assert retrieved_data == data

def test_model_version_creation(mock_cursor):
    # Test data
    version_data = {
        "version": "1.0.0",
        "model_path": "/path/to/model",
        "metrics": {"accuracy": 0.95, "precision": 0.94}
    }
    
    # Create model version
    version = ModelVersion.create(mock_cursor, version_data)
    
    # Assertions
    assert version["id"] == 1
    assert version["version"] == version_data["version"]
    assert version["model_path"] == version_data["model_path"]
    assert version["metrics"] == version_data["metrics"]

def test_model_version_retrieval(mock_cursor):
    # Create test model version
    version_data = {
        "version": "1.0.0",
        "model_path": "/path/to/model",
        "metrics": {"accuracy": 0.95, "precision": 0.94}
    }
    version = ModelVersion.create(mock_cursor, version_data)
    
    # Test retrieval
    retrieved_version = ModelVersion.get_by_id(mock_cursor, version["id"])
    assert retrieved_version == version

def test_model_version_filtering(mock_cursor):
    # Create test model versions
    versions = [
        ModelVersion.create(mock_cursor, {
            "version": "1.0.0",
            "model_path": "/path/to/model1",
            "metrics": {"accuracy": 0.95, "precision": 0.94}
        }),
        ModelVersion.create(mock_cursor, {
            "version": "2.0.0",
            "model_path": "/path/to/model2",
            "metrics": {"accuracy": 0.96, "precision": 0.95}
        })
    ]
    
    # Test filtering by version
    version = ModelVersion.get_by_version(mock_cursor, "1.0.0")
    assert version["version"] == "1.0.0"
    assert version["model_path"] == "/path/to/model1" 