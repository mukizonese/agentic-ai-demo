import asyncio
import aiohttp
import time
import os
from typing import Dict, Any, List, Optional
import logging

class SupportAppAgent:
    """Agent responsible for handling support-related queries"""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.support_app_url = os.getenv("SUPPORT_APP_URL", "http://localhost:8001")
        self.agent_name = "Support Agent"
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("SupportAppAgent")
        
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process support-related query"""
        self.logger.info(f"Processing support query: {query}")
        start_time = time.time()
        
        try:
            # Check if query is support-related
            if not await self._is_support_related(query):
                self.logger.info("Query not support-related.")
                return {
                    "handled": False,
                    "agent_name": self.agent_name,
                    "response": "",
                    "processing_time": time.time() - start_time,
                    "sources": []
                }
            
            # Search for relevant support articles
            support_articles = await self._search_support_articles(query)
            self.logger.info(f"Found support articles: {support_articles}")
            
            # Generate response based on support articles
            response = await self._generate_support_response(query, support_articles)
            self.logger.info(f"Support response: {response}")
            
            processing_time = time.time() - start_time
            
            return {
                "handled": True,
                "agent_name": self.agent_name,
                "response": response["text"],
                "processing_time": processing_time,
                "sources": [article.get("title", "") for article in support_articles[:3]]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing support query: {str(e)}", exc_info=True)
            return {
                "handled": False,
                "agent_name": self.agent_name,
                "response": f"Error processing support query: {str(e)}",
                "processing_time": time.time() - start_time,
                "sources": []
            }
    
    async def _is_support_related(self, query: str) -> bool:
        """Determine if query is support-related"""
        support_keywords = [
            "help", "support", "issue", "problem", "bug", "error", "trouble",
            "password", "login", "account", "reset", "fix", "broken",
            "not working", "can't", "unable", "difficulty", "assistance"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in support_keywords)
    
    async def _search_support_articles(self, query: str) -> List[Dict[str, Any]]:
        """Search for relevant support articles"""
        try:
            # First try to search using the query
            search_url = f"{self.support_app_url}/support_articles/search/{query}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        articles = await response.json()
                        if articles:
                            return articles[:5]  # Return top 5 results
            
            # If no search results, get all articles as fallback
            all_articles_url = f"{self.support_app_url}/support_articles"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(all_articles_url) as response:
                    if response.status == 200:
                        all_articles = await response.json()
                        # Simple relevance scoring based on query terms
                        return self._rank_articles_by_relevance(query, all_articles)[:3]
            
            return []
            
        except Exception as e:
            print(f"Error searching support articles: {e}")
            return []
    
    def _rank_articles_by_relevance(self, query: str, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank articles by relevance to query"""
        query_terms = query.lower().split()
        scored_articles = []
        
        for article in articles:
            score = 0
            title = article.get("title", "").lower()
            content = article.get("content", "").lower()
            tags = [tag.lower() for tag in article.get("tags", [])]
            
            # Score based on term matches
            for term in query_terms:
                if term in title:
                    score += 3  # Title matches are more important
                if term in content:
                    score += 1
                if any(term in tag for tag in tags):
                    score += 2
            
            scored_articles.append((score, article))
        
        # Sort by score (descending) and return articles
        scored_articles.sort(key=lambda x: x[0], reverse=True)
        return [article for score, article in scored_articles if score > 0]
    
    async def _generate_support_response(self, query: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response based on support articles"""
        if not articles:
            # No articles found, generate a general support response
            prompt = f"""User question: {query}
            
I don't have specific support articles for this question, but I can provide general guidance. Please provide a helpful response directing the user to appropriate resources or next steps."""
            
            return await self.llm_service.generate_text(prompt, max_tokens=300)
        
        # Build context from articles
        context = "Here are relevant support articles:\n\n"
        for i, article in enumerate(articles[:3], 1):
            context += f"{i}. {article.get('title', 'Untitled')}\n"
            context += f"   {article.get('content', '')[:200]}...\n\n"
        
        prompt = f"""Based on the following support articles, please provide a helpful and accurate response to the user's question.

{context}

User question: {query}

Please provide a clear, step-by-step response based on the support articles above. If the articles don't fully address the question, mention what additional help might be needed."""
        
        return await self.llm_service.generate_text(prompt, max_tokens=400)
    
    async def get_all_support_articles(self) -> List[Dict[str, Any]]:
        """Get all available support articles"""
        try:
            url = f"{self.support_app_url}/support_articles"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
            return []
        except Exception as e:
            print(f"Error fetching support articles: {e}")
            return []
    
    async def get_support_categories(self) -> List[str]:
        """Get all support article categories"""
        articles = await self.get_all_support_articles()
        categories = list(set(article.get("category", "") for article in articles))
        return [cat for cat in categories if cat]