"""
Text-to-Speech (TTS) Service using AWS Polly.
This is the MOUTH of our AI system - it converts text to spoken audio.
"""

import logging
import audioop
from typing import Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from src.config import settings

logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech Service using AWS Polly."""
    
    def __init__(self):
        """Initialize the TTS Service."""
        self.access_key = settings.aws_access_key_id
        self.secret_key = settings.aws_secret_access_key
        self.region = settings.aws_region
        
        if self.access_key and self.secret_key:
            self.client = boto3.client(
                'polly',
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name=self.region
            )
            logger.info(f"AWS Polly TTS Service initialized in region: {self.region}")
        else:
            self.client = None
            logger.warning("AWS credentials not found - TTS disabled")
    
    async def synthesize_speech(
        self,
        text: str,
        voice_id: str = "Joanna",
        output_format: str = "mp3"
    ) -> Optional[bytes]:
        """Convert text to speech audio."""
        if not self.client:
            logger.error("TTS Service not initialized - missing AWS credentials")
            return None
        
        try:
            logger.info(f"Synthesizing speech: {text[:50]}...")
            
            response = self.client.synthesize_speech(
                Text=text,
                OutputFormat=output_format,
                VoiceId=voice_id,
                Engine="neural"
            )
            
            audio_data = response['AudioStream'].read()
            
            logger.info(f"Speech synthesized: {len(audio_data)} bytes")
            
            return audio_data
            
        except (BotoCoreError, ClientError) as e:
            logger.error(f"TTS synthesis failed: {str(e)}")
            return None
    
    async def synthesize_for_twilio(self, text: str, voice_id: str = "Joanna") -> Optional[bytes]:
        """
        Convert text to speech in Twilio-compatible mulaw format.
        
        Twilio Media Streams require:
        - Format: mulaw (u-law)
        - Sample rate: 8000 Hz
        - Channels: 1 (mono)
        
        Process:
        1. Get PCM audio from Polly at 8000 Hz
        2. Convert PCM (16-bit linear) to mulaw
        """
        if not self.client:
            logger.error("TTS Service not initialized - missing AWS credentials")
            return None
        
        try:
            logger.info(f"Synthesizing for Twilio: {text[:50]}...")
            
            # Get PCM audio at 8000 Hz from Polly
            response = self.client.synthesize_speech(
                Text=text,
                OutputFormat="pcm",
                VoiceId=voice_id,
                Engine="neural",
                SampleRate="8000"
            )
            
            pcm_audio = response['AudioStream'].read()
            logger.info(f"PCM audio from Polly: {len(pcm_audio)} bytes")
            
            # Convert 16-bit PCM to 8-bit mulaw
            # audioop.lin2ulaw(fragment, width)
            # width = 2 because PCM is 16-bit (2 bytes per sample)
            mulaw_audio = audioop.lin2ulaw(pcm_audio, 2)
            
            logger.info(f"Converted to mulaw: {len(mulaw_audio)} bytes")
            
            return mulaw_audio
            
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Twilio TTS synthesis failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Audio conversion failed: {str(e)}")
            return None
    
    def get_available_voices(self, language_code: str = "en-US") -> list:
        """Get list of available voices for a language."""
        if not self.client:
            return []
        
        try:
            response = self.client.describe_voices(LanguageCode=language_code)
            voices = [
                {
                    "id": voice["Id"],
                    "name": voice["Name"],
                    "gender": voice["Gender"]
                }
                for voice in response["Voices"]
            ]
            return voices
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Failed to get voices: {str(e)}")
            return []


tts_service = TTSService()