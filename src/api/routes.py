"""
HTTP Routes for Twilio Voice Webhooks.

WHY THIS FILE EXISTS:
- Twilio calls these endpoints when calls arrive
- We respond with TwiML instructions
- TwiML tells Twilio to connect to our WebSocket

ENDPOINTS:
    POST /api/v1/calls/inbound   - When someone calls your number
    POST /api/v1/calls/outbound  - When you make an outbound call
    POST /api/v1/calls/status    - Call status updates
    GET  /api/v1/test            - Health check

TWIML:
    TwiML (Twilio Markup Language) is XML that tells Twilio what to do.
    <Connect><Stream url="..."/></Connect> starts audio streaming.
"""

import logging
from fastapi import APIRouter, Form
from fastapi.responses import Response

from src.config import settings

logger = logging.getLogger(__name__)

# Create router for HTTP routes
router = APIRouter()


def twiml_response(content: str) -> Response:
    """
    Create a TwiML XML response.
    
    Args:
        content: The TwiML elements (inside <Response>)
    
    Returns:
        FastAPI Response with correct content-type
    
    EXAMPLE:
        twiml_response('<Say>Hello</Say>')
        
        Returns:
        <?xml version="1.0" encoding="UTF-8"?>
        <Response>
            <Say>Hello</Say>
        </Response>
    """
    xml = f'<?xml version="1.0" encoding="UTF-8"?><Response>{content}</Response>'
    
    return Response(
        content=xml,
        media_type="application/xml"
    )


@router.get("/test")
async def test():
    """
    Health check endpoint.
    
    Use this to verify:
    1. Server is running
    2. Configuration is loaded
    3. ngrok is working
    
    Test with:
        curl https://your-ngrok-url/api/v1/test
    """
    return {
        "status": "ok",
        "websocket_url": settings.ngrok_wss_url,
        "services": {
            "deepgram": bool(settings.deepgram_api_key),
            "groq": bool(settings.groq_api_key),
            "elevenlabs": bool(settings.elevenlabs_api_key),
        }
    }


@router.post("/calls/inbound")
async def handle_inbound_call(
    CallSid: str = Form(...),
    From: str = Form(default=""),
    To: str = Form(default=""),
):
    """
    Handle inbound calls (when someone calls your Twilio number).
    
    Twilio POSTs here with call details:
    - CallSid: Unique identifier for this call
    - From: Caller's phone number
    - To: Your Twilio number
    
    We respond with TwiML that tells Twilio to:
    1. Connect to our WebSocket for audio streaming
    
    The WebSocket handler takes over from there.
    """
    logger.info(f"📞 Inbound call: {CallSid}")
    logger.info(f"   From: {From}")
    logger.info(f"   To: {To}")

    # Get WebSocket URL from settings
    stream_url = settings.ngrok_wss_url
    
    if not stream_url:
        logger.error("❌ NGROK_WSS_URL not configured!")
        return twiml_response('<Say>System error. Please try again later.</Say>')

    # Respond with TwiML to connect to our WebSocket
    # <Connect><Stream> tells Twilio to open a WebSocket and stream audio
    return twiml_response(f'<Connect><Stream url="{stream_url}" /></Connect>')


@router.post("/calls/outbound")
async def handle_outbound_call(
    CallSid: str = Form(...),
    From: str = Form(default=""),
    To: str = Form(default=""),
):
    """
    Handle outbound calls (when you call someone using Twilio).
    
    Same as inbound - we connect to our WebSocket for audio streaming.
    The only difference is who initiated the call.
    """
    logger.info(f"📞 Outbound call: {CallSid}")
    logger.info(f"   From: {From}")
    logger.info(f"   To: {To}")

    stream_url = settings.ngrok_wss_url
    
    if not stream_url:
        logger.error("❌ NGROK_WSS_URL not configured!")
        return twiml_response('<Say>System error. Please try again later.</Say>')

    return twiml_response(f'<Connect><Stream url="{stream_url}" /></Connect>')


@router.post("/calls/status")
async def handle_call_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: str = Form(default="0"),
):
    """
    Handle call status updates from Twilio.
    
    Twilio sends status updates throughout the call:
    - initiated: Call is starting
    - ringing: Phone is ringing
    - in-progress: Call is connected
    - completed: Call ended normally
    - busy: Recipient is busy
    - no-answer: No one answered
    - failed: Call failed
    
    Useful for:
    - Logging call history
    - Tracking call duration
    - Debugging issues
    """
    logger.info(f"📊 Call status: {CallSid} → {CallStatus} (duration: {CallDuration}s)")
    
    return {"status": "received"}
