"""
Voice AI Platform - API Routes.

This file contains all the endpoints (URLs) for handling voice calls.
Twilio will call these URLs when phone events happen.
"""

# =============================================================================
# IMPORTS
# =============================================================================

from fastapi import APIRouter, Request, Form
from fastapi.responses import Response
from typing import Optional
import logging
from datetime import datetime


# =============================================================================
# SETUP
# =============================================================================

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# HELPER FUNCTION
# =============================================================================

def create_twiml_response(twiml_content: str) -> Response:
    """
    Create a TwiML XML response for Twilio.
    
    Parameters:
        twiml_content: The TwiML commands (e.g., <Say>Hello</Say>)
        
    Returns:
        Response: FastAPI Response with XML content type
    """
    xml_response = f'''<?xml version="1.0" encoding="UTF-8"?>
<Response>
    {twiml_content}
</Response>'''
    
    return Response(content=xml_response, media_type="application/xml")


# =============================================================================
# TEST ROUTE
# =============================================================================

@router.get("/test")
async def test_route():
    """
    Simple test route to verify the router is working.
    
    URL: GET /api/v1/test
    """
    return {"message": "Router is working!", "status": "ok"}


# =============================================================================
# INBOUND CALL WEBHOOK
# =============================================================================

@router.post("/calls/inbound")
async def handle_inbound_call(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(None),
    Direction: str = Form(None),
    CallerCity: str = Form(None),
    CallerCountry: str = Form(None),
):
    """
    Handle incoming phone calls.
    
    Twilio calls this webhook when someone dials your Twilio number.
    
    URL: POST /api/v1/calls/inbound
    """
    logger.info("=" * 50)
    logger.info("INCOMING CALL")
    logger.info(f"  Call ID: {CallSid}")
    logger.info(f"  From: {From}")
    logger.info(f"  To: {To}")
    logger.info(f"  Status: {CallStatus}")
    logger.info(f"  Location: {CallerCity}, {CallerCountry}")
    logger.info("=" * 50)
    
    greeting = '''
        <Say voice="alice" language="en-US">
            Hello! Welcome to Voice AI Platform. 
            This is a test of the inbound call system.
            Thank you for calling. Goodbye!
        </Say>
    '''
    
    return create_twiml_response(greeting)


# =============================================================================
# OUTBOUND CALL WEBHOOK
# =============================================================================

@router.post("/calls/outbound")
async def handle_outbound_call(
    CallSid: str = Form(...),
    From: str = Form(...),
    To: str = Form(...),
    CallStatus: str = Form(None),
    Direction: str = Form(None),
):
    """
    Handle outbound call connections.
    
    When you initiate a call to a customer and they answer,
    Twilio calls this webhook to get instructions.
    
    URL: POST /api/v1/calls/outbound
    """
    logger.info("=" * 50)
    logger.info("OUTBOUND CALL CONNECTED")
    logger.info(f"  Call ID: {CallSid}")
    logger.info(f"  From (us): {From}")
    logger.info(f"  To (customer): {To}")
    logger.info(f"  Status: {CallStatus}")
    logger.info("=" * 50)
    
    message = '''
        <Say voice="alice" language="en-US">
            Hello! This is an automated call from Voice AI Platform.
            This is a test of the outbound call system.
            Thank you for your time. Goodbye!
        </Say>
    '''
    
    return create_twiml_response(message)


# =============================================================================
# CALL STATUS WEBHOOK
# =============================================================================

@router.post("/calls/status")
async def handle_call_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    From: str = Form(None),
    To: str = Form(None),
    Direction: str = Form(None),
    CallDuration: Optional[str] = Form(None),
):
    """
    Handle call status updates from Twilio.
    
    Twilio calls this webhook whenever a call's status changes.
    
    URL: POST /api/v1/calls/status
    """
    logger.info("=" * 50)
    logger.info("CALL STATUS UPDATE")
    logger.info(f"  Call ID: {CallSid}")
    logger.info(f"  Status: {CallStatus}")
    logger.info(f"  From: {From}")
    logger.info(f"  To: {To}")
    logger.info(f"  Duration: {CallDuration} seconds")
    logger.info("=" * 50)
    
    if CallStatus == "completed":
        logger.info(f"Call {CallSid} completed successfully")
        
    elif CallStatus == "no-answer":
        logger.info(f"Call {CallSid} - No answer")
        
    elif CallStatus == "busy":
        logger.info(f"Call {CallSid} - Line busy")
        
    elif CallStatus == "failed":
        logger.info(f"Call {CallSid} - Failed")
        
    elif CallStatus == "in-progress":
        logger.info(f"Call {CallSid} - In progress")
    
    return {
        "received": True,
        "call_sid": CallSid,
        "status": CallStatus,
        "timestamp": datetime.now().isoformat()
    }