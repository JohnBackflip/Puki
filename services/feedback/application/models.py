from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum
from .database import Base
from datetime import datetime
from typing import Optional, Dict, Any

class RatingValue(str, Enum):
    ONE = "1"
    TWO = "2"
    THREE = "3"
    FOUR = "4"
    FIVE = "5"

class ReviewStatus(str, Enum):
    PENDING = "pending"
    RESPONDED = "responded"
    ARCHIVED = "archived"

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, index=True)
    user_id = Column(Integer, index=True)
    rating = Column(SQLEnum(RatingValue))
    comment = Column(String)
    status = Column(SQLEnum(ReviewStatus), default=ReviewStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with responses
    responses = relationship("Response", back_populates="review")

    @staticmethod
    def create(cursor, booking_id: int, user_id: int, rating: str, comment: str) -> Dict[str, Any]:
        query = """
            INSERT INTO reviews (booking_id, user_id, rating, comment)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (booking_id, user_id, rating, comment))
        cursor.execute("SELECT LAST_INSERT_ID()")
        review_id = cursor.fetchone()["LAST_INSERT_ID()"]
        
        return Review.get_by_id(cursor, review_id)
    
    @staticmethod
    def get_by_id(cursor, review_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM reviews WHERE id = %s"
        cursor.execute(query, (review_id,))
        return cursor.fetchone()
    
    @staticmethod
    def list_reviews(cursor, skip: int = 0, limit: int = 100) -> list[Dict[str, Any]]:
        query = "SELECT * FROM reviews LIMIT %s OFFSET %s"
        cursor.execute(query, (limit, skip))
        return cursor.fetchall()
    
    @staticmethod
    def update_status(cursor, review_id: int, status: str) -> bool:
        query = "UPDATE reviews SET status = %s WHERE id = %s"
        cursor.execute(query, (status, review_id))
        return cursor.rowcount > 0

class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id"))
    staff_id = Column(Integer, index=True)
    comment = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship with review
    review = relationship("Review", back_populates="responses")

    @staticmethod
    def create(cursor, review_id: int, staff_id: int, comment: str) -> Dict[str, Any]:
        query = """
            INSERT INTO responses (review_id, staff_id, comment)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query, (review_id, staff_id, comment))
        cursor.execute("SELECT LAST_INSERT_ID()")
        response_id = cursor.fetchone()["LAST_INSERT_ID()"]
        
        # Update review status
        Review.update_status(cursor, review_id, "RESPONDED")
        
        return Response.get_by_id(cursor, response_id)
    
    @staticmethod
    def get_by_id(cursor, response_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM responses WHERE id = %s"
        cursor.execute(query, (response_id,))
        return cursor.fetchone()

class ReviewMetrics(Base):
    __tablename__ = "review_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), index=True)
    average_rating = Column(Float)
    total_reviews = Column(Integer)
    rating_distribution = Column(String)  # JSON string of rating counts
    sentiment_score = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @staticmethod
    def create(cursor, review_id: int, sentiment_score: float) -> Dict[str, Any]:
        query = """
            INSERT INTO review_metrics (review_id, sentiment_score)
            VALUES (%s, %s)
        """
        cursor.execute(query, (review_id, sentiment_score))
        cursor.execute("SELECT LAST_INSERT_ID()")
        metric_id = cursor.fetchone()["LAST_INSERT_ID()"]
        
        return ReviewMetrics.get_by_id(cursor, metric_id)
    
    @staticmethod
    def get_by_id(cursor, metric_id: int) -> Optional[Dict[str, Any]]:
        query = "SELECT * FROM review_metrics WHERE id = %s"
        cursor.execute(query, (metric_id,))
        return cursor.fetchone()
    
    @staticmethod
    def get_aggregate_metrics(cursor) -> Dict[str, Any]:
        query = """
            SELECT 
                COUNT(*) as total_reviews,
                AVG(CASE 
                    WHEN rating = 'ONE' THEN 1
                    WHEN rating = 'TWO' THEN 2
                    WHEN rating = 'THREE' THEN 3
                    WHEN rating = 'FOUR' THEN 4
                    WHEN rating = 'FIVE' THEN 5
                END) as average_rating,
                AVG(rm.sentiment_score) as average_sentiment
            FROM reviews r
            LEFT JOIN review_metrics rm ON r.id = rm.review_id
        """
        cursor.execute(query)
        return cursor.fetchone()