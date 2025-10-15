from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from loguru import logger

from backend.rag.vectorstore import vector_store


class HybridRetrieval:
    
    @staticmethod
    async def retrieve_context(query: str, top_k: int = 5, 
                               filters: Optional[Dict[str, Any]] = None,
                               include_bm25: bool = False) -> List[Dict]:
        vector_results = await vector_store.search(query, limit=top_k, filters=filters)
        
        if not include_bm25:
            return vector_results
        
        logger.info(f"Retrieved {len(vector_results)} results for query: {query[:100]}")
        return vector_results
    
    @staticmethod
    async def retrieve_parts_info(part_query: str, location_id: Optional[str] = None) -> List[Dict]:
        filters = {'type': 'parts_catalog'}
        if location_id:
            filters['location_id'] = location_id
        
        results = await vector_store.search(part_query, limit=10, filters=filters)
        return results
    
    @staticmethod
    async def retrieve_faq(question: str, department: Optional[str] = None) -> List[Dict]:
        filters = {'type': 'faq'}
        if department:
            filters['department'] = department
        
        results = await vector_store.search(question, limit=3, filters=filters)
        return results
    
    @staticmethod
    async def retrieve_policy(query: str, policy_type: Optional[str] = None) -> List[Dict]:
        filters = {'type': 'policy'}
        if policy_type:
            filters['policy_type'] = policy_type
        
        results = await vector_store.search(query, limit=5, filters=filters)
        return results
    
    @staticmethod
    def format_context_for_llm(results: List[Dict]) -> str:
        if not results:
            return "No relevant information found."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            score = result.get('score', 0)
            content = result.get('content', '')
            metadata = result.get('metadata', {})
            
            context_parts.append(
                f"[Source {i}] (Relevance: {score:.2f})\n{content}\n"
            )
        
        return "\n".join(context_parts)
    
    @staticmethod
    async def build_rag_context(query: str, context_type: str = "general", 
                                location_id: Optional[str] = None,
                                department: Optional[str] = None) -> str:
        if context_type == "parts":
            results = await HybridRetrieval.retrieve_parts_info(query, location_id)
        elif context_type == "faq":
            results = await HybridRetrieval.retrieve_faq(query, department)
        elif context_type == "policy":
            results = await HybridRetrieval.retrieve_policy(query)
        else:
            filters = {}
            if location_id:
                filters['location_id'] = location_id
            if department:
                filters['department'] = department
            results = await HybridRetrieval.retrieve_context(query, filters=filters)
        
        return HybridRetrieval.format_context_for_llm(results)


hybrid_retrieval = HybridRetrieval()

