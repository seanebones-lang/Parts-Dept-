from typing import Optional, Dict, Any, List
from enum import Enum
from loguru import logger
import httpx
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import settings


class ModelTier(str, Enum):
    FAST = "fast"
    BALANCED = "balanced"
    QUALITY = "quality"


class LLMRouter:
    def __init__(self):
        self.anthropic_client = None
        if settings.anthropic_api_key:
            self.anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    
    def classify_query_complexity(self, query: str, context_length: int = 0) -> ModelTier:
        query_length = len(query.split())
        
        if query_length < 20 and context_length < 500:
            return ModelTier.FAST
        
        complex_keywords = [
            'analyze', 'compare', 'explain', 'evaluate', 'complex',
            'detailed', 'comprehensive', 'multiple', 'various'
        ]
        
        if any(keyword in query.lower() for keyword in complex_keywords):
            return ModelTier.QUALITY
        
        if context_length > 2000 or query_length > 50:
            return ModelTier.BALANCED
        
        return ModelTier.FAST
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def call_llama(self, prompt: str, system: Optional[str] = None, 
                        max_tokens: int = 1000) -> str:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                payload = {
                    "model": settings.llama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": 0.7
                    }
                }
                
                if system:
                    payload["system"] = system
                
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        
        except Exception as e:
            logger.error(f"Llama API error: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def call_claude(self, prompt: str, system: Optional[str] = None,
                         max_tokens: int = 2000) -> str:
        if not self.anthropic_client:
            raise RuntimeError("Anthropic API key not configured")
        
        try:
            messages = [{"role": "user", "content": prompt}]
            
            kwargs = {
                "model": settings.claude_model,
                "max_tokens": max_tokens,
                "messages": messages
            }
            
            if system:
                kwargs["system"] = system
            
            response = await self.anthropic_client.messages.create(**kwargs)
            return response.content[0].text
        
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def call_mistral(self, prompt: str, system: Optional[str] = None,
                          max_tokens: int = 1500) -> str:
        if not settings.mistral_api_key:
            raise RuntimeError("Mistral API key not configured")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                headers = {
                    "Authorization": f"Bearer {settings.mistral_api_key}",
                    "Content-Type": "application/json"
                }
                
                messages = []
                if system:
                    messages.append({"role": "system", "content": system})
                messages.append({"role": "user", "content": prompt})
                
                payload = {
                    "model": settings.mistral_model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7
                }
                
                response = await client.post(
                    "https://api.mistral.ai/v1/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
        
        except Exception as e:
            logger.error(f"Mistral API error: {e}")
            raise
    
    async def generate(self, prompt: str, system: Optional[str] = None,
                      tier: Optional[ModelTier] = None, max_tokens: int = 1500) -> Dict[str, Any]:
        if tier is None:
            tier = self.classify_query_complexity(prompt)
        
        logger.info(f"Using {tier.value} tier model for query")
        
        try:
            if tier == ModelTier.FAST:
                response = await self.call_llama(prompt, system, max_tokens)
                model_used = "llama3"
            elif tier == ModelTier.QUALITY:
                response = await self.call_claude(prompt, system, max_tokens)
                model_used = "claude"
            else:
                try:
                    response = await self.call_mistral(prompt, system, max_tokens)
                    model_used = "mistral"
                except:
                    logger.warning("Mistral failed, falling back to Llama")
                    response = await self.call_llama(prompt, system, max_tokens)
                    model_used = "llama3"
            
            return {
                "response": response,
                "model_used": model_used,
                "tier": tier.value
            }
        
        except Exception as e:
            logger.error(f"All LLM attempts failed: {e}")
            
            try:
                logger.info("Attempting fallback to Llama")
                response = await self.call_llama(prompt, system, max_tokens)
                return {
                    "response": response,
                    "model_used": "llama3_fallback",
                    "tier": "fallback"
                }
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                raise


llm_router = LLMRouter()

