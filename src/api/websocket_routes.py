"""
WebSocket Routes for Twilio Media Streams.

WHY THIS FILE EXISTS:
- Defines the WebSocket endpoint URL
- Twilio connects here to stream audio
- Routes to our WebSocket handler

ENDPOINT:
    ws://your-server/ws/twilio-media-stream
    or
    wss://your-server/ws/twilio-media-stream (secure)

This is the URL you put in TwiML <Stream> element.
"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.api.websocket_handler import handle_media_stream

logger = logging.getLogger(__name__)

# Create router for WebSocket routes
router = APIRouter()


@router.websocket("/ws/twilio-media-stream")
async def twilio_media_stream(websocket: WebSocket):
    """
    WebSocket endpoint for Twilio Media Streams.
    
    Twilio connects here when we respond with:
    <Connect><Stream url="wss://xxx/ws/twilio-media-stream"/></Connect>
    
    Args:
        websocket: FastAPI WebSocket connection
    """
    try:
        # Hand off to our handler
        await handle_media_stream(websocket)
        
    except WebSocketDisconnect:
        # Normal disconnection - call ended
        logger.info("📴 Twilio WebSocket disconnected normally")
        
    except Exception as e:
        # Unexpected error
        logger.error(f"❌ WebSocket route error: {e}")
