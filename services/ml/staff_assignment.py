# ml/predictors/staff_assignment.py
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

class StaffAssignmentPredictor:
    def __init__(self):
        self.model = None
        self.model_path = os.path.join(os.getenv("MODEL_PATH"), "staff_assignment.joblib")
        self.load_model()
    
    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
        else:
            self.model = RandomForestClassifier()
    
    def train(self, X, y):
        self.model.fit(X, y)
        joblib.dump(self.model, self.model_path)
    
    def predict(self, features):
        return self.model.predict(features)

class MaintenancePrediction:
    def __init__(self):
        self.model = None
        self.model_path = os.path.join(os.getenv("MODEL_PATH"), "maintenance.joblib")
        self.load_model()
    
    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
        else:
            self.model = RandomForestClassifier()
    
    def predict_maintenance(self, room_data):
        if not self.model:
            return {"needs_maintenance": False, "confidence": 0.0}
        
        prediction = self.model.predict_proba([room_data])[0]
        needs_maintenance = prediction[1] > 0.7
        
        return {
            "needs_maintenance": needs_maintenance,
            "confidence": float(prediction[1])
        }