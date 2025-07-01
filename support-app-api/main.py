from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import os

app = FastAPI(
    title="Support App API",
    description="Mock Support App API for Agentic AI Demo",
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
class SupportArticle(BaseModel):
    id: str
    title: str
    content: str
    category: str
    tags: List[str]
    created_at: str
    updated_at: str

# Mock data - Support Articles
SUPPORT_ARTICLES = [
    {
        "id": "1",
        "title": "Resetting your password",
        "content": "Go to settings, click Reset Password, enter your email, check your inbox for reset link, click the link and create a new password. Make sure your new password is strong and unique.",
        "category": "Account",
        "tags": ["password", "reset", "security", "login"],
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-15T10:00:00Z"
    },
    {
        "id": "2",
        "title": "Updating profile information",
        "content": "Click on profile picture in top right corner, select Edit Profile, update your information including name, email, phone number, and profile picture. Save changes when done.",
        "category": "Profile",
        "tags": ["profile", "update", "personal", "information"],
        "created_at": "2024-01-16T14:30:00Z",
        "updated_at": "2024-01-16T14:30:00Z"
    },
    {
        "id": "3",
        "title": "Troubleshooting connection issues",
        "content": "If you're experiencing connection problems, try these steps: 1) Check your internet connection, 2) Clear browser cache and cookies, 3) Disable browser extensions, 4) Try a different browser, 5) Contact support if issues persist.",
        "category": "Technical",
        "tags": ["connection", "troubleshooting", "network", "browser"],
        "created_at": "2024-01-17T09:15:00Z",
        "updated_at": "2024-01-17T09:15:00Z"
    },
    {
        "id": "4",
        "title": "Managing notifications",
        "content": "You can customize your notification preferences in Settings > Notifications. Choose which types of notifications you want to receive via email, push notifications, or SMS. You can also set quiet hours.",
        "category": "Settings",
        "tags": ["notifications", "settings", "preferences", "email"],
        "created_at": "2024-01-18T16:45:00Z",
        "updated_at": "2024-01-18T16:45:00Z"
    },
    {
        "id": "5",
        "title": "Billing and subscription management",
        "content": "Access your billing information through Account > Billing. Here you can view your current plan, update payment methods, download invoices, and manage your subscription. You can upgrade, downgrade, or cancel anytime.",
        "category": "Billing",
        "tags": ["billing", "subscription", "payment", "invoice"],
        "created_at": "2024-01-19T11:20:00Z",
        "updated_at": "2024-01-19T11:20:00Z"
    }
]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "support-app-api"}

@app.get("/support_articles", response_model=List[SupportArticle])
async def get_support_articles():
    """Get all support articles"""
    return SUPPORT_ARTICLES

@app.get("/support_articles/{article_id}", response_model=SupportArticle)
async def get_support_article(article_id: str):
    """Get a specific support article by ID"""
    for article in SUPPORT_ARTICLES:
        if article["id"] == article_id:
            return article
    raise HTTPException(status_code=404, detail="Support article not found")

@app.get("/support_articles/search/{query}")
async def search_support_articles(query: str):
    """Search support articles by query"""
    query_lower = query.lower()
    results = []
    
    for article in SUPPORT_ARTICLES:
        if (query_lower in article["title"].lower() or 
            query_lower in article["content"].lower() or
            any(query_lower in tag.lower() for tag in article["tags"]) or
            query_lower in article["category"].lower()):
            results.append(article)
    
    return results

@app.get("/support_articles/category/{category}")
async def get_articles_by_category(category: str):
    """Get support articles by category"""
    results = [article for article in SUPPORT_ARTICLES if article["category"].lower() == category.lower()]
    return results

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port) 