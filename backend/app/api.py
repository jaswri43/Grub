from fastapi import APIRouter, HTTPException
from app.logic import optimize_order, filter_menu
from pydantic import BaseModel
from app.data import load_deals

router = APIRouter()

class OptimizeRequest(BaseModel):
    restaurant_id: str
    ingredient_requirements: list[str] # ex. ["chicken", "lettuce"]
    item_requirements: list[str] # ex. ["big_mac"]
    rewards_points: int

# Make sure backend is alive
@router.get("/health")
def health():
    return {"backend": "healthy"}

# GET specific restaurant
@router.get("/menu/{restaurant_id}")
def get_menu(restaurant_id: str):
    try:
        return filter_menu(restaurant_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
# GET cheapest items that satisfy each ingredient requirement
@router.post("/optimize")
def optimize(request: OptimizeRequest):
    menu = filter_menu(request.restaurant_id)
    deals = load_deals(request.restaurant_id)
    if menu is None:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    if request.rewards_points is None or request.rewards_points < 0:
        request.rewards_points = 0

    try:
        # return alternatives within +30% of cheapest, max 10 results by default
        options = optimize_order(
            menu,
            deals,
            request.item_requirements,
            request.ingredient_requirements,
            request.rewards_points,
            delta_pct=0.3,
            max_results=10,
        )

        return {"options": options}

    except HTTPException as e:
        raise e