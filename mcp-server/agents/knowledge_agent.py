import asyncio
import time
from typing import Dict, Any, List, Optional
import logging

class KnowledgeAgent:
    """Agent responsible for knowledge retrieval and RAG operations"""
    
    def __init__(self, llm_service, vector_service):
        self.llm_service = llm_service
        self.vector_service = vector_service
        self.agent_name = "Knowledge Agent"
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("KnowledgeAgent")
        
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process knowledge-related query using RAG"""
        self.logger.info(f"Processing knowledge query: {query}")
        start_time = time.time()
        
        try:
            # Search for relevant documents in vector database
            relevant_docs = await self.vector_service.search_similar(query, limit=5)
            self.logger.info(f"Found relevant docs: {relevant_docs}")
            
            # Generate response using retrieved documents as context
            response = await self._generate_rag_response(query, relevant_docs)
            
            processing_time = time.time() - start_time
            self.logger.info(f"Knowledge response: {response}")
            
            return {
                "handled": True,
                "agent_name": self.agent_name,
                "response": response["text"],
                "processing_time": processing_time,
                "sources": [doc.get("title", f"Document {doc.get('id', '')}") for doc in relevant_docs[:3]]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing knowledge query: {str(e)}", exc_info=True)
            return {
                "handled": False,
                "agent_name": self.agent_name,
                "response": f"Error processing knowledge query: {str(e)}",
                "processing_time": time.time() - start_time,
                "sources": []
            }
    
    async def _generate_rag_response(self, query: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response using retrieved documents as context"""
        if not documents:
            # No relevant documents found
            prompt = f"""User question: {query}
            
I don't have specific information in my knowledge base to answer this question accurately. Please provide a helpful response indicating that more specific information might be needed, or suggest alternative ways to help the user."""
            
            return await self.llm_service.generate_text(prompt, max_tokens=300)
        
        # Build context from retrieved documents
        context = "Based on the following information from my knowledge base:\n\n"
        for i, doc in enumerate(documents[:3], 1):
            context += f"{i}. {doc.get('title', 'Untitled Document')}\n"
            context += f"   Source: {doc.get('source', 'Unknown')}\n"
            context += f"   Content: {doc.get('content', '')[:300]}...\n"
            context += f"   Relevance Score: {doc.get('score', 0):.2f}\n\n"
        
        prompt = f"""Using the knowledge base information provided below, please answer the user's question accurately and comprehensively.

{context}

User question: {query}

Please provide a detailed response that:
1. Answers the user's question based on the retrieved information
2. Cites specific sources when possible
3. Indicates if the information is incomplete or if additional details are needed
4. Provides actionable advice or next steps where appropriate"""
        
        return await self.llm_service.generate_text(prompt, max_tokens=500)
    
    async def initialize_vector_data(self):
        """Initialize vector database with sample data from support and product APIs"""
        try:
            print("Initializing vector database with sample data...")
            
            # Import agents to get data
            from .support_agent import SupportAppAgent
            from .product_agent import ProductAppAgent
            
            # Create temporary agent instances to fetch data
            support_agent = SupportAppAgent(self.llm_service)
            product_agent = ProductAppAgent(self.llm_service)
            
            # Fetch support articles
            support_articles = await support_agent.get_all_support_articles()
            support_docs = []
            for article in support_articles:
                support_docs.append({
                    "id": f"support_{article.get('id')}",
                    "title": article.get("title", ""),
                    "content": f"{article.get('title', '')} - {article.get('content', '')}",
                    "source": "Support Articles"
                })
            
            # Fetch products
            products = await product_agent.get_all_products()
            product_docs = []
            for product in products:
                # Create content combining all product information
                features_text = ", ".join(product.get("features", []))
                specs_text = ", ".join([f"{k}: {v}" for k, v in product.get("specifications", {}).items()])
                
                content = f"{product.get('name', '')} - {product.get('description', '')}. "
                content += f"Category: {product.get('category', '')}. "
                content += f"Price: ${product.get('price', 0)}. "
                content += f"Features: {features_text}. "
                content += f"Specifications: {specs_text}. "
                content += f"Rating: {product.get('rating', 0)}/5 ({product.get('reviews_count', 0)} reviews). "
                content += f"Availability: {product.get('availability', '')}"
                
                product_docs.append({
                    "id": f"product_{product.get('id')}",
                    "title": product.get("name", ""),
                    "content": content,
                    "source": "Product Catalog"
                })
            
            # Add all documents to vector database
            all_docs = support_docs + product_docs
            if all_docs:
                success = await self.vector_service.add_documents(all_docs)
                if success:
                    print(f"Successfully added {len(all_docs)} documents to vector database")
                else:
                    print("Failed to add documents to vector database")
            else:
                print("No documents to add to vector database")
                
        except Exception as e:
            print(f"Error initializing vector data: {e}")
    
    async def add_knowledge_document(self, title: str, content: str, source: str = "Manual") -> bool:
        """Add a single document to the knowledge base"""
        try:
            doc = {
                "id": f"manual_{int(time.time())}",
                "title": title,
                "content": content,
                "source": source
            }
            
            return await self.vector_service.add_documents([doc])
        except Exception as e:
            print(f"Error adding knowledge document: {e}")
            return False
    
    async def search_knowledge_base(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the knowledge base and return raw results"""
        try:
            return await self.vector_service.search_similar(query, limit)
        except Exception as e:
            print(f"Error searching knowledge base: {e}")
            return []
    
    async def get_knowledge_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base"""
        try:
            return await self.vector_service.get_collection_stats()
        except Exception as e:
            print(f"Error getting knowledge stats: {e}")
            return {"error": str(e)} 