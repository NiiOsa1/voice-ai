"""
Configuration Management for Voice AI Platform.

This module loads all settings from environment variables and .env file.
Using Pydantic Settings ensures validation and type safety.

WHAT IS THIS FILE?
------------------
A central place to manage ALL settings for the entire application.
Instead of scattering API keys and settings across multiple files,
we define them all here once.

WHY DO WE NEED IT?
------------------
1. Security: Secrets stay in .env file, not in code
2. Organization: All settings in one place
3. Validation: Pydantic checks values are correct
4. Type Safety: IDE knows what type each setting is
"""

# =============================================================================
# IMPORTS
# =============================================================================

# -----------------------------------------------------------------------------
# functools.lru_cache - Caching decorator
# -----------------------------------------------------------------------------
# WHAT: A decorator that remembers (caches) function return values
# WHY: Loading settings from disk is slow. We only want to do it ONCE.
#
# HOW IT WORKS:
#   First call:  get_settings() → reads .env file → returns Settings → STORES in cache
#   Second call: get_settings() → checks cache → returns cached Settings (NO file read!)
#
# PYTHON COMPARISON:
#   Without cache - like looking up a phone number in phonebook every time
#   With cache - like writing it on sticky note after first lookup
# -----------------------------------------------------------------------------
from functools import lru_cache

# -----------------------------------------------------------------------------
# typing.Optional - Type hint for "value OR None"
# -----------------------------------------------------------------------------
# WHAT: Tells Python (and your IDE) that a variable can be a value OR None
#
# EXAMPLE:
#   name: str           → MUST be a string, cannot be None
#   name: Optional[str] → Can be a string OR None
#
# WHY: Helps catch bugs. IDE warns if you forget to handle None case.
# -----------------------------------------------------------------------------
from typing import Optional

# -----------------------------------------------------------------------------
# pydantic.Field - Add metadata to settings
# -----------------------------------------------------------------------------
# WHAT: Wraps a setting with extra information (default value, description)
#
# WITHOUT Field:
#   port: int = 8000  # Just a value, no description
#
# WITH Field:
#   port: int = Field(default=8000, description="Server port")
#   # Now we have documentation built-in!
# -----------------------------------------------------------------------------
from pydantic import Field, field_validator

# -----------------------------------------------------------------------------
# pydantic_settings - Load settings from environment
# -----------------------------------------------------------------------------
# WHAT: A Pydantic extension that automatically reads from:
#   1. Environment variables (export PORT=8000)
#   2. .env files (PORT=8000 in a file)
#
# WHY: Secrets should NEVER be in code. This lets us keep them separate.
# -----------------------------------------------------------------------------
from pydantic_settings import BaseSettings, SettingsConfigDict


# =============================================================================
# SETTINGS CLASS
# =============================================================================
# -----------------------------------------------------------------------------
# class Settings(BaseSettings):
# -----------------------------------------------------------------------------
# WHAT: A class that holds all our application settings
#
# BaseSettings vs BaseModel:
#   BaseModel    → Regular Pydantic (validates data)
#   BaseSettings → Pydantic + reads from environment variables
#
# INHERITANCE REMINDER (Python concept):
#   class Child(Parent):  → Child inherits all abilities from Parent
#   class Settings(BaseSettings): → Settings inherits env-reading from BaseSettings
# -----------------------------------------------------------------------------

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    HOW PRIORITY WORKS (highest to lowest):
    1. Environment variables: export OPENAI_API_KEY="sk-xxx"
    2. .env file contents: OPENAI_API_KEY=sk-xxx
    3. Default values defined below: default=""
    
    If same setting exists in multiple places, higher priority wins.
    """
    
    # -------------------------------------------------------------------------
    # Model Configuration
    # -------------------------------------------------------------------------
    # WHAT: Tells Pydantic HOW to behave when loading settings
    #
    # SettingsConfigDict is like a "settings for our settings" 
    # -------------------------------------------------------------------------
    model_config = SettingsConfigDict(
        # env_file: Which file to read settings from
        # The .env file in your project root
        env_file=".env",
        
        # env_file_encoding: How to read the file
        # UTF-8 supports special characters (é, ñ, 中文, etc.)
        env_file_encoding="utf-8",
        
        # case_sensitive: Does OPENAI_API_KEY equal openai_api_key?
        # False = yes, they're the same (more forgiving)
        case_sensitive=False,
        
        # extra: What to do with env vars NOT defined in this class?
        # "ignore" = skip them (don't crash)
        # "forbid" = crash if unknown var found
        extra="ignore",
    )
    
    # -------------------------------------------------------------------------
    # APPLICATION SETTINGS
    # -------------------------------------------------------------------------
    
    # app_name: Name of your application
    # Used in: logs, error messages, API documentation
    app_name: str = Field(
        default="voice-ai-platform",
        description="Name of the application"
    )
    
    # app_env: Which environment are we running in?
    # development = your laptop (debug mode, verbose errors)
    # staging = test server (like production but for testing)
    # production = real server (customers use this!)
    app_env: str = Field(
        default="development",
        description="Environment: development, staging, production"
    )
    
    # debug: Show extra information for debugging?
    # True = detailed error messages, more logging (NEVER in production!)
    # False = minimal info, secure
    debug: bool = Field(
        default=False,
        description="Enable debug mode (more logging, error details)"
    )
    
    # -------------------------------------------------------------------------
    # SERVER SETTINGS
    # -------------------------------------------------------------------------
    
    # host: Which IP address to listen on
    # "0.0.0.0" = Accept connections from ANY IP (required for Docker)
    # "127.0.0.1" = Only accept from localhost (your machine only)
    # "localhost" = Same as 127.0.0.1
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind the server to"
    )
    
    # port: Which port number to listen on
    # Standard ports: 80 (HTTP), 443 (HTTPS), 22 (SSH)
    # We use 8000 (common for development servers)
    # Valid range: 1-65535
    port: int = Field(
        default=8000,
        description="Port to run the server on"
    )
    
    # -------------------------------------------------------------------------
    # TWILIO SETTINGS (Telephony - Making/Receiving Phone Calls)
    # -------------------------------------------------------------------------
    # Twilio is the service that connects our app to the phone network.
    # Without Twilio, our app can't make or receive real phone calls.
    
    # Account SID: Your Twilio account identifier
    # Looks like: "ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    # Found at: https://console.twilio.com (dashboard)
    twilio_account_sid: str = Field(
        default="",
        description="Twilio Account SID"
    )
    
    # Auth Token: Your Twilio password/secret
    # Looks like: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    # Found at: https://console.twilio.com (dashboard, click to reveal)
    # KEEP THIS SECRET! Anyone with this can use your account.
    twilio_auth_token: str = Field(
        default="",
        description="Twilio Auth Token"
    )
    
    # Phone Number: Your Twilio phone number (Ghana number)
    # Format: "+233XXXXXXXXX" (include country code!)
    # This number is used for BOTH:
    #   - Inbound: Customers call this number
    #   - Outbound: Calls show this as caller ID
    twilio_phone_number: str = Field(
        default="",
        description="Twilio phone number for inbound AND outbound calls"
    )
    
    # -------------------------------------------------------------------------
    # DEEPGRAM SETTINGS (Speech-to-Text / STT)
    # -------------------------------------------------------------------------
    # Deepgram converts spoken audio into text.
    # Customer speaks → Deepgram → Text that AI can understand
    
    # API Key: Your Deepgram authentication key
    # Found at: https://console.deepgram.com → API Keys
    deepgram_api_key: str = Field(
        default="",
        description="Deepgram API key for speech recognition"
    )
    
    # -------------------------------------------------------------------------
    # OPENAI SETTINGS (Large Language Model / LLM)
    # -------------------------------------------------------------------------
    # OpenAI provides the "brain" - the AI that understands and responds.
    # Text from customer → OpenAI → Intelligent response
    
    # API Key: Your OpenAI authentication key
    # Found at: https://platform.openai.com/api-keys
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key"
    )
    
    # Model: Which AI model to use
    # Options:
    #   "gpt-4o-mini" - Fast, cheap, good for most tasks ($0.15/1M input tokens)
    #   "gpt-4o" - Smartest, more expensive ($2.50/1M input tokens)
    #   "gpt-3.5-turbo" - Older, cheaper, less capable
    # We use gpt-4o-mini for cost-effectiveness
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use"
    )
    
    # -------------------------------------------------------------------------
    # AWS SETTINGS (Amazon Polly - Text-to-Speech / TTS)
    # -------------------------------------------------------------------------
    # Polly converts text into spoken audio.
    # AI response text → Polly → Audio that customer hears
    
    # Access Key ID: Your AWS username (for programmatic access)
    # Found at: AWS Console → IAM → Users → Security credentials
    aws_access_key_id: str = Field(
        default="",
        description="AWS Access Key ID"
    )
    
    # Secret Access Key: Your AWS password
    # Found at: AWS Console → IAM → Users → Security credentials
    # Only shown ONCE when created - save it!
    aws_secret_access_key: str = Field(
        default="",
        description="AWS Secret Access Key"
    )
    
    # Region: Which AWS data center to use
    # "us-east-1" = Virginia, USA (most services available here)
    # "eu-west-1" = Ireland
    # "af-south-1" = Cape Town, South Africa (closest to Ghana!)
    # We use us-east-1 for reliability, can change later
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region for Polly"
    )
    
    # -------------------------------------------------------------------------
    # DATABASE SETTINGS (PostgreSQL)
    # -------------------------------------------------------------------------
    # PostgreSQL stores all our data:
    # - Call history
    # - Customer information
    # - Conversation logs
    # - Analytics
    
    # Database URL: Connection string with all info needed to connect
    # Format: postgresql://USERNAME:PASSWORD@HOST:PORT/DATABASE_NAME
    #
    # Breaking it down:
    #   postgresql://  → Protocol (like https:// for websites)
    #   postgres       → Username
    #   :postgres      → Password (after the colon)
    #   @localhost     → Host (where database runs)
    #   :5432          → Port (PostgreSQL default)
    #   /voiceai       → Database name
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/voiceai",
        description="PostgreSQL connection URL"
    )
    
    # -------------------------------------------------------------------------
    # REDIS SETTINGS (Cache/Fast Storage)
    # -------------------------------------------------------------------------
    # Redis is an in-memory database (super fast!).
    # Used for:
    # - Session storage (who's currently on a call)
    # - Caching (avoid recalculating same things)
    # - Rate limiting (prevent abuse)
    
    # Redis URL: Connection string
    # Format: redis://HOST:PORT/DATABASE_NUMBER
    #
    # Breaking it down:
    #   redis://    → Protocol
    #   localhost   → Host
    #   :6379       → Port (Redis default)
    #   /0          → Database number (Redis has 16 databases: 0-15)
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # -------------------------------------------------------------------------
    # VALIDATORS - Custom validation logic
    # -------------------------------------------------------------------------
    # Validators run BEFORE the setting is stored.
    # If validation fails, Pydantic raises an error immediately.
    
    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        """
        Ensure app_env is one of the allowed values.
        
        WHAT THIS DOES:
        1. Receives the value someone tried to set (v)
        2. Checks if it's valid
        3. Returns the cleaned value OR raises error
        
        WHY @classmethod?
        Validators run BEFORE the object exists, so we can't use 'self'.
        We use 'cls' (the class) instead.
        
        EXAMPLE:
            APP_ENV=development  → ✅ Returns "development"
            APP_ENV=PRODUCTION   → ✅ Returns "production" (lowercased)
            APP_ENV=testing      → ❌ ValueError: must be one of [...]
        """
        allowed = ["development", "staging", "production"]
        if v.lower() not in allowed:
            raise ValueError(f"app_env must be one of: {allowed}")
        return v.lower()  # Always return lowercase for consistency
    
    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """
        Ensure port is in valid range.
        
        VALID PORTS: 1 to 65535
        WHY? Computer networking only allows these port numbers.
        
        COMMON PORTS:
            1-1023     = System ports (need admin/root access)
            1024-49151 = Registered ports (common apps)
            49152-65535 = Dynamic/private ports
        
        We typically use 8000, 8080, 3000, 5000 for development.
        """
        if not 1 <= v <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v
    
    # -------------------------------------------------------------------------
    # COMPUTED PROPERTIES - Values calculated from other settings
    # -------------------------------------------------------------------------
    # @property makes a method act like an attribute.
    # Instead of: settings.is_production()  (method call with parentheses)
    # We write:   settings.is_production    (attribute access, cleaner!)
    
    @property
    def is_production(self) -> bool:
        """
        Check if running in production environment.
        
        USAGE:
            if settings.is_production:
                # Don't show debug info to customers!
                pass
        """
        return self.app_env == "production"
    
    @property
    def is_development(self) -> bool:
        """
        Check if running in development environment.
        
        USAGE:
            if settings.is_development:
                # Show extra debug info for developers
                pass
        """
        return self.app_env == "development"


# =============================================================================
# SETTINGS INSTANCE (Singleton Pattern)
# =============================================================================
# WHAT IS A SINGLETON?
# A design pattern where only ONE instance of a class exists.
# Every time you ask for it, you get the SAME instance.
#
# WHY?
# - Settings should be consistent across the app
# - Loading settings is slow (file I/O)
# - We only need ONE copy of settings
#
# HOW WE ACHIEVE IT:
# @lru_cache() decorator caches the return value.
# First call creates Settings(), subsequent calls return cached version.
# =============================================================================

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Using lru_cache ensures we only load settings ONCE,
    not every time we import them.
    
    USAGE (Option 1 - via function):
        from src.config import get_settings
        settings = get_settings()
        print(settings.port)  # 8000
    
    Returns:
        Settings: The application settings instance
    """
    return Settings()


# -----------------------------------------------------------------------------
# Default instance for easy importing
# -----------------------------------------------------------------------------
# This line runs when the module is first imported.
# It creates ONE Settings instance that everyone shares.
#
# USAGE (Option 2 - direct import, RECOMMENDED):
#     from src.config import settings
#     print(settings.port)  # 8000
#
# This is cleaner than calling get_settings() every time.
# -----------------------------------------------------------------------------
settings = get_settings()