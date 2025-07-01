import os
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
import json
import numpy as np

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    import pinecone
    PINECONE_AVAILABLE = True
except ImportError:
    PINECONE_AVAILABLE = False

class VectorService:
    """Service for routing vector operations to different backends"""
    
    def __init__(self):
        self.use_pinecone = os.getenv("USE_PINECONE_API", "false").lower() == "true"
        self.use_local_vectordb = os.getenv("USE_LOCAL_VECTORDB", "true").lower() == "true"
        self.local_vectordb_type = os.getenv("LOCAL_VECTORDB_TYPE", "chroma")
        
        # Pinecone configuration
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone_env = os.getenv("PINECONE_ENV", "us-west1-gcp")
        self.pinecone_index = os.getenv("PINECONE_INDEX", "agentic-demo-index")
        
        # ChromaDB configuration
        self.chroma_host = os.getenv("CHROMA_HOST", "localhost")
        self.chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        
        # Initialize clients
        self.pinecone_client = None
        self.chroma_client = None
        self.chroma_collection = None
        
        print(f"Vector Service initialized - Pinecone: {self.use_pinecone}, Local: {self.use_local_vectordb}")
    
    async def initialize(self):
        """Initialize vector database connections"""
        try:
            if self.use_pinecone and PINECONE_AVAILABLE:
                await self._initialize_pinecone()
            elif self.use_local_vectordb and self.local_vectordb_type == "chroma":
                await self._initialize_chroma()
            
            print("Vector Service initialization completed")
        except Exception as e:
            print(f"Error initializing Vector Service: {e}")
    
    async def _initialize_pinecone(self):
        """Initialize Pinecone client"""
        if not self.pinecone_api_key:
            raise Exception("Pinecone API key not provided")
        
        pinecone.init(
            api_key=self.pinecone_api_key,
            environment=self.pinecone_env
        )
        
        # Check if index exists, create if not
        if self.pinecone_index not in pinecone.list_indexes():
            pinecone.create_index(
                name=self.pinecone_index,
                dimension=384,  # Assuming sentence-transformers embeddings
                metric="cosine"
            )
        
        self.pinecone_client = pinecone.Index(self.pinecone_index)
        print("Pinecone client initialized")
    
    async def _initialize_chroma(self):
        """Initialize ChromaDB client"""
        if not CHROMADB_AVAILABLE:
            raise Exception("ChromaDB not available")
        
        try:
            # Try to connect to ChromaDB server
            self.chroma_client = chromadb.HttpClient(
                host=self.chroma_host,
                port=self.chroma_port
            )
            
            # Create or get collection
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="agentic_demo_collection",
                metadata={"description": "Collection for agentic AI demo"}
            )
            
            print("ChromaDB client initialized")
        except Exception as e:
            print(f"Failed to connect to ChromaDB server, using in-memory client: {e}")
            # Fallback to in-memory ChromaDB
            self.chroma_client = chromadb.Client()
            self.chroma_collection = self.chroma_client.get_or_create_collection(
                name="agentic_demo_collection"
            )
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embeddings for text (mock implementation)"""
        # In a real implementation, you would use a proper embedding model
        # For now, we'll create a simple hash-based embedding
        import hashlib
        
        # Create a deterministic hash-based embedding
        hash_obj = hashlib.md5(text.encode())
        hash_int = int(hash_obj.hexdigest(), 16)
        
        # Convert to a 384-dimensional vector
        np.random.seed(hash_int % (2**32))
        embedding = np.random.normal(0, 1, 384).tolist()
        
        return embedding
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to vector database"""
        try:
            if self.use_pinecone and self.pinecone_client:
                return await self._add_documents_pinecone(documents)
            elif self.use_local_vectordb and self.chroma_collection:
                return await self._add_documents_chroma(documents)
            else:
                print("No vector database configured")
                return False
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False
    
    async def _add_documents_pinecone(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to Pinecone"""
        vectors = []
        
        for doc in documents:
            embedding = await self.embed_text(doc.get("content", ""))
            vectors.append({
                "id": doc.get("id", ""),
                "values": embedding,
                "metadata": {
                    "content": doc.get("content", ""),
                    "title": doc.get("title", ""),
                    "source": doc.get("source", "")
                }
            })
        
        self.pinecone_client.upsert(vectors)
        return True
    
    async def _add_documents_chroma(self, documents: List[Dict[str, Any]]) -> bool:
        """Add documents to ChromaDB"""
        ids = []
        embeddings = []
        metadatas = []
        documents_text = []
        
        for doc in documents:
            embedding = await self.embed_text(doc.get("content", ""))
            
            ids.append(doc.get("id", ""))
            embeddings.append(embedding)
            documents_text.append(doc.get("content", ""))
            metadatas.append({
                "title": doc.get("title", ""),
                "source": doc.get("source", "")
            })
        
        self.chroma_collection.add(
            embeddings=embeddings,
            documents=documents_text,
            metadatas=metadatas,
            ids=ids
        )
        return True
    
    async def search_similar(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for similar documents"""
        try:
            if self.use_pinecone and self.pinecone_client:
                return await self._search_pinecone(query, limit)
            elif self.use_local_vectordb and self.chroma_collection:
                return await self._search_chroma(query, limit)
            else:
                return []
        except Exception as e:
            print(f"Error searching documents: {e}")
            return []
    
    async def _search_pinecone(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search Pinecone for similar documents"""
        query_embedding = await self.embed_text(query)
        
        results = self.pinecone_client.query(
            vector=query_embedding,
            top_k=limit,
            include_metadata=True
        )
        
        documents = []
        for match in results.get("matches", []):
            documents.append({
                "id": match.get("id"),
                "content": match.get("metadata", {}).get("content", ""),
                "title": match.get("metadata", {}).get("title", ""),
                "source": match.get("metadata", {}).get("source", ""),
                "score": match.get("score", 0.0)
            })
        
        return documents
    
    async def _search_chroma(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Search ChromaDB for similar documents"""
        query_embedding = await self.embed_text(query)
        
        results = self.chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )
        
        documents = []
        if results and "ids" in results:
            for i in range(len(results["ids"][0])):
                documents.append({
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i] if "documents" in results else "",
                    "title": results["metadatas"][0][i].get("title", "") if "metadatas" in results else "",
                    "source": results["metadatas"][0][i].get("source", "") if "metadatas" in results else "",
                    "score": 1.0 - results["distances"][0][i] if "distances" in results else 0.0
                })
        
        return documents
    
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection"""
        try:
            if self.use_pinecone and self.pinecone_client:
                stats = self.pinecone_client.describe_index_stats()
                return {
                    "backend": "pinecone",
                    "total_vectors": stats.get("total_vector_count", 0),
                    "dimension": stats.get("dimension", 0)
                }
            elif self.use_local_vectordb and self.chroma_collection:
                count = self.chroma_collection.count()
                return {
                    "backend": "chromadb",
                    "total_vectors": count,
                    "dimension": 384
                }
            else:
                return {"backend": "none", "total_vectors": 0, "dimension": 0}
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {"backend": "error", "total_vectors": 0, "dimension": 0} 