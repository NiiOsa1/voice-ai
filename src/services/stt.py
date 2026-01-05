"""
Speech-to-Text (STT) Service using Deepgram.
Converts spoken audio into text - the ears of our AI system.
"""

import logging
import audioop
import wave
import io
from typing import Optional

from deepgram import DeepgramClient, PrerecordedOptions

from src.config import settings

logger = logging.getLogger(__name__)


class STTService:
    """Speech-to-Text Service using Deepgram."""
    
    def __init__(self):
        """Initialize the STT Service."""
        self.api_key = settings.deepgram_api_key
        
        if self.api_key:
            self.client = DeepgramClient(self.api_key)
            logger.info("Deepgram STT Service initialized")
        else:
            self.client = None
            logger.warning("Deepgram API key not found - STT disabled")
    
    async def transcribe_audio(self, audio_data: bytes, mimetype: str = "audio/wav") -> Optional[str]:
        """Convert audio bytes to text."""
        if not self.client:
            logger.error("STT Service not initialized - missing API key")
            return None
        
        try:
            logger.info(f"Transcribing audio: {len(audio_data)} bytes, format: {mimetype}")
            
            options = PrerecordedOptions(
                model="nova-2",
                language="en",
                smart_format=True,
                punctuate=True,
            )
            
            payload = {
                "buffer": audio_data,
                "mimetype": mimetype
            }
            
            response = self.client.listen.prerecorded.v("1").transcribe_file(
                payload,
                options
            )
            
            transcript = response.results.channels[0].alternatives[0].transcript
            
            if transcript:
                logger.info(f"Transcription successful: {transcript[:50]}...")
            else:
                logger.warning("Transcription returned empty result")
            
            return transcript
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            return None
    
    def _mulaw_to_wav(self, mulaw_data: bytes, sample_rate: int = 8000) -> bytes:
        """
        Convert mulaw audio to WAV format.
        
        1. Convert mulaw to linear PCM (16-bit)
        2. Wrap in WAV file format with proper headers
        """
        # Convert mulaw to 16-bit linear PCM
        pcm_data = audioop.ulaw2lin(mulaw_data, 2)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)        # Mono
            wav_file.setsampwidth(2)         # 16-bit = 2 bytes
            wav_file.setframerate(sample_rate)  # 8000 Hz
            wav_file.writeframes(pcm_data)
        
        # Get the WAV bytes
        wav_buffer.seek(0)
        return wav_buffer.read()
    
    async def transcribe_twilio_audio(self, audio_data: bytes) -> Optional[str]:
        """
        Transcribe audio from Twilio Media Streams.
        
        Twilio sends mulaw at 8000 Hz.
        We convert to WAV and send to Deepgram.
        """
        if not self.client:
            logger.error("STT Service not initialized - missing API key")
            return None
        
        try:
            logger.info(f"Transcribing Twilio audio: {len(audio_data)} bytes")
            
            # Convert mulaw to proper WAV format
            wav_audio = self._mulaw_to_wav(audio_data, sample_rate=8000)
            logger.info(f"Converted to WAV: {len(wav_audio)} bytes")
            
            options = PrerecordedOptions(
                model="nova-2",
                language="en",
                smart_format=True,
                punctuate=True,
            )
            
            payload = {
                "buffer": wav_audio,
                "mimetype": "audio/wav"
            }
            
            response = self.client.listen.prerecorded.v("1").transcribe_file(
                payload,
                options
            )
            
            transcript = response.results.channels[0].alternatives[0].transcript
            
            if transcript:
                logger.info(f"Twilio transcription successful: {transcript[:50]}...")
            else:
                logger.warning("Twilio transcription returned empty result")
            
            return transcript
            
        except Exception as e:
            logger.error(f"Twilio transcription failed: {str(e)}")
            return None
    
    async def transcribe_url(self, audio_url: str) -> Optional[str]:
        """Transcribe audio from a URL."""
        if not self.client:
            logger.error("STT Service not initialized - missing API key")
            return None
        
        try:
            logger.info(f"Transcribing from URL: {audio_url}")
            
            options = PrerecordedOptions(
                model="nova-2",
                language="en",
                smart_format=True,
                punctuate=True,
            )
            
            payload = {"url": audio_url}
            
            response = self.client.listen.prerecorded.v("1").transcribe_url(
                payload,
                options
            )
            
            transcript = response.results.channels[0].alternatives[0].transcript
            
            if transcript:
                logger.info(f"Transcription successful: {transcript[:50]}...")
            else:
                logger.warning("Transcription returned empty result")
            
            return transcript
            
        except Exception as e:
            logger.error(f"URL transcription failed: {str(e)}")
            return None


stt_service = STTService()