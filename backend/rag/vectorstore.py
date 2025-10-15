from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from loguru import logger
import uuid

from backend.config import settings


class VectorStore:
    def __init__(self):
        self.client: Optional[AsyncQdrantClient] = None
        self.collection_name = settings.qdrant_collection_name
        self.embedding_model = None
        self.embedding_dim = 384
    
    async def initialize(self):
        try:
            self.client = AsyncQdrantClient(
                url=settings.qdrant_url,
                api_key=settings.qdrant_api_key
            )
            
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()
            
            collections = await self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if self.collection_name not in collection_names:
                await self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.embedding_dim,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            else:
                logger.info(f"Qdrant collection exists: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")
        
        embedding = self.embedding_model.encode(text, convert_to_numpy=True)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not self.embedding_model:
            raise RuntimeError("Embedding model not initialized")
        
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
    
    async def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        if not self.client:
            raise RuntimeError("Vector store not initialized")
        
        texts = [doc['content'] for doc in documents]
        embeddings = self.embed_batch(texts)
        
        points = []
        doc_ids = []
        
        for doc, embedding in zip(documents, embeddings):
            doc_id = doc.get('id', str(uuid.uuid4()))
            doc_ids.append(doc_id)
            
            payload = {
                'content': doc['content'],
                'metadata': doc.get('metadata', {})
            }
            
            points.append(PointStruct(
                id=doc_id,
                vector=embedding,
                payload=payload
            ))
        
        await self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        
        logger.info(f"Added {len(points)} documents to vector store")
        return doc_ids
    
    async def search(self, query: str, limit: int = 5, 
                    filters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        if not self.client:
            raise RuntimeError("Vector store not initialized")
        
        query_vector = self.embed_text(query)
        
        search_filter = None
        if filters:
            conditions = []
            for key, value in filters.items():
                conditions.append(
                    FieldCondition(
                        key=f"metadata.{key}",
                        match=MatchValue(value=value)
                    )
                )
            if conditions:
                search_filter = Filter(must=conditions)
        
        results = await self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=search_filter
        )
        
        return [
            {
                'id': result.id,
                'score': result.score,
                'content': result.payload['content'],
                'metadata': result.payload.get('metadata', {})
            }
            for result in results
        ]
    
    async def delete_document(self, doc_id: str):
        if not self.client:
            raise RuntimeError("Vector store not initialized")
        
        await self.client.delete(
            collection_name=self.collection_name,
            points_selector=[doc_id]
        )
        logger.info(f"Deleted document: {doc_id}")


vector_store = VectorStore()

