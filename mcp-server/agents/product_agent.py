import asyncio
import aiohttp
import time
import os
from typing import Dict, Any, List, Optional
import logging

class ProductAppAgent:
    """Agent responsible for handling product-related queries"""
    
    def __init__(self, llm_service):
        self.llm_service = llm_service
        self.product_app_url = os.getenv("PRODUCT_APP_URL", "http://localhost:8002")
        self.agent_name = "Product Agent"
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("ProductAppAgent")
        
    async def process_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process product-related query"""
        self.logger.info(f"Processing product query: {query}")
        start_time = time.time()
        
        try:
            # Check if query is product-related
            if not await self._is_product_related(query):
                self.logger.info("Query not product-related.")
                return {
                    "handled": False,
                    "agent_name": self.agent_name,
                    "response": "",
                    "processing_time": time.time() - start_time,
                    "sources": []
                }
            
            # Search for relevant products
            products = await self._search_products(query)
            self.logger.info(f"Found products: {products}")
            
            # Generate response based on products
            response = await self._generate_product_response(query, products)
            self.logger.info(f"Product response: {response}")
            
            processing_time = time.time() - start_time
            
            return {
                "handled": True,
                "agent_name": self.agent_name,
                "response": response["text"],
                "processing_time": processing_time,
                "sources": [product.get("name", "") for product in products[:3]]
            }
            
        except Exception as e:
            self.logger.error(f"Error processing product query: {str(e)}", exc_info=True)
            return {
                "handled": False,
                "agent_name": self.agent_name,
                "response": f"Error processing product query: {str(e)}",
                "processing_time": time.time() - start_time,
                "sources": []
            }
    
    async def _is_product_related(self, query: str) -> bool:
        """Determine if query is product-related"""
        product_keywords = [
            "product", "price", "cost", "buy", "purchase", "specification", "spec",
            "feature", "available", "stock", "delivery", "shipping", "warranty",
            "review", "rating", "compare", "recommendation", "best", "model",
            "category", "brand", "smartwidget", "powerhub", "ecosmart", "aquapure", "fittracker"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in product_keywords)
    
    async def _search_products(self, query: str) -> List[Dict[str, Any]]:
        """Search for relevant products"""
        try:
            # First try to search using the query
            search_url = f"{self.product_app_url}/products/search/{query}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url) as response:
                    if response.status == 200:
                        products = await response.json()
                        if products:
                            return products[:5]  # Return top 5 results
            
            # If no search results, try to extract price range or category
            price_range = self._extract_price_range(query)
            if price_range:
                price_url = f"{self.product_app_url}/products/price-range/{price_range[0]}/{price_range[1]}"
                async with aiohttp.ClientSession() as session:
                    async with session.get(price_url) as response:
                        if response.status == 200:
                            products = await response.json()
                            if products:
                                return products[:5]
            
            # Get all products as fallback and rank by relevance
            all_products_url = f"{self.product_app_url}/products"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(all_products_url) as response:
                    if response.status == 200:
                        all_products = await response.json()
                        # Simple relevance scoring based on query terms
                        return self._rank_products_by_relevance(query, all_products)[:3]
            
            return []
            
        except Exception as e:
            print(f"Error searching products: {e}")
            return []
    
    def _extract_price_range(self, query: str) -> Optional[tuple]:
        """Extract price range from query"""
        import re
        
        # Look for patterns like "under $300", "below 200", "$100-$500", etc.
        patterns = [
            r'under\s*\$?(\d+)',
            r'below\s*\$?(\d+)',
            r'less\s+than\s*\$?(\d+)',
            r'\$?(\d+)\s*-\s*\$?(\d+)',
            r'between\s*\$?(\d+)\s*and\s*\$?(\d+)'
        ]
        
        query_lower = query.lower()
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                if len(match.groups()) == 1:
                    # Single price (under/below)
                    max_price = float(match.group(1))
                    return (0, max_price)
                elif len(match.groups()) == 2:
                    # Price range
                    min_price = float(match.group(1))
                    max_price = float(match.group(2))
                    return (min_price, max_price)
        
        return None
    
    def _rank_products_by_relevance(self, query: str, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank products by relevance to query"""
        query_terms = query.lower().split()
        scored_products = []
        
        for product in products:
            score = 0
            name = product.get("name", "").lower()
            description = product.get("description", "").lower()
            category = product.get("category", "").lower()
            features = [feature.lower() for feature in product.get("features", [])]
            
            # Score based on term matches
            for term in query_terms:
                if term in name:
                    score += 3  # Name matches are more important
                if term in description:
                    score += 1
                if term in category:
                    score += 2
                if any(term in feature for feature in features):
                    score += 2
            
            scored_products.append((score, product))
        
        # Sort by score (descending) and return products
        scored_products.sort(key=lambda x: x[0], reverse=True)
        return [product for score, product in scored_products if score > 0]
    
    async def _generate_product_response(self, query: str, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate response based on products"""
        if not products:
            # No products found, generate a general product response
            prompt = f"""User question: {query}
            
I don't have specific products matching this query, but I can provide general guidance about our product catalog. Please provide a helpful response directing the user to browse categories or refine their search."""
            
            return await self.llm_service.generate_text(prompt, max_tokens=300)
        
        # Build context from products
        context = "Here are relevant products from our catalog:\n\n"
        for i, product in enumerate(products[:3], 1):
            context += f"{i}. {product.get('name', 'Unnamed Product')}\n"
            context += f"   Price: ${product.get('price', 0):.2f}\n"
            context += f"   Category: {product.get('category', 'N/A')}\n"
            context += f"   Rating: {product.get('rating', 0)}/5 ({product.get('reviews_count', 0)} reviews)\n"
            context += f"   Description: {product.get('description', '')[:150]}...\n"
            
            features = product.get('features', [])
            if features:
                context += f"   Key Features: {', '.join(features[:3])}\n"
            
            context += f"   Availability: {product.get('availability', 'Unknown')}\n\n"
        
        prompt = f"""Based on the following product information, please provide a helpful and informative response to the user's question.

{context}

User question: {query}

Please provide a detailed response that:
1. Addresses the user's specific question
2. Highlights the most relevant products
3. Compares features, prices, or specifications if appropriate
4. Provides purchasing recommendations based on their needs
5. Mentions availability and any other important details"""
        
        return await self.llm_service.generate_text(prompt, max_tokens=500)
    
    async def get_all_products(self) -> List[Dict[str, Any]]:
        """Get all available products"""
        try:
            url = f"{self.product_app_url}/products"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
            return []
        except Exception as e:
            print(f"Error fetching products: {e}")
            return []
    
    async def get_product_categories(self) -> List[str]:
        """Get all product categories"""
        products = await self.get_all_products()
        categories = list(set(product.get("category", "") for product in products))
        return [cat for cat in categories if cat]
    
    async def get_products_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get products by category"""
        try:
            url = f"{self.product_app_url}/products/category/{category}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
            return []
        except Exception as e:
            print(f"Error fetching products by category: {e}")
            return [] 