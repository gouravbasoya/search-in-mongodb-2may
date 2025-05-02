from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

# CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Atlas connection
client = MongoClient("mongodb+srv://gouravbasoya3:6fU2JcfOWJ3FQUd3@grocery.ikbmetg.mongodb.net/")
db = client["groceries"]
collection = db["updated_products"]

# Product schema for response
class Product(BaseModel):
    item_name: str
    brand_name: str
    price: float
    category: str
    search_tags: List[str]

@app.get("/search")
def search_products(
    query: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None)
):
    search_filter = {}

    # Tag-based query
    if query:
        search_filter["search_tags"] = {"$regex": query, "$options": "i"}

    # Category filter
    if category:
        search_filter["category"] = category

    # Price filters
    price_filter = {}
    if min_price is not None:
        price_filter["$gte"] = min_price
    if max_price is not None:
        price_filter["$lte"] = max_price
    if price_filter:
        search_filter["price"] = price_filter

    # Search results
    results = list(collection.find(search_filter, {"_id": 0}))

    # Gather tags for similar suggestions
    tags = set()
    for product in results:
        tags.update(product["search_tags"])

    # Suggestions based on shared tags but not same items
    suggestions_filter = {
        "search_tags": {"$in": list(tags)},
        "item_name": {"$nin": [item["item_name"] for item in results]}
    }
    if category:
        suggestions_filter["category"] = category

    suggestions = list(collection.find(suggestions_filter, {"_id": 0}).limit(5))

    return {
        "results": results,
        "suggestions": suggestions
    }

@app.get("/categories")
def get_categories():
    categories = collection.distinct("category")
    return sorted(categories)
