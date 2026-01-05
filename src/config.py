"""
Configuration Management for Voice AI Platform.

WHY THIS FILE EXISTS:
- Loads settings from .env file
- Validates all values (catches errors early)
- Provides typed access (IDE autocomplete works!)
- Single source of truth for all configuration

HOW TO USE:
    from src.config import settings
    
    print(settings.groq_api_key)    # Your Groq key
    print(settings.app_env)          # "development"
"""

from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from .env file.
    
    Pydantic automatically:
    1. Reads .env file
    2. Maps GROQ_API_KEY → groq_api_key (case insensitive)
    3. Validates types (str, int, bool)
    4. Raises error if required value is missing
    """
    
    # Tell Pydantic where to find .env and how to read it
    model_config = SettingsConfigDict(
        env_file=".env",           # File to read
        env_file_encoding="utf-8", # Support special characters
        case_sensitive=False,      # GROQ_API_KEY = groq_api_key
        extra="ignore",            # Ignore unknown variables
    )
    
    # ─────────────────────────────────────────────────────────────
    # APPLICATION SETTINGS
    # ─────────────────────────────────────────────────────────────
    # Field() lets us add defaults and descriptions
    
    app_name: str = Field(
        default="voice-ai-platform",
        description="Name of the application"
    )
    
    app_env: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    
    debug: bool = Field(
        default=True,
        description="Enable debug logging"
    )
    
    # ─────────────────────────────────────────────────────────────
    # SERVER SETTINGS
    # ─────────────────────────────────────────────────────────────
    
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind server to"
    )
    
    port: int = Field(
        default=8000,
        description="Port to run server on"
    )
    
    # ─────────────────────────────────────────────────────────────
    # NGROK SETTINGS (Public URLs)
    # ─────────────────────────────────────────────────────────────
    
    ngrok_wss_url: str = Field(
        default="",
        description="WebSocket URL for Twilio Media Streams"
    )
    
    ngrok_public_url: str = Field(
        default="",
        description="Public HTTPS URL for webhooks"
    )
    
    # ─────────────────────────────────────────────────────────────
    # TWILIO SETTINGS (Phone Calls)
    # ─────────────────────────────────────────────────────────────
    
    twilio_account_sid: str = Field(
        default="",
        description="Twilio Account SID"
    )
    
    twilio_auth_token: str = Field(
        default="",
        description="Twilio Auth Token (keep secret!)"
    )
    
    twilio_phone_number: str = Field(
        default="",
        description="Your Twilio phone number"
    )
    
    # ─────────────────────────────────────────────────────────────
    # DEEPGRAM SETTINGS (Speech-to-Text)
    # ─────────────────────────────────────────────────────────────
    
    deepgram_api_key: str = Field(
        default="",
        description="Deepgram API key for STT"
    )
    
    # ─────────────────────────────────────────────────────────────
    # GROQ SETTINGS (Fast LLM)
    # ─────────────────────────────────────────────────────────────
    
    groq_api_key: str = Field(
        default="",
        description="Groq API key for ultra-fast LLM"
    )
    
    groq_model: str = Field(
        default="llama-3.1-8b-instant",
        description="Groq model to use"
    )
    
    # ─────────────────────────────────────────────────────────────
    # ELEVENLABS SETTINGS (Natural TTS)
    # ─────────────────────────────────────────────────────────────
    
    elevenlabs_api_key: str = Field(
        default="",
        description="ElevenLabs API key for natural voice"
    )
    
    elevenlabs_voice_id: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",
        description="Default voice ID (Rachel)"
    )
    
    # ─────────────────────────────────────────────────────────────
    # HELPER PROPERTIES
    # ─────────────────────────────────────────────────────────────
    # @property makes a method act like an attribute
    # settings.is_production instead of settings.is_production()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.app_env == "development"


# ─────────────────────────────────────────────────────────────────
# SINGLETON PATTERN
# ─────────────────────────────────────────────────────────────────
# @lru_cache ensures we only create ONE Settings instance
# Every import gets the SAME object (not a new copy)

@lru_cache()
def get_settings() -> Settings:
    """
    Get the cached settings instance.
    
    WHY CACHE?
    - Loading .env file = disk I/O (slow)
    - We only need to do it ONCE
    - All code shares the same settings object
    """
    return Settings()


# Create the instance for easy importing
settings = get_settings()
