from fastapi import FastAPI, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from prometheus_client import make_asgi_app
import strawberry
from strawberry.fastapi import GraphQLRouter

from services.event import models, schemas
from services.event.database import get_db
from services.event.graphql_schema import schema
from services.room.middleware.auth import require_auth, require_auth_security
from services.monitoring.prometheus import track_request, REQUEST_COUNT
from services.monitoring.tracing import setup_tracing

app = FastAPI(title="Event Service")
setup_tracing(app, "event-service")

# Add prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Add GraphQL endpoint
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

@app.post("/events", response_model=schemas.Event)
@require_auth(["admin"])
async def create_event(event: schemas.EventCreate, user_data: dict = Depends(require_auth_security), db = Depends(get_db)):
    with db.cursor() as cursor:
        try:
            result = models.Event.create(
                cursor,
                event.name,
                event.description,
                event.event_type,
                event.start_date,
                event.end_date,
                event.location
            )
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/events", response_model=List[schemas.Event])
async def list_events(
    event_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        return models.Event.list_events(cursor, event_type, start_date, end_date)

@app.get("/events/{event_id}", response_model=schemas.Event)
async def get_event(event_id: int, db = Depends(get_db)):
    with db.cursor() as cursor:
        event = models.Event.get_by_id(cursor, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        return event

@app.post("/events/price-adjustments", response_model=schemas.PriceAdjustment)
@require_auth(["admin"])
async def create_price_adjustment(
    adjustment: schemas.PriceAdjustmentCreate,
    user_data: dict = Depends(require_auth_security),
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        # Check if event exists
        event = models.Event.get_by_id(cursor, adjustment.event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        try:
            result = models.PriceAdjustment.create(
                cursor,
                adjustment.event_id,
                adjustment.adjustment_type,
                adjustment.value
            )
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@app.get("/events/{event_id}/price-adjustments", response_model=List[schemas.PriceAdjustment])
async def list_price_adjustments(event_id: int, db = Depends(get_db)):
    with db.cursor() as cursor:
        # Check if event exists
        event = models.Event.get_by_id(cursor, event_id)
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return models.PriceAdjustment.get_by_event(cursor, event_id)

@app.get("/events/price-adjustments/{adjustment_id}", response_model=schemas.PriceAdjustment)
async def get_price_adjustment(adjustment_id: int, db = Depends(get_db)):
    with db.cursor() as cursor:
        adjustment = models.PriceAdjustment.get_by_id(cursor, adjustment_id)
        if not adjustment:
            raise HTTPException(status_code=404, detail="Price adjustment not found")
        return adjustment

@app.put("/events/price-adjustments/{adjustment_id}", response_model=schemas.PriceAdjustment)
@require_auth(["admin"])
async def update_price_adjustment(
    adjustment_id: int,
    adjustment: schemas.PriceAdjustmentUpdate,
    user_data: dict = Depends(require_auth_security),
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        # Check if adjustment exists
        existing = models.PriceAdjustment.get_by_id(cursor, adjustment_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Price adjustment not found")
        
        try:
            result = models.PriceAdjustment.update(
                cursor,
                adjustment_id,
                adjustment_type=adjustment.adjustment_type,
                value=adjustment.value
            )
            db.commit()
            return result
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e))

@app.delete("/events/price-adjustments/{adjustment_id}")
@require_auth(["admin"])
async def delete_price_adjustment(
    adjustment_id: int,
    user_data: dict = Depends(require_auth_security),
    db = Depends(get_db)
):
    with db.cursor() as cursor:
        # Check if adjustment exists
        existing = models.PriceAdjustment.get_by_id(cursor, adjustment_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Price adjustment not found")
        
        try:
            if models.PriceAdjustment.delete(cursor, adjustment_id):
                db.commit()
                return {"message": "Price adjustment deleted successfully"}
            db.rollback()
            raise HTTPException(status_code=400, detail="Failed to delete price adjustment")
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=str(e)) 