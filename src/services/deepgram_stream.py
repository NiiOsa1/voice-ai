"""
Deepgram Streaming Client - WITH KEEPALIVE + PHONE OPTIMIZATION

Proper solution to prevent connection death.
Optimized for phone calls from Ghana/Africa.
"""

import json
import asyncio
import logging
from typing import Callable, Optional

import websockets

logger = logging.getLogger(__name__)


class DeepgramStreamClient:
    """Deepgram streaming with KeepAlive support."""
    
    DEEPGRAM_URL = "wss://api.deepgram.com/v1/listen"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.on_partial: Optional[Callable] = None
        self.on_final: Optional[Callable] = None
        self.running = False
        self.keepalive_task: Optional[asyncio.Task] = None
    
    async def connect(
        self,
        on_partial: Callable[[str], None],
        on_final: Callable[[str], None]
    ) -> bool:
        """Connect to Deepgram with streaming config."""
        self.on_partial = on_partial
        self.on_final = on_final
        
        # OPTIMIZED for phone calls from Ghana/Africa
        params = {
            "encoding": "mulaw",
            "sample_rate": 8000,
            "channels": 1,
            "model": "nova-2-conversationalai",      # Better for phone audio
            "language": "en",
            "punctuate": "true",
            "interim_results": "true",
            "endpointing": 500,              # Quick response
            "utterance_end_ms": 1500,        # Backup for network issues
            "vad_events": "true",
            "smart_format": "true",           # Better formatting
            "no_delay": "true",               # Return results immediately
            "filler_words": "true",           # Catch um, uh, etc
        }
        
        query = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.DEEPGRAM_URL}?{query}"
        
        headers = [("Authorization", f"Token {self.api_key}")]
        
        try:
            self.ws = await websockets.connect(
                url,
                additional_headers=headers,
                ping_interval=5,
                ping_timeout=10
            )
            self.running = True
            
            asyncio.create_task(self._receive_loop())
            self.keepalive_task = asyncio.create_task(self._keepalive_loop())
            
            logger.info("🎧 Connected to Deepgram STT")
            return True
            
        except TypeError:
            try:
                self.ws = await websockets.connect(
                    url,
                    extra_headers={"Authorization": f"Token {self.api_key}"},
                    ping_interval=5,
                    ping_timeout=10
                )
                self.running = True
                asyncio.create_task(self._receive_loop())
                self.keepalive_task = asyncio.create_task(self._keepalive_loop())
                logger.info("🎧 Connected to Deepgram STT")
                return True
            except Exception as e:
                logger.error(f"❌ Deepgram connection failed: {e}")
                return False
        except Exception as e:
            logger.error(f"❌ Deepgram connection failed: {e}")
            return False
    
    async def _keepalive_loop(self) -> None:
        """Send KeepAlive messages to prevent timeout."""
        logger.info("💓 Deepgram KeepAlive started")
        
        while self.running:
            try:
                await asyncio.sleep(5)
                
                if self.ws and self.running:
                    await self.ws.send(json.dumps({"type": "KeepAlive"}))
                    logger.info("💓 Sent KeepAlive to Deepgram")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"⚠️ KeepAlive error: {e}")
                break
    
    async def _receive_loop(self) -> None:
        """Receive and process transcripts."""
        try:
            async for message in self.ws:
                if not self.running:
                    break
                    
                data = json.loads(message)
                msg_type = data.get("type", "")
                
                if msg_type == "Results":
                    channel = data.get("channel", {})
                    alternatives = channel.get("alternatives", [])
                    
                    if alternatives:
                        transcript = alternatives[0].get("transcript", "")
                        is_final = data.get("is_final", False)
                        
                        if transcript:
                            if is_final:
                                logger.info(f"✅ Final: {transcript}")
                                if self.on_final:
                                    asyncio.create_task(self.on_final(transcript))
                            else:
                                if self.on_partial:
                                    asyncio.create_task(self.on_partial(transcript))
                                    
        except websockets.exceptions.ConnectionClosed:
            logger.warning("⚠️ Deepgram connection closed")
        except Exception as e:
            logger.error(f"❌ Deepgram receive error: {e}")
        finally:
            self.running = False
    
    async def send_audio(self, audio: bytes) -> None:
        """Send audio chunk to Deepgram."""
        if self.ws and self.running:
            try:
                await self.ws.send(audio)
            except Exception as e:
                logger.error(f"❌ Send audio error: {e}")
                self.running = False
    
    async def close(self) -> None:
        """Close the connection."""
        self.running = False
        
        if self.keepalive_task:
            self.keepalive_task.cancel()
            try:
                await self.keepalive_task
            except asyncio.CancelledError:
                pass
        
        if self.ws:
            try:
                await self.ws.close()
            except:
                pass
        
        logger.info("🔌 Deepgram closed")