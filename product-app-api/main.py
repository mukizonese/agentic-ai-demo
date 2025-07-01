from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os

app = FastAPI(
    title="Product App API",
    description="Mock Product App API for Agentic AI Demo",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class Product(BaseModel):
    id: str
    name: str
    description: str
    category: str
    price: float
    features: List[str]
    specifications: Dict[str, str]
    availability: str
    rating: float
    reviews_count: int

# Mock data - Products
PRODUCTS = [
    {
        "id": "1",
        "name": "SmartWidget 3000",
        "description": "Smart home automation device with AI-powered features. Control your entire home with voice commands and intelligent scheduling.",
        "category": "Smart Home",
        "price": 299.99,
        "features": [
            "Voice Control",
            "AI Scheduling",
            "Mobile App Integration",
            "Energy Monitoring",
            "Multi-room Support"
        ],
        "specifications": {
            "Connectivity": "WiFi 6, Bluetooth 5.0",
            "Power": "AC 100-240V",
            "Dimensions": "4.5 x 4.5 x 2.0 inches",
            "Weight": "1.2 lbs",
            "Warranty": "2 years"
        },
        "availability": "In Stock",
        "rating": 4.5,
        "reviews_count": 1247
    },
    {
        "id": "2",
        "name": "PowerHub Pro",
        "description": "Portable power bank with solar charging capability. Perfect for outdoor activities and emergency backup power.",
        "category": "Electronics",
        "price": 159.99,
        "features": [
            "Solar Charging",
            "Fast Charging",
            "Wireless Charging Pad",
            "LED Flashlight",
            "Waterproof Design"
        ],
        "specifications": {
            "Capacity": "20,000mAh",
            "Solar Panel": "5W Monocrystalline",
            "Ports": "2x USB-C, 2x USB-A",
            "Weight": "1.8 lbs",
            "Warranty": "1 year"
        },
        "availability": "In Stock",
        "rating": 4.3,
        "reviews_count": 892
    },
    {
        "id": "3",
        "name": "EcoSmart Thermostat",
        "description": "Energy-efficient smart thermostat with learning algorithms. Automatically adjusts temperature based on your habits and preferences.",
        "category": "Smart Home",
        "price": 249.99,
        "features": [
            "Learning Algorithm",
            "Remote Control",
            "Energy Reports",
            "Geofencing",
            "Voice Assistant Compatible"
        ],
        "specifications": {
            "Display": "3.5 inch Color LCD",
            "Connectivity": "WiFi, Thread",
            "Compatibility": "Most HVAC systems",
            "Installation": "DIY or Professional",
            "Warranty": "3 years"
        },
        "availability": "In Stock",
        "rating": 4.7,
        "reviews_count": 2156
    },
    {
        "id": "4",
        "name": "AquaPure Filter System",
        "description": "Advanced water filtration system with multi-stage purification. Removes 99.9% of contaminants and improves taste.",
        "category": "Home & Kitchen",
        "price": 399.99,
        "features": [
            "Multi-Stage Filtration",
            "UV Sterilization",
            "Smart Monitoring",
            "Easy Installation",
            "Filter Life Indicator"
        ],
        "specifications": {
            "Flow Rate": "2.5 GPM",
            "Filter Life": "6 months",
            "Dimensions": "14 x 8 x 20 inches",
            "Installation": "Under-sink",
            "Warranty": "5 years"
        },
        "availability": "Limited Stock",
        "rating": 4.6,
        "reviews_count": 743
    },
    {
        "id": "5",
        "name": "FitTracker Elite",
        "description": "Advanced fitness tracker with heart rate monitoring, GPS, and comprehensive health analytics. Track your fitness journey with precision.",
        "category": "Fitness",
        "price": 199.99,
        "features": [
            "Heart Rate Monitor",
            "GPS Tracking",
            "Sleep Analysis",
            "Water Resistance",
            "7-day Battery Life"
        ],
        "specifications": {
            "Display": "1.4 inch AMOLED",
            "Battery": "Up to 7 days",
            "Water Resistance": "5ATM",
            "Sensors": "Heart Rate, GPS, Accelerometer",
            "Warranty": "2 years"
        },
        "availability": "In Stock",
        "rating": 4.4,
        "reviews_count": 1689
    }
]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "product-app-api"}

@app.get("/products", response_model=List[Product])
async def get_products():
    """Get all products"""
    return PRODUCTS

@app.get("/products/{product_id}", response_model=Product)
async def get_product(product_id: str):
    """Get a specific product by ID"""
    for product in PRODUCTS:
        if product["id"] == product_id:
            return product
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/products/search/{query}")
async def search_products(query: str):
    """Search products by query"""
    query_lower = query.lower()
    results = []
    
    for product in PRODUCTS:
        if (query_lower in product["name"].lower() or 
            query_lower in product["description"].lower() or
            query_lower in product["category"].lower() or
            any(query_lower in feature.lower() for feature in product["features"])):
            results.append(product)
    
    return results

@app.get("/products/category/{category}")
async def get_products_by_category(category: str):
    """Get products by category"""
    results = [product for product in PRODUCTS if product["category"].lower() == category.lower()]
    return results

@app.get("/products/price-range/{min_price}/{max_price}")
async def get_products_by_price_range(min_price: float, max_price: float):
    """Get products within a price range"""
    results = [product for product in PRODUCTS if min_price <= product["price"] <= max_price]
    return results

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port) 