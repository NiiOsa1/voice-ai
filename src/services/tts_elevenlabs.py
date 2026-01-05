"""
Text-to-Speech Service using ElevenLabs.

WHY THIS FILE EXISTS:
- Converts AI text responses to spoken audio
- Uses ElevenLabs for natural, human-like voices
- Outputs Twilio-compatible format (mulaw) DIRECTLY

OPTIMIZATIONS APPLIED:
- eleven_flash_v2_5: 75ms latency (fastest model)
- ulaw_8000: Native Twilio format (no conversion needed!)
"""

import logging
from typing import Optional

from elevenlabs import ElevenLabs

from src.config import settings

logger = logging.getLogger(__name__)


class ElevenLabsTTSService:
    """
    Natural Text-to-Speech with Twilio-compatible output.
    
    USAGE:
        from src.services.tts_elevenlabs import elevenlabs_tts
        
        # For Twilio (mulaw format) - USE THIS FOR PHONE CALLS:
        audio = await elevenlabs_tts.synthesize_for_twilio(
            text="Hello, how can I help?",
            voice="rachel"
        )
        
        # For other uses (MP3 format):
        mp3_audio = await elevenlabs_tts.synthesize_mp3(
            text="Hello!",
            voice="rachel"
        )
    """

    # ─────────────────────────────────────────────────────────────
    # AVAILABLE VOICES
    # ─────────────────────────────────────────────────────────────
    # Map friendly names to ElevenLabs voice IDs
    # You can preview these at: https://elevenlabs.io/voice-library
    
    VOICES = {
        # Female voices
        "rachel": "21m00Tcm4TlvDq8ikWAM",    # Calm, professional
        "sarah": "EXAVITQu4vr4xnSDxMaL",     # Soft, friendly
        "emily": "LcfcDJNUP1GQjkzn1xUU",     # Calm, clear
        "matilda": "XrExE9yKIg1WjnnlVkGX",   # Warm, welcoming
        "lily": "pFZP5JQG7iQjIQuC4Bku",      # British, warm
        
        # Male voices
        "dave": "CYw3kZ02Hs0563khs1Fj",      # Conversational
        "charlie": "IKne3meq5aSn9XLyUdCD",   # Casual, friendly
        "james": "ZQe5CZNOzWyzPSCn5a3c",     # British, calm
        "george": "JBFqnCBsd6RMkjVDRZzb",    # British, warm
        "matthew": "Yko7PKs6WkxO6YstNZgX",   # Audiobook narrator
    }

    def __init__(self):
        """
        Initialize ElevenLabs client.
        
        Uses default US endpoint (api.elevenlabs.io).
        """
        self.api_key = settings.elevenlabs_api_key

        if self.api_key:
            self.client = ElevenLabs(api_key=self.api_key)
            logger.info("✅ ElevenLabs TTS ready (flash_v2_5 + ulaw_8000)")
        else:
            self.client = None
            logger.warning("⚠️ ElevenLabs API key not found - TTS disabled")

    async def synthesize_for_twilio(
        self,
        text: str,
        voice: str = "rachel"
    ) -> Optional[bytes]:
        """
        Generate mulaw audio DIRECTLY for Twilio Media Streams.
        
        THIS IS THE PRIMARY METHOD FOR PHONE CALLS.
        
        OPTIMIZATIONS:
        - eleven_flash_v2_5: 75ms latency (vs 150ms for turbo)
        - ulaw_8000: Native Twilio format (no conversion!)
        
        Args:
            text: The text to convert to speech
            voice: Voice name (rachel, sarah, dave, etc.)
        
        Returns:
            mulaw audio bytes ready for Twilio, or None if error
        """
        if not self.client:
            logger.error("❌ ElevenLabs client not initialized")
            return None

        try:
            # Look up voice ID from friendly name, or use as-is if not found
            voice_id = self.VOICES.get(voice.lower(), voice)
            
            logger.info(f"🗣️ Generating speech: {text[:50]}...")

            # Call ElevenLabs API with OPTIMIZED settings
            audio_generator = self.client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_flash_v2_5",  # Fastest: ~75ms latency
                output_format="ulaw_8000",     # Native Twilio format!
            )

            # Collect all audio chunks from generator
            mulaw_data = b"".join(audio_generator)
            
            logger.info(f"✅ Generated {len(mulaw_data)} bytes mulaw")
            return mulaw_data

        except Exception as e:
            logger.error(f"❌ ElevenLabs error: {e}")
            return None

    async def synthesize_mp3(
        self,
        text: str,
        voice: str = "rachel"
    ) -> Optional[bytes]:
        """
        Generate MP3 audio from text (for non-Twilio uses).
        
        Use this for:
        - Saving audio files
        - Web playback
        - Testing
        
        For phone calls, use synthesize_for_twilio() instead!
        
        Args:
            text: The text to convert to speech
            voice: Voice name (see VOICES dict) or ElevenLabs voice ID
        
        Returns:
            MP3 audio bytes, or None if error
        """
        if not self.client:
            logger.error("❌ ElevenLabs client not initialized")
            return None

        try:
            voice_id = self.VOICES.get(voice.lower(), voice)
            
            logger.info(f"🗣️ Generating MP3: {text[:50]}...")

            audio_generator = self.client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id="eleven_flash_v2_5",
                output_format="mp3_44100_128",
            )

            mp3_data = b"".join(audio_generator)
            
            logger.info(f"✅ Generated {len(mp3_data)} bytes MP3")
            return mp3_data

        except Exception as e:
            logger.error(f"❌ ElevenLabs error: {e}")
            return None


# ─────────────────────────────────────────────────────────────────
# SINGLETON INSTANCE
# ─────────────────────────────────────────────────────────────────
# Create one instance that all code shares
# Import as: from src.services.tts_elevenlabs import elevenlabs_tts

elevenlabs_tts = ElevenLabsTTSService()
