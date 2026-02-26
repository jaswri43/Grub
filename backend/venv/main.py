from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

class OptimizeRequest(BaseModel):
    restaurant_id: str
    requirements: list[str]

app = FastAPI()

# Necessary middleware to connect fronend to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Make sure backend is alive
@app.get("/")
def root():
    return {"status": "Backend running"}

@app.get("/health")
def health():
    return {"backend": "healthy"}


# GET a list of supported restaurants
@app.get("/restaurants")
def restaurants():
    return {"restaurants": [
            {
                "id": "mcdonalds",
                "name": "McDonald's",
            },
            {
                "id": "tacobell",
                "name": "Taco Bell",
                }
        ]
    }


# Stand-in database of menu items
MENUS = {
    "mcdonalds": {
        "restaurant": "McDonald's",
        "menu": [
            {
                "id": 1,
                "slug": "big_mac",
                "name": "Big Mac",
                "ingredients": ["bun", "beef","lettuce", "cheese"],
                "price": 5.29
            },
            {
                "id": 2,
                "slug": "chicken_nuggets_6",
                "name": "6 Piece Chicken McNuggets",
                "ingredients": ["chicken"],
                "price": 4.99
            }
        ]
    },
    
    "tacobell": {
        "restaurant": "Taco Bell",
        "menu": [
            {
                "id": 1,
                "slug": "beef_taco",
                "name": "Beef Taco",
                "ingredients": ["beef", "tortilla", "lettuce", "cheese"],
                "price": 1.99
            },
            {
                "id": 2,
                "slug": "chicken_burrito",
                "name": "Chicken Burrito",
                "ingredients": ["chicken","tortilla", "rice", "beans"],
                "price": 3.49
            }
        ]
    }
}


# GET specific restaurant
@app.get("/menu/{restaurant_id}")
def get_menu(restaurant_id: str):
    if restaurant_id not in MENUS:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    return MENUS[restaurant_id]


# GET filtered menu based on ingredients
@app.get("/menu/{restaurant_id}/filter")
def filter_menu(restaurant_id: str, include: str):
    if restaurant_id not in MENUS:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    requested_ingredients = include.split(",")
    menu = MENUS[restaurant_id]
    
    results = []
    
    for item in menu["menu"]:
        for ingredient in requested_ingredients:
            if ingredient in item["ingredients"]:
                results.append(item)
                break

    return results

# GET cheapest items that satisfy each ingredient requirement
@app.post("/optimize")
def optimize(request: OptimizeRequest):
    if request.restaurant_id not in MENUS:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    menu = MENUS[request.restaurant_id]

    selected_items = []
    total_price = 0.0
    used_item_ids = set()
    
    for requirement in request.requirements:
        matches = [
            item for item in menu["menu"]
            if requirement in item["ingredients"]
            and item["id"] not in used_item_ids
        ]
        
        if not matches:
            raise HTTPException(status_code=400, detail=f"No item satisfies requirement: {requirement}")

        chosen = min(matches, key=lambda item: item["price"])
        selected_items.append(chosen)
        used_item_ids.add(chosen["id"])
        total_price += chosen["price"]
        
    return {
        "items": selected_items,
        "total_price": total_price
    }