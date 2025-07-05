#!/usr/bin/env python3
"""
Test script for the LangGraph orchestrator
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.llm_service import LLMService
from agents.support_agent import SupportAppAgent
from agents.product_agent import ProductAppAgent
from agents.orchestrator import LangGraphOrchestrator

async def test_langgraph_orchestrator():
    """Test the LangGraph orchestrator with various queries"""
    
    print("🚀 Testing LangGraph Orchestrator...")
    
    # Load environment variables
    load_dotenv()
    
    # Initialize services
    llm_service = LLMService()
    
    # Initialize agents
    support_agent = SupportAppAgent(llm_service)
    product_agent = ProductAppAgent(llm_service)
    
    # Initialize LangGraph orchestrator
    orchestrator = LangGraphOrchestrator(
        support_agent=support_agent,
        product_agent=product_agent,
        llm_service=llm_service
    )
    
    # Test queries
    test_queries = [
        "I need help with my password reset",
        "What products do you have available?",
        "Tell me about your pricing",
        "How do I contact support?",
        "What's the weather like today?"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test {i}: {query}")
        print("-" * 50)
        
        try:
            result = await orchestrator.process_message(
                message=query,
                user_id="test_user",
                session_id="test_session"
            )
            
            print(f"✅ Intent: {result.get('intent', 'unknown')}")
            print(f"✅ Response: {result.get('response', 'No response')[:200]}...")
            print(f"✅ Processing time: {result.get('processing_time', 0):.2f}s")
            
            agent_responses = result.get('agent_responses', [])
            for agent_resp in agent_responses:
                print(f"   🤖 {agent_resp.get('agent_name', 'Unknown')}: {agent_resp.get('response', '')[:100]}...")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    print("\n🎉 LangGraph Orchestrator test completed!")

if __name__ == "__main__":
    asyncio.run(test_langgraph_orchestrator()) 