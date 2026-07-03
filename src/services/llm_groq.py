"""
Groq LLM Service - Handles AI response generation.

WHY THIS FILE EXISTS:
- Wraps the Groq API client
- Manages conversation context
- Provides both streaming and non-streaming responses
- Keeps LLM logic separate from WebSocket handling

USED BY:
    websocket_handler.py calls generate_response() or stream_response()
"""

import logging
from typing import Optional, List, Dict, AsyncGenerator
from groq import Groq
from src.config import settings

logger = logging.getLogger(__name__)


class GroqLLMService:
    """Service for interacting with Groq's LLM API."""

    def __init__(self):
        """Initialize the Groq client."""
        try:
            self.client = Groq(api_key=settings.groq_api_key)
            self.model = settings.groq_model
            logger.info(f"Groq LLM ready: {self.model} (streaming enabled)")
        except Exception as e:
            logger.error(f"Failed to initialize Groq: {e}")
            self.client = None
            self.model = None

    def _build_messages(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> List[Dict[str, str]]:
        """
        Build the messages array for the API call.

        Args:
            user_message: The user's transcribed speech
            system_prompt: Optional system prompt override
            conversation_history: Optional prior messages

        Returns:
            List of message dicts ready for the API
        """
        messages = []

        # System prompt sets the AI's personality
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({
                "role": "system",
                "content": (
                    "You are Nana Ama, a friendly and helpful AI voice assistant. "
                    "Keep responses concise (2-3 sentences max) since this is a voice conversation. "
                    "Be natural and conversational. "
                    "If you don't understand something, ask for clarification."
                )
            })

        # Add conversation history for context
        if conversation_history:
            messages.extend(conversation_history)

        # Add the current user message
        messages.append({"role": "user", "content": user_message})

        return messages

    async def generate_response(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Optional[str]:
        """
        Generate AI response using non-streaming mode.

        Uses stream=False for simplicity. Real streaming
        will be implemented in the AWS production build (Step 2).

        Args:
            user_message: Transcribed user speech
            system_prompt: Optional system prompt override
            conversation_history: Optional prior messages

        Returns:
            AI response text, or None on error
        """
        if not self.client:
            logger.error("Groq client not initialized")
            return None

        try:
            messages = self._build_messages(
                user_message,
                system_prompt,
                conversation_history
            )

            logger.debug(f"Calling Groq: {user_message[:50]}...")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=1024,
                temperature=0.7,
                stream=False,
            )

            full_response = response.choices[0].message.content or ""
            full_response = full_response.strip()

            logger.info(f"Groq response: {full_response[:50]}...")

            return full_response

        except Exception as e:
            logger.error(f"Groq error: {e}")
            return None

    async def stream_response(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream AI response token by token.

        Yields individual tokens as they are generated.
        Used for real-time voice responses where TTFT matters.

        Args:
            user_message: Transcribed user speech
            system_prompt: Optional system prompt override
            conversation_history: Optional prior messages

        Yields:
            Individual tokens/words as strings
        """
        if not self.client:
            logger.error("Groq client not initialized")
            return

        try:
            messages = self._build_messages(
                user_message,
                system_prompt,
                conversation_history
            )

            logger.debug(f"Token streaming: {user_message[:50]}...")

            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_completion_tokens=1024,
                temperature=0.7,
                stream=True,
            )

            for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    yield delta.content

        except Exception as e:
            logger.error(f"Groq stream error: {e}")


# Create singleton instance
groq_llm = GroqLLMService()
