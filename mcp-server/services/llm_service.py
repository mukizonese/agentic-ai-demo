import os
import asyncio
import aiohttp
import openai
from typing import Dict, Any, Optional, List
import json
import logging
from langchain.embeddings import HuggingFaceEmbeddings

class LLMService:
    """Service for routing LLM requests to different backends"""
    
    def __init__(self):
        self.use_ollama = os.getenv("USE_OLLAMA", "true").lower() == "true"
        self.use_openai = os.getenv("USE_OPENAI", "false").lower() == "true"
        self.use_hf = os.getenv("USE_HF", "false").lower() == "true"
        
        # LLM configurations
        self.ollama_host = os.getenv("OLLAMA_HOST", "localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "gemma:2b")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.hf_model = os.getenv("HF_MODEL", "microsoft/DialoGPT-medium")
        
        # Initialize OpenAI client if needed
        if self.use_openai:
            openai.api_key = os.getenv("OPENAI_API_KEY")
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("LLMService")
        
        print(f"LLM Service initialized - Ollama: {self.use_ollama}, OpenAI: {self.use_openai}, HF: {self.use_hf}")
    
    async def generate_text(self, prompt: str, context: Optional[str] = None, max_tokens: int = 500) -> Dict[str, Any]:
        """Generate text using the configured LLM backend"""
        
        self.logger.info(f"Generating text with prompt: {prompt[:200]}... (truncated)")
        
        # Combine prompt with context if provided
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        try:
            if self.use_ollama:
                return await self._generate_ollama(full_prompt, max_tokens)
            elif self.use_openai:
                return await self._generate_openai(full_prompt, max_tokens)
            elif self.use_hf:
                return await self._generate_huggingface(full_prompt, max_tokens)
            else:
                # Fallback to mock response
                return await self._generate_mock(full_prompt, max_tokens)
        except Exception as e:
            self.logger.error(f"Error generating text: {str(e)}", exc_info=True)
            return await self._generate_mock(full_prompt, max_tokens)
    
    async def _generate_ollama(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Generate text using Ollama"""
        self.logger.info("Calling Ollama backend...")
        url = f"http://{self.ollama_host}/api/generate"
        
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": 0.7
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "text": result.get("response", "").strip(),
                        "backend": "ollama",
                        "model": self.ollama_model,
                        "success": True
                    }
                else:
                    raise Exception(f"Ollama API error: {response.status}")
    
    async def _generate_openai(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Generate text using OpenAI API"""
        self.logger.info("Calling OpenAI backend...")
        try:
            response = await openai.ChatCompletion.acreate(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7
            )
            
            return {
                "text": response.choices[0].message.content.strip(),
                "backend": "openai",
                "model": self.openai_model,
                "success": True
            }
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    async def _generate_huggingface(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Generate text using HuggingFace API"""
        self.logger.info("Calling HuggingFace backend...")
        hf_api_key = os.getenv("HF_API_KEY")
        if not hf_api_key:
            raise Exception("HuggingFace API key not provided")
        
        url = f"https://api-inference.huggingface.co/models/{self.hf_model}"
        headers = {"Authorization": f"Bearer {hf_api_key}"}
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_tokens,
                "temperature": 0.7,
                "return_full_text": False
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    result = await response.json()
                    text = result[0].get("generated_text", "").strip() if isinstance(result, list) else ""
                    return {
                        "text": text,
                        "backend": "huggingface",
                        "model": self.hf_model,
                        "success": True
                    }
                else:
                    raise Exception(f"HuggingFace API error: {response.status}")
    
    async def _generate_mock(self, prompt: str, max_tokens: int) -> Dict[str, Any]:
        """Generate mock response using langchain embeddings"""
        self.logger.info("Returning mock response with langchain embeddings...")
        # Use HuggingFaceEmbeddings from langchain
        try:
            embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
            embedding = embedder.embed_query(prompt)
            text = f"[EMBEDDING GENERATED] Vector length: {len(embedding)}. This is a mock response."
        except Exception as e:
            text = f"[EMBEDDING ERROR] {str(e)}. This is a mock response."
        return {
            "text": text,
            "backend": "mock-langchain-embedding",
            "model": "sentence-transformers/all-MiniLM-L6-v2",
            "success": True
        }
    
    async def summarize(self, text: str, max_length: int = 150) -> str:
        """Summarize text using the LLM"""
        self.logger.info(f"Summarizing text: {text[:200]}... (truncated)")
        prompt = f"Please provide a concise summary of the following text in no more than {max_length} characters:\n\n{text}"
        result = await self.generate_text(prompt, max_tokens=100)
        return result.get("text", text[:max_length])
    
    async def extract_intent(self, message: str) -> Dict[str, Any]:
        """Extract intent and entities from user message"""
        self.logger.info(f"Extracting intent from message: {message}")
        prompt = f"""Analyze the following user message and extract the intent and key entities.
        
User message: "{message}"

Please respond in JSON format with:
- intent: the main intent (support, product_info, general_question, etc.)
- entities: list of important entities mentioned
- confidence: confidence score from 0.0 to 1.0

Example response:
{{"intent": "support", "entities": ["password", "reset"], "confidence": 0.9}}"""
        
        result = await self.generate_text(prompt, max_tokens=200)
        
        try:
            # Try to parse JSON response
            response_text = result.get("text", "{}")
            if response_text.startswith("{") and response_text.endswith("}"):
                return json.loads(response_text)
        except:
            pass
        
        # Fallback to simple intent detection
        message_lower = message.lower()
        if any(word in message_lower for word in ["support", "help", "issue", "problem", "bug"]):
            return {"intent": "support", "entities": [], "confidence": 0.7}
        elif any(word in message_lower for word in ["product", "price", "feature", "specification"]):
            return {"intent": "product_info", "entities": [], "confidence": 0.7}
        else:
            return {"intent": "general_question", "entities": [], "confidence": 0.5} 