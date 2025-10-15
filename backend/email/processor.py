from typing import Dict, Any, List, Optional
from loguru import logger
import re
import json

from backend.llm.router import llm_router, ModelTier
from backend.rag.retrieval import hybrid_retrieval
from backend.graph.queries import inventory_queries
from backend.config import settings


class EmailIntent:
    PARTS_ORDER = "parts_order"
    SERVICE_INQUIRY = "service_inquiry"
    INVOICE_REQUEST = "invoice_request"
    INVENTORY_CHECK = "inventory_check"
    GENERAL_INQUIRY = "general_inquiry"
    COMPLAINT = "complaint"
    TRANSFER_REQUEST = "transfer_request"


class EmailProcessor:
    
    @staticmethod
    async def classify_intent(subject: str, body: str) -> Dict[str, Any]:
        prompt = f"""
Classify the intent of this customer email. Choose the most appropriate category.

Subject: {subject}
Body: {body[:500]}

Categories:
- parts_order: Customer wants to order parts
- service_inquiry: Question about service or installation
- invoice_request: Requesting invoice or payment information
- inventory_check: Checking if parts are in stock
- general_inquiry: General questions
- complaint: Issue or complaint
- transfer_request: Requesting part transfer between locations

Respond in JSON format:
{{
    "intent": "category_name",
    "confidence": 0.0-1.0,
    "key_entities": ["extracted", "entities"],
    "urgency": "low/medium/high"
}}
"""
        
        try:
            result = await llm_router.generate(prompt, tier=ModelTier.FAST, max_tokens=300)
            response_text = result['response'].strip()
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                classification = json.loads(json_match.group())
            else:
                classification = {
                    "intent": EmailIntent.GENERAL_INQUIRY,
                    "confidence": 0.5,
                    "key_entities": [],
                    "urgency": "medium"
                }
            
            logger.info(f"Email classified as: {classification['intent']} (confidence: {classification['confidence']})")
            return classification
        
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")
            return {
                "intent": EmailIntent.GENERAL_INQUIRY,
                "confidence": 0.3,
                "key_entities": [],
                "urgency": "medium"
            }
    
    @staticmethod
    async def extract_entities(body: str) -> Dict[str, Any]:
        prompt = f"""
Extract key information from this email:

{body}

Extract:
- part_skus: List of part numbers/SKUs mentioned
- location: Any location/branch mentioned
- customer_name: Customer name if mentioned
- contact_info: Phone or email if mentioned
- quantities: Quantities requested

Respond in JSON format:
{{
    "part_skus": [],
    "location": null,
    "customer_name": null,
    "contact_info": null,
    "quantities": {{}}
}}
"""
        
        try:
            result = await llm_router.generate(prompt, tier=ModelTier.FAST, max_tokens=300)
            response_text = result['response'].strip()
            
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                entities = json.loads(json_match.group())
            else:
                entities = {}
            
            return entities
        
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {}
    
    @staticmethod
    async def route_to_department(intent: str, entities: Dict) -> str:
        department_routing = {
            EmailIntent.PARTS_ORDER: "sales",
            EmailIntent.SERVICE_INQUIRY: "service",
            EmailIntent.INVOICE_REQUEST: "accounting",
            EmailIntent.INVENTORY_CHECK: "sales",
            EmailIntent.COMPLAINT: "customer_service",
            EmailIntent.TRANSFER_REQUEST: "warehouse",
            EmailIntent.GENERAL_INQUIRY: "customer_service"
        }
        
        return department_routing.get(intent, "customer_service")
    
    @staticmethod
    async def generate_response(email_data: Dict[str, str], 
                               classification: Dict[str, Any],
                               entities: Dict[str, Any]) -> Dict[str, Any]:
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        from_addr = email_data.get('from', '')
        
        intent = classification['intent']
        confidence = classification['confidence']
        
        if confidence < settings.confidence_threshold:
            return {
                "requires_human": True,
                "reason": "Low confidence classification",
                "suggested_department": await EmailProcessor.route_to_department(intent, entities),
                "draft_response": None
            }
        
        context = ""
        inventory_info = []
        
        if intent in [EmailIntent.PARTS_ORDER, EmailIntent.INVENTORY_CHECK]:
            part_skus = entities.get('part_skus', [])
            
            if part_skus:
                for sku in part_skus[:5]:
                    inv = await inventory_queries.check_inventory(sku)
                    if inv:
                        inventory_info.extend(inv)
                
                rag_context = await hybrid_retrieval.build_rag_context(
                    f"parts {' '.join(part_skus)}",
                    context_type="parts"
                )
                context = rag_context
        
        elif intent == EmailIntent.SERVICE_INQUIRY:
            rag_context = await hybrid_retrieval.build_rag_context(
                body[:200],
                context_type="faq"
            )
            context = rag_context
        
        system_prompt = """You are a helpful customer service representative for an auto parts dealer.
Be professional, friendly, and provide accurate information based on the context provided.
If you cannot fully answer, politely suggest contacting the appropriate department."""
        
        user_prompt = f"""
Customer Email:
From: {from_addr}
Subject: {subject}
Body: {body}

Intent: {intent}
Extracted Information: {json.dumps(entities, indent=2)}

"""
        
        if inventory_info:
            inv_text = "\n".join([
                f"- {item['part_name']} (SKU: {item['sku']}) at {item['location']}: {item['quantity']} in stock (${item['price']})"
                for item in inventory_info
            ])
            user_prompt += f"\nInventory Information:\n{inv_text}\n"
        
        if context:
            user_prompt += f"\nRelevant Information:\n{context}\n"
        
        user_prompt += "\nGenerate a professional email response to the customer."
        
        try:
            result = await llm_router.generate(
                user_prompt,
                system=system_prompt,
                tier=ModelTier.QUALITY if intent == EmailIntent.COMPLAINT else ModelTier.BALANCED
            )
            
            response_text = result['response']
            
            return {
                "requires_human": False,
                "response": response_text,
                "department": await EmailProcessor.route_to_department(intent, entities),
                "inventory_data": inventory_info,
                "confidence": confidence,
                "model_used": result['model_used']
            }
        
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            return {
                "requires_human": True,
                "reason": f"Generation error: {str(e)}",
                "suggested_department": await EmailProcessor.route_to_department(intent, entities),
                "draft_response": None
            }
    
    @staticmethod
    async def process_email(email_data: Dict[str, str]) -> Dict[str, Any]:
        subject = email_data.get('subject', '')
        body = email_data.get('body', '')
        
        logger.info(f"Processing email: {subject[:50]}")
        
        classification = await EmailProcessor.classify_intent(subject, body)
        
        entities = await EmailProcessor.extract_entities(body)
        
        response_data = await EmailProcessor.generate_response(
            email_data,
            classification,
            entities
        )
        
        return {
            "email_id": email_data.get('id'),
            "classification": classification,
            "entities": entities,
            "response_data": response_data,
            "processed_at": str(logger._core.log_time)
        }


email_processor = EmailProcessor()

