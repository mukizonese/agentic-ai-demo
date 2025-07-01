import asyncio
import time
from typing import Dict, Any, List, Optional
import logging

class AgentOrchestrator:
    """Orchestrates agent responses and manages conversation flow"""
    
    def __init__(self, support_agent, product_agent, llm_service):
        self.support_agent = support_agent
        self.product_agent = product_agent
        self.llm_service = llm_service
        
        # Session storage for conversation context
        self.sessions = {}
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("AgentOrchestrator")
        
    async def process_message(self, message: str, user_id: str = "anonymous", session_id: str = "default") -> Dict[str, Any]:
        """Process user message through appropriate agents"""
        
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
        
        # Extract intent to determine which agents to use
        intent_info = await self.llm_service.extract_intent(message)
        intent = intent_info.get("intent", "general_question")
        self.logger.info(f"Extracted intent: {intent_info}")
        
        # Process message through relevant agents
        agent_responses = []
        
        try:
            # Always try support agent for support-related queries
            support_keywords = ["support", "help", "issue", "problem", "bug", "password", "reset", "login", "account"]
            if intent == "support" or any(word in message.lower() for word in support_keywords):
                # route to Support Agent
                self.logger.info("Routing to Support Agent...")
                support_response = await self.support_agent.process_query(message)
                self.logger.info(f"Support Agent response: {support_response}")
                if support_response.get("handled"):
                    agent_responses.append({
                        "agent_name": support_response["agent_name"],
                        "response": support_response["response"],
                        "processing_time": support_response["processing_time"],
                        "sources": support_response.get("sources", [])
                    })
            
            # Try product agent for product-related queries
            product_keywords = ["product", "price", "buy", "feature"]
            if intent == "product_info" or any(word in message.lower() for word in product_keywords):
                self.logger.info("Routing to Product Agent...")
                product_response = await self.product_agent.process_query(message)
                self.logger.info(f"Product Agent response: {product_response}")
                if product_response.get("handled"):
                    agent_responses.append({
                        "agent_name": product_response["agent_name"],
                        "response": product_response["response"],
                        "processing_time": product_response["processing_time"],
                        "sources": product_response.get("sources", [])
                    })
            
            # If no agents handled the query, provide a general response
            if not agent_responses:
                self.logger.info("No agent handled the query, generating general response...")
                general_response = await self._generate_general_response(message)
                agent_responses.append({
                    "agent_name": "General Assistant",
                    "response": general_response["text"],
                    "processing_time": 0.1,
                    "sources": []
                })
            
            # Synthesize final response
            self.logger.info(f"Collected agent responses: {agent_responses}")
            final_response = await self._synthesize_response(message, agent_responses)
            self.logger.info(f"Final synthesized response: {final_response}")
            
            # Add assistant response to session
            self.sessions[session_id]["messages"].append({
                "role": "assistant",
                "content": final_response,
                "timestamp": time.time(),
                "agent_responses": agent_responses
            })
            
            return {
                "response": final_response,
                "agent_responses": agent_responses,
                "intent": intent,
                "session_id": session_id
            }
            
        except Exception as e:
            self.logger.error(f"Error in process_message: {str(e)}", exc_info=True)
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
                "session_id": session_id
            }
    
    async def _synthesize_response(self, user_message: str, agent_responses: List[Dict[str, Any]]) -> str:
        """Synthesize a coherent response from multiple agent responses"""
        
        self.logger.info("Synthesizing final response from agent responses...")
        
        if len(agent_responses) == 1:
            return agent_responses[0]["response"]
        
        # Multiple agent responses - synthesize them
        context = f"User asked: {user_message}\n\n"
        context += "Here are responses from different agents:\n\n"
        
        for i, response in enumerate(agent_responses, 1):
            context += f"{i}. {response['agent_name']}:\n"
            context += f"   {response['response']}\n"
            if response.get('sources'):
                context += f"   Sources: {', '.join(response['sources'])}\n"
            context += "\n"
        
        # Highlight Product Agent's response if present
        product_response = next((r for r in agent_responses if r['agent_name'] == 'Product Agent'), None)
        prompt = f"""You are an expert AI assistant. Based on the following agent responses, provide a coherent, comprehensive answer to the user's question.\n\n{context}\n\nInstructions:\n1. If the Product Agent provides a direct answer or product list, always prioritize and clearly present this information in your summary.\n2. Use Knowledge Agent and Support Agent responses to add context or fill gaps, but do not contradict the Product Agent.\n3. Address the user's original question directly.\n4. Combine the most relevant information from each agent.\n5. Avoid redundancy.\n6. Provide a clear, actionable response.\n7. Mention relevant sources when appropriate.\n"""
        self.logger.info(f"LLM synthesis prompt: {prompt}")
        synthesis_result = await self.llm_service.generate_text(prompt, max_tokens=600)
        self.logger.info(f"LLM synthesis result: {synthesis_result}")
        return synthesis_result.get("text", agent_responses[0]["response"])
    
    async def _generate_general_response(self, message: str) -> Dict[str, Any]:
        """Generate a general response when no specific agent handles the query"""
        prompt = f"""User message: {message}

This is a general inquiry that doesn't fall into specific support or product categories. Please provide a helpful, friendly response that:
1. Acknowledges the user's question
2. Provides any general guidance you can
3. Suggests how they might get more specific help
4. Maintains a professional, helpful tone"""
        
        return await self.llm_service.generate_text(prompt, max_tokens=300)
    
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