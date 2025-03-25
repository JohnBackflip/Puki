# main.py
from fastapi import FastAPI, HTTPException, status, Depends
from pydantic import BaseModel
from datetime import date
from typing import List, Optional
import uvicorn
from middleware.auth import require_auth  # Import the middleware

app = FastAPI(title="Promotion Service")

class Promotion(BaseModel):
    id: Optional[int] = None
    name: str
    code: str
    start_date: date
    end_date: date
    discount_percentage: int
    room_type: str

# Mock database
promotions_db = []
promotion_id_counter = 1

@app.post("/promotions/", response_model=Promotion, status_code=status.HTTP_201_CREATED)
async def create_promotion(promotion: Promotion):
    global promotion_id_counter
    promotion.id = promotion_id_counter
    promotions_db.append(promotion)
    promotion_id_counter += 1
    return promotion

@app.get("/promotions/", response_model=List[Promotion])
async def list_promotions():
    return promotions_db

@app.get("/promotions/{promotion_id}", response_model=Promotion)
async def get_promotion(promotion_id: int):
    for promo in promotions_db:
        if promo.id == promotion_id:
            return promo
    raise HTTPException(status_code=404, detail="Promotion not found")

@app.put("/promotions/{promotion_id}", response_model=Promotion)
async def update_promotion(promotion_id: int, promotion: Promotion):
    for i, promo in enumerate(promotions_db):
        if promo.id == promotion_id:
            promotion.id = promotion_id
            promotions_db[i] = promotion
            return promotion
    raise HTTPException(status_code=404, detail="Promotion not found")

@app.delete("/promotions/{promotion_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_promotion(promotion_id: int):
    for i, promo in enumerate(promotions_db):
        if promo.id == promotion_id:
            promotions_db.pop(i)
            return
    raise HTTPException(status_code=404, detail="Promotion not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)