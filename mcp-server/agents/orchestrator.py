import asyncio
import time
from typing import Dict, Any, List, Optional, TypedDict, Annotated
import logging
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
import aiohttp
from dataclasses import dataclass

@dataclass
class AgentResponse:
    """Structured response from agents"""
    agent_name: str
    response: str
    handled: bool
    processing_time: float
    sources: List[str]
    error: Optional[str] = None

# Define the state structure for LangGraph
class AgentState(TypedDict):
    """State structure for the agent orchestration graph"""
    messages: Annotated[List[Dict[str, Any]], add_messages]
    user_message: str
    user_id: str
    session_id: str
    intent: Optional[str]
    intent_confidence: Optional[float]
    entities: List[str]
    agent_responses: List[AgentResponse]
    current_agent: Optional[str]
    error: Optional[str]
    retry_count: int
    processing_start_time: float

class LangGraphOrchestrator:
    """LangGraph-based orchestrator for agent responses and conversation flow"""
    
    def __init__(self, support_agent, product_agent, llm_service):
        self.support_agent = support_agent
        self.product_agent = product_agent
        self.llm_service = llm_service
        
        # Session storage for conversation context
        self.sessions = {}
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("LangGraphOrchestrator")
        
        # Initialize checkpoint memory for state persistence
        self.memory = MemorySaver()
        
        # Build the LangGraph workflow
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow with nodes and edges"""
        
        # Create the state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("intent_detection", self._intent_detection_node)
        workflow.add_node("support_agent", self._support_agent_node)
        workflow.add_node("product_agent", self._product_agent_node)
        workflow.add_node("fallback_handler", self._fallback_handler_node)
        workflow.add_node("response_synthesis", self._response_synthesis_node)
        
        # Set entry point
        workflow.set_entry_point("intent_detection")
        
        # Define conditional edges based on intent
        workflow.add_conditional_edges(
            "intent_detection",
            self._route_by_intent,
            {
                "support_agent": "support_agent",
                "product_agent": "product_agent", 
                "fallback_handler": "fallback_handler"
            }
        )
        
        # Add edges from agents to synthesis
        workflow.add_edge("support_agent", "response_synthesis")
        workflow.add_edge("product_agent", "response_synthesis")
        workflow.add_edge("fallback_handler", "response_synthesis")
        
        # Set end point
        workflow.add_edge("response_synthesis", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    async def _intent_detection_node(self, state: AgentState) -> AgentState:
        """Node for detecting user intent"""
        self.logger.info(f"Detecting intent for message: {state['user_message']}")
        
        try:
            # Extract intent using LLM service
            intent_info = await self.llm_service.extract_intent(state['user_message'])
            
            return {
                **state,
                "intent": intent_info.get("intent", "general_question"),
                "intent_confidence": intent_info.get("confidence", 0.5),
                "entities": intent_info.get("entities", [])
            }
        except Exception as e:
            self.logger.error(f"Error in intent detection: {str(e)}")
            return {
                **state,
                "intent": "general_question",
                "intent_confidence": 0.3,
                "entities": [],
                "error": f"Intent detection error: {str(e)}"
            }
    
    def _route_by_intent(self, state: AgentState) -> str:
        """Route to appropriate agent based on intent"""
        intent = state.get("intent", "general_question")
        confidence = state.get("intent_confidence", 0.0)
        
        # If confidence is low, route to fallback
        if confidence is not None and confidence < 0.4:
            return "fallback_handler"
        
        # Route based on intent
        if intent == "support":
            return "support_agent"
        elif intent == "product_info":
            return "product_agent"
        else:
            return "fallback_handler"
    
    async def _support_agent_node(self, state: AgentState) -> AgentState:
        """Node for processing support agent queries with retry logic"""
        self.logger.info("Processing with Support Agent...")
        
        response = await self._call_agent_with_retry(
            self.support_agent.process_query,
            state['user_message'],
            max_retries=1
        )
        
        return {
            **state,
            "agent_responses": [response],
            "current_agent": "Support Agent"
        }
    
    async def _product_agent_node(self, state: AgentState) -> AgentState:
        """Node for processing product agent queries with retry logic"""
        self.logger.info("Processing with Product Agent...")
        
        response = await self._call_agent_with_retry(
            self.product_agent.process_query,
            state['user_message'],
            max_retries=1
        )
        
        return {
            **state,
            "agent_responses": [response],
            "current_agent": "Product Agent"
        }
    
    async def _fallback_handler_node(self, state: AgentState) -> AgentState:
        """Node for handling general queries and fallbacks"""
        self.logger.info("Processing with Fallback Handler...")
        
        try:
            # Generate a general response
            prompt = f"""User message: {state['user_message']}

This is a general inquiry that doesn't fall into specific support or product categories. Please provide a helpful, friendly response that:
1. Acknowledges the user's question
2. Provides any general guidance you can
3. Suggests how they might get more specific help
4. Maintains a professional, helpful tone"""
            
            result = await self.llm_service.generate_text(prompt, max_tokens=300)
            
            response = AgentResponse(
                agent_name="General Assistant",
                response=result.get("text", "I'm here to help! How can I assist you today?"),
                handled=True,
                processing_time=0.1,
                sources=[]
            )
            
            return {
                **state,
                "agent_responses": [response],
                "current_agent": "General Assistant"
            }
            
        except Exception as e:
            self.logger.error(f"Error in fallback handler: {str(e)}")
            error_response = AgentResponse(
                agent_name="Error Handler",
                response=f"I encountered an error while processing your request: {str(e)}",
                handled=False,
                processing_time=0.0,
                sources=[],
                error=str(e)
            )
            
            return {
                **state,
                "agent_responses": [error_response],
                "current_agent": "Error Handler",
                "error": str(e)
            }
    
    async def _response_synthesis_node(self, state: AgentState) -> AgentState:
        """Node for synthesizing final response from agent responses"""
        self.logger.info("Synthesizing final response...")
        
        agent_responses = state.get("agent_responses", [])
        
        if not agent_responses:
            final_response = "I'm sorry, I couldn't process your request. Please try again."
        elif len(agent_responses) == 1:
            final_response = agent_responses[0].response
        else:
            # Multiple agent responses - synthesize them
            final_response = await self._synthesize_multiple_responses(
                state['user_message'], 
                agent_responses
            )
        
        # Add assistant message to state
        assistant_message = {
            "role": "assistant",
            "content": final_response,
            "timestamp": time.time(),
            "agent_responses": [
                {
                    "agent_name": resp.agent_name,
                    "response": resp.response,
                    "processing_time": resp.processing_time,
                    "sources": resp.sources,
                    "handled": resp.handled
                }
                for resp in agent_responses
            ]
        }
        
        return {
            **state,
            "messages": [assistant_message]
        }
    
    async def _call_agent_with_retry(self, agent_func, query: str, max_retries: int = 1) -> AgentResponse:
        """Call agent function with retry logic"""
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                self.logger.info(f"Calling agent (attempt {attempt + 1}/{max_retries + 1})")
                
                # Call the agent function
                result = await agent_func(query)
                
                # Convert to AgentResponse
                return AgentResponse(
                    agent_name=result.get("agent_name", "Unknown Agent"),
                    response=result.get("response", ""),
                    handled=result.get("handled", False),
                    processing_time=result.get("processing_time", 0.0),
                    sources=result.get("sources", [])
                )
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"Agent call failed (attempt {attempt + 1}): {str(e)}")
                
                if attempt < max_retries:
                    # Wait before retry (exponential backoff)
                    await asyncio.sleep(2 ** attempt)
                else:
                    self.logger.error(f"All retry attempts failed for agent call")
        
        # All retries failed
        return AgentResponse(
            agent_name="Error Handler",
            response=f"Sorry, I encountered an error while processing your request: {str(last_error)}",
            handled=False,
            processing_time=0.0,
            sources=[],
            error=str(last_error)
        )
    
    async def _synthesize_multiple_responses(self, user_message: str, agent_responses: List[AgentResponse]) -> str:
        """Synthesize a coherent response from multiple agent responses"""
        
        context = f"User asked: {user_message}\n\n"
        context += "Here are responses from different agents:\n\n"
        
        for i, response in enumerate(agent_responses, 1):
            context += f"{i}. {response.agent_name}:\n"
            context += f"   {response.response}\n"
            if response.sources:
                context += f"   Sources: {', '.join(response.sources)}\n"
            context += "\n"
        
        # Highlight Product Agent's response if present
        product_response = next((r for r in agent_responses if r.agent_name == 'Product Agent'), None)
        prompt = f"""You are an expert AI assistant. Based on the following agent responses, provide a coherent, comprehensive answer to the user's question.

{context}

Instructions:
1. If the Product Agent provides a direct answer or product list, always prioritize and clearly present this information in your summary.
2. Use Knowledge Agent and Support Agent responses to add context or fill gaps, but do not contradict the Product Agent.
3. Address the user's original question directly.
4. Combine the most relevant information from each agent.
5. Avoid redundancy.
6. Provide a clear, actionable response.
7. Mention relevant sources when appropriate."""
        
        synthesis_result = await self.llm_service.generate_text(prompt, max_tokens=600)
        return synthesis_result.get("text", agent_responses[0].response)
    
    async def process_message(self, message: str, user_id: str = "anonymous", session_id: str = "default") -> Dict[str, Any]:
        """Process user message through the LangGraph workflow"""
        
        self.logger.info(f"Processing message: '{message}' | user_id={user_id} | session_id={session_id}")
        
        # Initialize session if not exists
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "messages": [],
                "context": {}
            }
        
        # Add user message to session
        self.sessions[session_id]["messages"].append({
            "role": "user",
            "content": message,
            "timestamp": time.time()
        })
        
        # Prepare initial state for LangGraph
        initial_state = AgentState(
            messages=[],
            user_message=message,
            user_id=user_id,
            session_id=session_id,
            intent=None,
            intent_confidence=None,
            entities=[],
            agent_responses=[],
            current_agent=None,
            error=None,
            retry_count=0,
            processing_start_time=time.time()
        )
        
        try:
            # Execute the LangGraph workflow
            config = {"configurable": {"thread_id": session_id}}
            final_state = await self.workflow.ainvoke(initial_state, config)
            
            # Extract results
            final_response = final_state.get("messages", [{}])[0].get("content", "No response generated")
            agent_responses = final_state.get("agent_responses", [])
            
            # Add assistant response to session
            self.sessions[session_id]["messages"].append({
                "role": "assistant",
                "content": final_response,
                "timestamp": time.time(),
                "agent_responses": [
                    {
                        "agent_name": resp.agent_name,
                        "response": resp.response,
                        "processing_time": resp.processing_time,
                        "sources": resp.sources,
                        "handled": resp.handled
                    }
                    for resp in agent_responses
                ]
            })
            
            return {
                "response": final_response,
                "agent_responses": [
                    {
                        "agent_name": resp.agent_name,
                        "response": resp.response,
                        "processing_time": resp.processing_time,
                        "sources": resp.sources
                    }
                    for resp in agent_responses
                ],
                "intent": final_state.get("intent", "general_question"),
                "session_id": session_id,
                "processing_time": time.time() - final_state.get("processing_start_time", time.time())
            }
            
        except Exception as e:
            self.logger.error(f"Error in LangGraph workflow: {str(e)}", exc_info=True)
            error_response = f"I encountered an error while processing your request: {str(e)}"
            
            return {
                "response": error_response,
                "agent_responses": [{
                    "agent_name": "Error Handler",
                    "response": error_response,
                    "processing_time": 0.0,
                    "sources": []
                }],
                "intent": "error",
                "session_id": session_id,
                "processing_time": time.time() - initial_state.get("processing_start_time", time.time())
            }
    
    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a session"""
        return self.sessions.get(session_id, {}).get("messages", [])
    
    def clear_session(self, session_id: str) -> bool:
        """Clear a conversation session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def get_active_sessions(self) -> List[str]:
        """Get list of active session IDs"""
        return list(self.sessions.keys())
    
    async def get_conversation_summary(self, session_id: str) -> str:
        """Get a summary of the conversation"""
        if session_id not in self.sessions:
            return "No conversation found for this session."
        
        messages = self.sessions[session_id]["messages"]
        if not messages:
            return "No messages in this conversation."
        
        # Build conversation context
        conversation = ""
        for msg in messages[-10:]:  # Last 10 messages
            role = msg["role"].title()
            content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            conversation += f"{role}: {content}\n"
        
        prompt = f"""Please provide a brief summary of this conversation:

{conversation}

Summary should include:
1. Main topics discussed
2. Key questions asked
3. Solutions or information provided
4. Any unresolved issues"""
        
        result = await self.llm_service.generate_text(prompt, max_tokens=200)
        return result.get("text", "Unable to generate conversation summary.") 