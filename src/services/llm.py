"""
LLM Service - Maximum speed.
"""

import logging
from typing import Optional
from openai import OpenAI

from src.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key, timeout=5.0, max_retries=0)
            logger.info(f"OpenAI: {self.model}")
        else:
            self.client = None
    
    async def generate_response(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[list] = None
    ) -> Optional[str]:
        if not self.client:
            return None
        
        try:
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Only last 2 exchanges for speed
            if conversation_history:
                messages.extend(conversation_history[-2:])
            
            messages.append({"role": "user", "content": user_message})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=30,  # Very short responses
                temperature=0.9,
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error: {e}")
            return None


llm_service = LLMService()
