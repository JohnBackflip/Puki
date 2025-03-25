# event/graphql_schema.py
import strawberry
from typing import List, Optional
from datetime import datetime
from services.event.models import Event, PriceAdjustment
from services.event.database import get_db

@strawberry.type
class EventType:
    id: int
    name: str
    description: str
    event_type: str
    start_date: datetime
    end_date: datetime
    location: str
    created_at: datetime
    updated_at: datetime

@strawberry.type
class PriceAdjustmentType:
    id: int
    event_id: int
    adjustment_type: str
    value: float
    created_at: datetime
    updated_at: datetime

@strawberry.type
class Query:
    @strawberry.field
    def event(self, id: int) -> Optional[EventType]:
        db = next(get_db())
        with db.cursor() as cursor:
            result = Event.get_by_id(cursor, id)
            if result:
                return EventType(**result)
            return None
    
    @strawberry.field
    def events(self) -> List[EventType]:
        db = next(get_db())
        with db.cursor() as cursor:
            results = Event.list_events(cursor)
            return [EventType(**result) for result in results]
    
    @strawberry.field
    def price_adjustment(self, id: int) -> Optional[PriceAdjustmentType]:
        db = next(get_db())
        with db.cursor() as cursor:
            result = PriceAdjustment.get_by_id(cursor, id)
            if result:
                return PriceAdjustmentType(**result)
            return None
    
    @strawberry.field
    def price_adjustments(self, event_id: Optional[int] = None) -> List[PriceAdjustmentType]:
        db = next(get_db())
        with db.cursor() as cursor:
            if event_id:
                results = PriceAdjustment.get_by_event(cursor, event_id)
            else:
                results = PriceAdjustment.get_by_event(cursor, None)
            return [PriceAdjustmentType(**result) for result in results]

@strawberry.type
class Mutation:
    @strawberry.mutation
    def create_event(
        self,
        name: str,
        description: str,
        event_type: str,
        start_date: datetime,
        end_date: datetime,
        location: str
    ) -> EventType:
        db = next(get_db())
        with db.cursor() as cursor:
            result = Event.create(cursor, name, description, event_type, start_date, end_date, location)
            db.commit()
            return EventType(**result)
    
    @strawberry.mutation
    def create_price_adjustment(
        self,
        event_id: int,
        adjustment_type: str,
        value: float
    ) -> PriceAdjustmentType:
        db = next(get_db())
        with db.cursor() as cursor:
            result = PriceAdjustment.create(cursor, event_id, adjustment_type, value)
            db.commit()
            return PriceAdjustmentType(**result)

schema = strawberry.Schema(query=Query, mutation=Mutation) 