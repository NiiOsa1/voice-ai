"""
Ultra-fast LLM Service using Groq.

WHY THIS FILE EXISTS:
- Provides the AI "brain" that generates responses
- Uses Groq for ultra-low latency (50-200ms TTFT)
- Supports streaming for even faster perceived response
- Maintains conversation context

WHY GROQ:
- 10x faster than OpenAI/Anthropic
- Custom LPU hardware designed for LLMs
- Critical for real-time voice conversations
- Streaming reduces Time-To-First-Token (TTFT)

OPTIMIZATION APPLIED:
- stream=True: Start processing immediately
- Groq TTFT: ~50-100ms (vs ~300ms for full response)
"""

import logging
from typing import Optional, List, Dict, AsyncGenerator

from groq import Groq

from src.config import settings

logger = logging.getLogger(__name__)


class GroqLLMService:
    """
    Ultra-fast LLM for real-time voice AI.
    
    USAGE:
        from src.services.llm_groq import groq_llm
        
        # Standard (still fast, simpler):
        response = await groq_llm.generate_response(...)
        
        # Streaming (fastest, for advanced pipelines):
        async for token in groq_llm.stream_response(...):
            # Process tokens as they arrive
            pass
    """

    def __init__(self):
        """Initialize the Groq client."""
        self.api_key = settings.groq_api_key
        self.model = settings.groq_model  # Default: llama-3.1-8b-instant

        if self.api_key:
            self.client = Groq(api_key=self.api_key)
            logger.info(f"✅ Groq LLM ready: {self.model} (streaming enabled)")
        else:
            self.client = None
            logger.warning("⚠️ Groq API key not found - LLM disabled")

    def _build_messages(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        Build the messages array for the API call.
        
        Extracted to avoid duplication between streaming/non-streaming methods.
        """
        messages = []

        # 1. System prompt (instructions) - always first
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })

        # 2. Conversation history - keep last 4 for speed
        if conversation_history:
            messages.extend(conversation_history[-12:])  # Last 12 messages = 6 exchanges

        # 3. Current user message - always last
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages

    async def generate_response(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[str]:
        """
        Generate AI response (non-streaming for GPT-OSS-20B compatibility test).
        """
        if not self.client:
            logger.error("❌ Groq client not initialized")
            return None

        try:
            messages = self._build_messages(
                user_message, 
                system_prompt, 
                conversation_history
            )

            logger.debug(f"🧠 Calling Groq: {user_message[:50]}...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=1024,
                temperature=0.7,
                stream=False,
                include_reasoning=False,
            )

            full_response = response.choices[0].message.content or ""
            full_response = full_response.strip()
            
            logger.info(f"🤖 Groq response: {full_response[:50]}...")
            
            return full_response

        except Exception as e:
            logger.error(f"❌ Groq error: {e}")
            return None

    async def stream_response(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream AI response token by token.
        """
        if not self.client:
            logger.error("❌ Groq client not initialized")
            return

        try:
            messages = self._build_messages(
                user_message, 
                system_prompt, 
                conversation_history
            )

            logger.debug(f"🧠 Token streaming: {user_message[:50]}...")

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=1024,
                temperature=0.7,
                stream=True,
                include_reasoning=False,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

        except Exception as e:
            logger.error(f"❌ Groq stream error: {e}")

# ─────────────────────────────────────────────────────────────────
# SINGLETON INSTANCE
# ─────────────────────────────────────────────────────────────────
groq_llm = GroqLLMService()
