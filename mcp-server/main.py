from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import time
import os
from contextlib import asynccontextmanager

from services.llm_service import LLMService
from services.vector_service import VectorService
from agents.support_agent import SupportAppAgent
from agents.product_agent import ProductAppAgent
from agents.knowledge_agent import KnowledgeAgent
from agents.orchestrator import AgentOrchestrator

# Global services
llm_service = None
vector_service = None
orchestrator = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services and agents on startup"""
    global llm_service, vector_service, orchestrator
    
    print("Initializing MCP Server...")
    
    # Initialize services
    llm_service = LLMService()
    vector_service = VectorService()
    await vector_service.initialize()
    
    # Initialize agents
    support_agent = SupportAppAgent(llm_service)
    product_agent = ProductAppAgent(llm_service)
    knowledge_agent = KnowledgeAgent(llm_service, vector_service)
    
    # Initialize orchestrator
    orchestrator = AgentOrchestrator(
        support_agent=support_agent,
        product_agent=product_agent,
        knowledge_agent=knowledge_agent,
        llm_service=llm_service
    )
    
    # Initialize vector database with sample data
    await knowledge_agent.initialize_vector_data()
    
    print("MCP Server initialized successfully!")
    yield
    
    # Cleanup on shutdown
    print("Shutting down MCP Server...")

app = FastAPI(
    title="MCP Server - Multi-Agent Orchestration",
    description="FastAPI server with LangChain agents for agentic AI demo",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatMessage(BaseModel):
    message: str
    user_id: Optional[str] = "anonymous"
    session_id: Optional[str] = "default"

class AgentResponse(BaseModel):
    agent_name: str
    response: str
    processing_time: float
    sources: Optional[List[str]] = None

class ChatResponse(BaseModel):
    response: str
    agent_responses: List[AgentResponse]
    total_processing_time: float
    session_id: str

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "service": "mcp-server",
        "agents_initialized": orchestrator is not None
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """Main chat endpoint that orchestrates agent responses"""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="MCP Server not initialized")
    
    start_time = time.time()
    
    try:
        # Process message through orchestrator
        result = await orchestrator.process_message(
            message.message,
            user_id=message.user_id,
            session_id=message.session_id
        )
        
        total_time = time.time() - start_time
        
        return ChatResponse(
            response=result["response"],
            agent_responses=result["agent_responses"],
            total_processing_time=total_time,
            session_id=message.session_id
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")

@app.get("/agents/status")
async def get_agents_status():
    """Get status of all agents"""
    if not orchestrator:
        return {"status": "not_initialized"}
    
    return {
        "status": "active",
        "agents": {
            "support_agent": "active",
            "product_agent": "active",
            "knowledge_agent": "active"
        },
        "services": {
            "llm_service": "active",
            "vector_service": "active"
        }
    }

@app.get("/config")
async def get_config():
    """Get current configuration"""
    return {
        "llm_backend": {
            "use_ollama": os.getenv("USE_OLLAMA", "true").lower() == "true",
            "use_openai": os.getenv("USE_OPENAI", "false").lower() == "true",
            "use_hf": os.getenv("USE_HF", "false").lower() == "true",
            "ollama_model": os.getenv("OLLAMA_MODEL", "gemma:2b")
        },
        "vector_db": {
            "use_pinecone": os.getenv("USE_PINECONE_API", "false").lower() == "true",
            "use_local_vectordb": os.getenv("USE_LOCAL_VECTORDB", "true").lower() == "true",
            "local_vectordb_type": os.getenv("LOCAL_VECTORDB_TYPE", "chroma")
        },
        "environment": os.getenv("ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 