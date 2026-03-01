import json
from pathlib import Path

DATA_PATH = Path("data")

def load_menu(restaurant_id: str):
    path = DATA_PATH / "menus" / f"{restaurant_id}.json"
    
    with open(path) as f:
        return json.load(f)

def load_deals(restaurant_id: str):
    path = DATA_PATH / "deals" / f"{restaurant_id}.json"
    
    if not path.exists():
        return []
    
    with open(path) as f:
        return json.load(f)