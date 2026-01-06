"""
WebSocket Handler - PRODUCTION GRADE

Features:
- Natural conversation flow (no repetitive phrases)
- Context-aware responses (remembers conversation)
- Filters garbage inputs only
- Deepgram KeepAlive
- Barge-in support
- Auto-reconnect
"""

import json
import base64
import logging
import asyncio
from typing import Optional, List, Dict
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect

from src.config import settings
from src.services.deepgram_stream import DeepgramStreamClient
from src.services.llm_groq import groq_llm
from src.services.tts_elevenlabs import elevenlabs_tts

logger = logging.getLogger(__name__)


# PRODUCTION-GRADE PROMPT
SYSTEM_PROMPT = """You are Nana Ama, a warm and friendly Ghanaian phone assistant.

CONVERSATION RULES:
1. Response length - KEEP IT SHORT FOR PHONE:
   - Simple chat: 5-15 words max
   - Questions/explanations: 2-3 sentences MAX (under 50 words)
   - Never give long lists - give 2-3 items, then ask "want more?"
   - Phone calls need SHORT responses - user can always ask for more
2. Be conversational and natural - like talking to a friend
3. Dont over repeat "How can I help you" or "How can I assist you" 
4. If you don't understand, say "Sorry, I missed that" or "Come again?"
5. If you don't know something, say "I don't know that one" - don't guess
6. NO asterisks, emotes, or robotic phrases
7. Remember what was discussed - don't restart the conversation
9. USE CONTEXT: If user refers to "it", "that", "the recipe", etc., use conversation history to understand what they mean
10. Reference previous topics naturally: "About the Jollof rice you asked..." or "Going back to what you said..."
8. When giving instructions (like recipes), give the COMPLETE answer, don't make user ask "is that all?"

GHANAIAN CONTEXT:
- Jollof rice: Ghana's is the best, Nigeria wishes!
- Ghana has 16 regions (changed from 10 in 2019)
- Popular foods: Banku, Fufu, Waakye, Kelewele
- Capital: Accra

RESPONSE STYLE:
- Sound warm and human
- Use varied phrases like: "Ah I see", "Oh okay", "Right", "Sure thing"
- Keep the conversation flowing naturally
- If user seems confused, gently clarify
- Dont say hey what's on yhour mind

When user says bye/goodbye: "Alright, take care!"
"""

GREETING = "Hello! Nana Ama here. How can I help you today?"

GOODBYE_PHRASES = ["bye", "goodbye", "see you", "take care", "hang up", "end call", "later"]


class State(Enum):
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"


class CallHandler:
    """Production-grade call handler."""

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.stream_sid: Optional[str] = None
        self.call_sid: Optional[str] = None
        self.deepgram: Optional[DeepgramStreamClient] = None
        self.conversation_history: List[Dict] = []
        self.state = State.IDLE
        self.greeted = False
        self.audio_queue: asyncio.Queue = asyncio.Queue()
        self.interrupted = False
        self.should_hangup = False
        self.deepgram_ready = False
        self.audio_sender_task = None
        self.heartbeat_task = None
        self.last_transcript_time = 0.0
        self.reconnecting = False
        self.last_final_text = ""    # Track last processed text for echo detection
        self.last_final_time = 0.0   # Track when it was said

    async def process_message(self, message: dict) -> None:
        """Process WebSocket message from Twilio."""
        event = message.get("event")

        if event == "connected":
            logger.info("🔌 Twilio connected")

        elif event == "start":
            start = message.get("start", {})
            self.stream_sid = start.get("streamSid")
            self.call_sid = start.get("callSid")
            logger.info(f"📞 Call started: {self.call_sid}")
            
            asyncio.create_task(self._connect_deepgram())
            self.audio_sender_task = asyncio.create_task(self._audio_sender())
            self.heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
            
            if not self.greeted:
                self.greeted = True
                await self._speak(GREETING)

        elif event == "media":
            media = message.get("media", {})
            payload = media.get("payload", "")
            if payload:
                audio = base64.b64decode(payload)
                await self.audio_queue.put(audio)

        elif event == "mark":
            mark = message.get("mark", {}).get("name", "")
            logger.info(f"✅ Mark: {mark}")
            
            if self.should_hangup:
                await asyncio.sleep(0.2)
                await self._hangup()
                return
            
            if self.state == State.SPEAKING and not self.interrupted:
                self.state = State.LISTENING
                self.last_transcript_time = asyncio.get_event_loop().time()
                logger.info("🎤 Listening...")

        elif event == "stop":
            logger.info(f"📴 Call ended: {self.call_sid}")
            await self._cleanup()

    async def _connect_deepgram(self) -> None:
        """Connect to Deepgram."""
        try:
            self.deepgram = DeepgramStreamClient(settings.deepgram_api_key)
            connected = await self.deepgram.connect(
                on_partial=self._on_partial,
                on_final=self._on_final
            )
            self.deepgram_ready = connected
            self.last_transcript_time = asyncio.get_event_loop().time()
            if connected:
                logger.info("🎧 Deepgram ready")
        except Exception as e:
            logger.error(f"❌ Deepgram error: {e}")

    async def _reconnect_deepgram(self) -> None:
        """Reconnect Deepgram if it dies."""
        if self.reconnecting:
            return
        
        self.reconnecting = True
        logger.warning("🔄 Reconnecting Deepgram...")
        
        try:
            if self.deepgram:
                await self.deepgram.close()
            
            self.deepgram_ready = False
            self.deepgram = DeepgramStreamClient(settings.deepgram_api_key)
            connected = await self.deepgram.connect(
                on_partial=self._on_partial,
                on_final=self._on_final
            )
            
            self.deepgram_ready = connected
            self.last_transcript_time = asyncio.get_event_loop().time()
            
            if connected:
                logger.info("✅ Deepgram reconnected!")
            else:
                logger.error("❌ Deepgram reconnection failed")
                
        except Exception as e:
            logger.error(f"❌ Reconnection error: {e}")
        finally:
            self.reconnecting = False

    async def _heartbeat_monitor(self) -> None:
        """Backup monitor - reconnect if no transcript for 15 seconds."""
        logger.info("💓 Heartbeat monitor started (backup)")
        
        while True:
            try:
                await asyncio.sleep(5)
                
                if self.state == State.LISTENING and self.deepgram_ready:
                    silence = asyncio.get_event_loop().time() - self.last_transcript_time
                    
                    if silence > 15:
                        logger.warning(f"⚠️ No transcript for {silence:.0f}s - reconnecting")
                        await self._reconnect_deepgram()
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Heartbeat error: {e}")

    async def _audio_sender(self) -> None:
        """Send audio to Deepgram continuously."""
        logger.info("🎙️ Audio sender started")
        chunks = 0
        
        while True:
            try:
                audio = await asyncio.wait_for(self.audio_queue.get(), timeout=0.1)
                if self.deepgram and self.deepgram_ready:
                    await self.deepgram.send_audio(audio)
                    chunks += 1
                    if chunks % 500 == 0:
                        logger.info(f"🎙️ Sent {chunks} chunks")
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except:
                break

    async def _on_partial(self, text: str) -> None:
        """Handle partial transcript - for barge-in only."""
        if not text.strip():
            return
        
        self.last_transcript_time = asyncio.get_event_loop().time()
        
        if self.state == State.SPEAKING:
            # Echo detection: ignore if same as last final transcript
            text_clean = text.strip().lower().rstrip('.,!?')
            last_clean = self.last_final_text.strip().lower().rstrip('.,!?')
            time_since_final = asyncio.get_event_loop().time() - self.last_final_time
            
            # If same text within 2 seconds, it's an echo - ignore it
            if text_clean == last_clean and time_since_final < 2.0:
                logger.info(f"👻 Echo ignored: '{text}'")
                return
            
            # Require minimum 3 words to trigger barge-in
            # Prevents false triggers from single words, throat clearing, etc.
            word_count = len(text.strip().split())
            if word_count < 3:
                logger.info(f"👂 Partial too short ({word_count} words): '{text}'")
                return
            
            logger.info(f"🛑 Barge-in: '{text}'")
            self.interrupted = True
            self.state = State.LISTENING
            await self._clear_audio()

    async def _on_final(self, text: str) -> None:
        """Handle final transcript."""
        text = text.strip()
        if not text:
            return
        
        self.last_transcript_time = asyncio.get_event_loop().time()
        self.last_final_text = text  # Store for echo detection
        self.last_final_time = self.last_transcript_time
        
        if self.state in (State.PROCESSING, State.SPEAKING):
            return
        
        logger.info(f"👤 User: {text}")
        
        # Filter only garbage inputs (too short to be meaningful)
        # This allows all real speech through, only blocks punctuation-only or empty
        clean_text = text.strip()
        if len(clean_text) < 2 or clean_text in [".", ",", "?", "!", "-"]:
            logger.info(f"⏭️ Skipping garbage: '{text}'")
            return
        
        text_lower = text.lower()
        if any(phrase in text_lower for phrase in GOODBYE_PHRASES):
            self.should_hangup = True
            await self._speak("Thanks for calling! Take care now.")
        else:
            await self._respond(text)

    async def _respond(self, user_text: str) -> None:
        """Generate and speak response."""
        self.state = State.PROCESSING
        
        try:
            # Use more conversation history for context (8 messages = 4 exchanges)
            response = await groq_llm.generate_response(
                user_message=user_text,
                system_prompt=SYSTEM_PROMPT,
                conversation_history=self.conversation_history[-16:]  # Last 16 messages = 8 exchanges
            )
            
            if not response:
                response = "Sorry, I missed that."
            
            logger.info(f"🤖 Nana Ama: {response}")
            
            self.conversation_history.append({"role": "user", "content": user_text})
            self.conversation_history.append({"role": "assistant", "content": response})
            
            await self._speak(response)
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            self.state = State.LISTENING

    async def _speak(self, text: str) -> None:
        """Convert text to speech and send."""
        self.state = State.SPEAKING
        self.interrupted = False
        
        logger.info(f"🗣️ Speaking: {text}")
        
        audio = await elevenlabs_tts.synthesize_for_twilio(text=text, voice="rachel")
        
        if not audio:
            self.state = State.LISTENING
            return
        
        logger.info(f"📢 Sending {len(audio)} bytes")
        
        try:
            chunk_size = 320
            
            for i in range(0, len(audio), chunk_size):
                if self.interrupted:
                    self.state = State.LISTENING
                    return
                
                chunk = audio[i:i + chunk_size]
                payload = base64.b64encode(chunk).decode()
                
                await self.websocket.send_json({
                    "event": "media",
                    "streamSid": self.stream_sid,
                    "media": {"payload": payload}
                })
                
                await asyncio.sleep(0)
                await asyncio.sleep(0.035)  # 35ms = closer to real-time playback
            
            if not self.interrupted:
                await self.websocket.send_json({
                    "event": "mark",
                    "streamSid": self.stream_sid,
                    "mark": {"name": "done"}
                })
                logger.info("✅ Audio sent")
            
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            self.state = State.LISTENING

    async def _clear_audio(self) -> None:
        """Clear Twilio audio buffer."""
        try:
            await self.websocket.send_json({
                "event": "clear",
                "streamSid": self.stream_sid
            })
            self.last_transcript_time = asyncio.get_event_loop().time()
            logger.info("🔇 Cleared")
        except:
            pass

    async def _hangup(self) -> None:
        """End call."""
        try:
            from twilio.rest import Client
            client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
            client.calls(self.call_sid).update(status="completed")
            logger.info("📴 Hung up")
        except Exception as e:
            logger.error(f"❌ Hangup error: {e}")

    async def _cleanup(self) -> None:
        """Clean up resources."""
        if self.audio_sender_task:
            self.audio_sender_task.cancel()
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
        if self.deepgram:
            await self.deepgram.close()


async def handle_media_stream(websocket: WebSocket) -> None:
    """Main WebSocket handler."""
    await websocket.accept()
    logger.info("🧲 WebSocket accepted")
    
    handler = CallHandler(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            await handler.process_message(json.loads(data))
    except WebSocketDisconnect:
        logger.info("🔌 Disconnected")
        await handler._cleanup()
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        await handler._cleanup()
