from fastapi import FastAPI, Depends, HTTPException, Security
from sqlalchemy.orm import Session
from typing import List, Dict
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
import pandas as pd
from datetime import datetime, timedelta
import joblib
import os
from prometheus_client import make_asgi_app

from . import models, schemas, database
from .database import engine
from middleware.auth import require_auth
from monitoring.prometheus import track_request, REQUEST_COUNT
from monitoring.tracing import setup_tracing
from textblob import TextBlob
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

models.Base.metadata.create_all(bind=engine)

app = FastAPI()
setup_tracing(app, "ml-service")

# Add prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Load or train models
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

def get_or_train_model(name, model_class, **kwargs):
    model_path = os.path.join(MODELS_DIR, f"{name}.joblib")
    if os.path.exists(model_path):
        return joblib.load(model_path)
    model = model_class(**kwargs)
    joblib.dump(model, model_path)
    return model

# Initialize models
customer_segmentation = get_or_train_model(
    "customer_segmentation",
    KMeans,
    n_clusters=4,
    random_state=42
)

revenue_predictor = get_or_train_model(
    "revenue_predictor",
    RandomForestRegressor,
    n_estimators=100,
    random_state=42
)

maintenance_predictor = get_or_train_model(
    "maintenance_predictor",
    RandomForestClassifier,
    n_estimators=100,
    random_state=42
)

staff_assignment_model = get_or_train_model(
    "staff_assignment",
    RandomForestClassifier,
    n_estimators=100,
    random_state=42
)

@app.post("/predict/customer-segments")
@require_auth()
@track_request()
async def predict_customer_segments(
    data: Dict,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    customers = pd.DataFrame(data["customers"])
    
    # Feature engineering
    features = customers[[
        'total_stays',
        'total_spent',
        'avg_booking_value',
        'cancellation_rate'
    ]].values
    
    # Scale features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    # Predict segments
    segments = customer_segmentation.predict(scaled_features)
    
    # Map segments to meaningful descriptions
    segment_descriptions = {
        0: "Budget Travelers",
        1: "Luxury Guests",
        2: "Business Travelers",
        3: "Family Vacationers"
    }
    
    return {
        "segments": segments.tolist(),
        "segment_descriptions": segment_descriptions
    }

@app.post("/predict/revenue")
@require_auth()
@track_request()
async def predict_revenue(
    features: Dict,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Convert features to DataFrame
    df = pd.DataFrame([features])
    
    # Make prediction
    predicted_revenue = revenue_predictor.predict(df)
    
    return {
        "predicted_revenue": float(predicted_revenue[0]),
        "confidence_interval": {
            "lower": float(predicted_revenue[0] * 0.9),
            "upper": float(predicted_revenue[0] * 1.1)
        }
    }

@app.post("/predict/maintenance")
@require_auth()
@track_request()
async def predict_maintenance(
    data: Dict,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    # Convert input to DataFrame
    df = pd.DataFrame([{
        'last_maintenance_days': data['last_maintenance_days'],
        'occupancy_rate': data['occupancy_rate'],
        'reported_issues': data['reported_issues'],
        'age_in_years': data['age_in_years']
    }])
    
    # Make prediction
    needs_maintenance = maintenance_predictor.predict(df)[0]
    confidence = float(max(maintenance_predictor.predict_proba(df)[0]))
    
    # Get feature importances
    importances = dict(zip(
        df.columns,
        maintenance_predictor.feature_importances_
    ))
    
    return {
        "needs_maintenance": bool(needs_maintenance),
        "confidence": confidence,
        "contributing_factors": {
            k: float(v) for k, v in importances.items()
        }
    }

@app.post("/predict/staff-assignment")
@require_auth()
@track_request()
async def predict_staff_assignment(
    data: Dict,
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    staff = pd.DataFrame(data["staff"])
    rooms = pd.DataFrame(data["rooms"])
    
    # Feature engineering for staff-room pairs
    assignments = []
    for _, staff_member in staff.iterrows():
        for _, room in rooms.iterrows():
            score = staff_assignment_model.predict_proba([[
                staff_member["experience_years"],
                staff_member["performance_rating"],
                room["cleaning_difficulty"],
                room["time_estimate"]
            ]])[0][1]
            
            assignments.append({
                "staff_id": staff_member["id"],
                "room_id": room["id"],
                "score": float(score)
            })
    
    # Sort assignments by score
    assignments.sort(key=lambda x: x["score"], reverse=True)
    
    # Assign rooms to staff (greedy algorithm)
    final_assignments = []
    assigned_rooms = set()
    assigned_staff = set()
    
    for assignment in assignments:
        if (assignment["room_id"] not in assigned_rooms and 
            assignment["staff_id"] not in assigned_staff):
            final_assignments.append(assignment)
            assigned_rooms.add(assignment["room_id"])
            assigned_staff.add(assignment["staff_id"])
    
    return {
        "assignments": final_assignments
    }

@app.post("/analyze/trends")
@require_auth()
@track_request()
async def analyze_trends(
    data: List[Dict],
    db: Session = Depends(database.get_db),
    user_data: dict = Security(require_auth())
):
    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    
    # Calculate trends
    revenue_trend = np.polyfit(range(len(df)), df['revenue'], 1)[0]
    booking_trend = np.polyfit(range(len(df)), df['bookings'], 1)[0]
    occupancy_trend = np.polyfit(range(len(df)), df['occupancy'], 1)[0]
    
    # Calculate seasonality
    df['month'] = df['date'].dt.month
    monthly_revenue = df.groupby('month')['revenue'].mean()
    peak_months = monthly_revenue.nlargest(3).index.tolist()
    
    return {
        "trends": {
            "revenue": float(revenue_trend),
            "bookings": float(booking_trend),
            "occupancy": float(occupancy_trend)
        },
        "peak_months": peak_months,
        "analysis": {
            "revenue_growth": "positive" if revenue_trend > 0 else "negative",
            "booking_growth": "positive" if booking_trend > 0 else "negative",
            "occupancy_growth": "positive" if occupancy_trend > 0 else "negative"
        }
    }

@app.post("/analyze/sentiment")
@require_auth()
async def analyze_sentiment(
    text_data: dict,
    user_data: dict = Security(require_auth())
):
    text = text_data.get("text")
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")
    
    # Analyze sentiment using TextBlob
    analysis = TextBlob(text)
    
    # Extract keywords (nouns and adjectives)
    words = analysis.tags
    keywords = [word for word, tag in words if tag.startswith(('JJ', 'NN'))]
    
    # Calculate sentiment score (-1 to 1)
    sentiment_score = analysis.sentiment.polarity
    
    # Determine sentiment label
    if sentiment_score > 0:
        sentiment = "positive"
    elif sentiment_score < 0:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    return {
        "sentiment": sentiment,
        "score": sentiment_score,
        "keywords": keywords[:5]  # Return top 5 keywords
    }