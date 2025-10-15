from typing import List, Dict, Any
from loguru import logger
import re

from backend.rag.vectorstore import vector_store


class DocumentIngestion:
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    @staticmethod
    def semantic_chunk(text: str, max_chunk_size: int = 600) -> List[str]:
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(current_chunk) + len(para) < max_chunk_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    @staticmethod
    async def ingest_parts_catalog(catalog_data: List[Dict[str, Any]], location_id: str = None) -> int:
        documents = []
        
        for part in catalog_data:
            content = f"""
Part: {part.get('name', 'Unknown')}
SKU: {part.get('sku', 'N/A')}
Description: {part.get('description', 'No description available')}
Category: {part.get('category', 'General')}
Manufacturer: {part.get('manufacturer', 'Unknown')}
Price: ${part.get('price', 0):.2f}
            """.strip()
            
            metadata = {
                'type': 'parts_catalog',
                'sku': part.get('sku'),
                'category': part.get('category'),
                'price': part.get('price')
            }
            
            if location_id:
                metadata['location_id'] = location_id
            
            documents.append({
                'content': content,
                'metadata': metadata
            })
        
        doc_ids = await vector_store.add_documents(documents)
        logger.info(f"Ingested {len(doc_ids)} parts into vector store")
        return len(doc_ids)
    
    @staticmethod
    async def ingest_faq(faq_data: List[Dict[str, str]], department: str = None) -> int:
        documents = []
        
        for faq in faq_data:
            content = f"""
Question: {faq.get('question', '')}
Answer: {faq.get('answer', '')}
            """.strip()
            
            metadata = {
                'type': 'faq',
                'category': faq.get('category', 'general')
            }
            
            if department:
                metadata['department'] = department
            
            documents.append({
                'content': content,
                'metadata': metadata
            })
        
        doc_ids = await vector_store.add_documents(documents)
        logger.info(f"Ingested {len(doc_ids)} FAQ entries into vector store")
        return len(doc_ids)
    
    @staticmethod
    async def ingest_policy_document(text: str, policy_type: str, department: str = None) -> int:
        chunks = DocumentIngestion.semantic_chunk(text)
        documents = []
        
        for i, chunk in enumerate(chunks):
            metadata = {
                'type': 'policy',
                'policy_type': policy_type,
                'chunk_index': i,
                'total_chunks': len(chunks)
            }
            
            if department:
                metadata['department'] = department
            
            documents.append({
                'content': chunk,
                'metadata': metadata
            })
        
        doc_ids = await vector_store.add_documents(documents)
        logger.info(f"Ingested policy document '{policy_type}' as {len(doc_ids)} chunks")
        return len(doc_ids)
    
    @staticmethod
    async def ingest_service_manual(text: str, part_sku: str = None) -> int:
        chunks = DocumentIngestion.semantic_chunk(text)
        documents = []
        
        for i, chunk in enumerate(chunks):
            metadata = {
                'type': 'service_manual',
                'chunk_index': i,
                'total_chunks': len(chunks)
            }
            
            if part_sku:
                metadata['part_sku'] = part_sku
            
            documents.append({
                'content': chunk,
                'metadata': metadata
            })
        
        doc_ids = await vector_store.add_documents(documents)
        logger.info(f"Ingested service manual as {len(doc_ids)} chunks")
        return len(doc_ids)


document_ingestion = DocumentIngestion()

