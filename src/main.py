"""
Voice AI Platform - Main Application Entry Point.

WHY THIS FILE EXISTS:
- Creates and configures the FastAPI application
- Registers all HTTP and WebSocket routes
- Configures middleware (CORS, logging)
- Handles startup and shutdown events

HOW TO RUN:
    uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

    --reload: Auto-restart on code changes (development only)
    --host 0.0.0.0: Accept connections from any IP
    --port 8000: Listen on port 8000

ARCHITECTURE:
    main.py
    ├── Creates FastAPI app
    ├── Registers /api/v1/* routes (HTTP webhooks)
    ├── Registers /ws/* routes (WebSocket)
    └── Configures middleware
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings

# ─────────────────────────────────────────────────────────────────
# LOGGING CONFIGURATION
# ─────────────────────────────────────────────────────────────────
# Configure logging BEFORE anything else
# This ensures all modules use the same logging format

logging.basicConfig(
    # DEBUG shows everything, INFO shows less (production)
    level=logging.DEBUG if settings.debug else logging.INFO,
    
    # Format: timestamp - module - level - message
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# LIFESPAN EVENTS (Startup/Shutdown)
# ─────────────────────────────────────────────────────────────────
# asynccontextmanager lets us run code on startup and shutdown
# Everything before "yield" runs on startup
# Everything after "yield" runs on shutdown

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown.
    
    STARTUP (before yield):
    - Log configuration
    - Verify services are ready
    - Any initialization needed
    
    SHUTDOWN (after yield):
    - Clean up resources
    - Close connections
    - Log shutdown
    """
    # ─── STARTUP ───
    logger.info("=" * 60)
    logger.info("🚀 VOICE AI PLATFORM STARTING")
    logger.info("=" * 60)
    logger.info(f"📍 Environment: {settings.app_env}")
    logger.info(f"🐞 Debug mode: {settings.debug}")
    logger.info(f"🌐 WebSocket URL: {settings.ngrok_wss_url}")
    logger.info("")
    logger.info("📋 Services Status:")
    logger.info(f"   Deepgram:   {'✅ Ready' if settings.deepgram_api_key else '❌ Missing API key'}")
    logger.info(f"   Groq:       {'✅ Ready' if settings.groq_api_key else '❌ Missing API key'}")
    logger.info(f"   ElevenLabs: {'✅ Ready' if settings.elevenlabs_api_key else '❌ Missing API key'}")
    logger.info("=" * 60)
    
    yield  # Application runs here
    
    # ─── SHUTDOWN ───
    logger.info("=" * 60)
    logger.info("🛑 VOICE AI PLATFORM SHUTTING DOWN")
    logger.info("👋 Goodbye!")
    logger.info("=" * 60)


# ─────────────────────────────────────────────────────────────────
# CREATE FASTAPI APPLICATION
# ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.app_name,
    description="AI-powered voice platform for natural phone conversations",
    version="1.0.0",
    lifespan=lifespan,
    
    # API documentation URLs
    docs_url="/docs",           # Swagger UI
    redoc_url="/redoc",         # ReDoc
    openapi_url="/openapi.json" # OpenAPI schema
)


# ─────────────────────────────────────────────────────────────────
# MIDDLEWARE: CORS
# ─────────────────────────────────────────────────────────────────
# CORS = Cross-Origin Resource Sharing
# Allows web browsers to call our API from different domains
# We allow all origins (*) for development - restrict in production

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Allow all origins (restrict in production)
    allow_credentials=True,     # Allow cookies
    allow_methods=["*"],        # Allow all HTTP methods
    allow_headers=["*"],        # Allow all headers
)


# ─────────────────────────────────────────────────────────────────
# MIDDLEWARE: REQUEST LOGGING
# ─────────────────────────────────────────────────────────────────
# Log every HTTP request with timing information
# Useful for debugging and monitoring

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log all HTTP requests with timing.
    
    Output: GET /api/v1/test - 200 - 5ms
    """
    start_time = datetime.now()
    
    # Process the request
    response = await call_next(request)
    
    # Calculate duration
    duration_ms = (datetime.now() - start_time).total_seconds() * 1000
    
    # Log (skip health checks to reduce noise)
    if request.url.path != "/health":
        logger.info(
            f"{request.method} {request.url.path} - {response.status_code} - {duration_ms:.0f}ms"
        )
    
    return response


# ─────────────────────────────────────────────────────────────────
# ROOT ENDPOINTS
# ─────────────────────────────────────────────────────────────────
# Basic endpoints that don't need to be in separate route files

@app.get("/")
async def root():
    """
    Root endpoint - basic info about the API.
    """
    return {
        "name": "Voice AI Platform",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring.
    
    Use this to verify the server is running:
        curl http://localhost:8000/health
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
    }


# ─────────────────────────────────────────────────────────────────
# REGISTER ROUTE FILES
# ─────────────────────────────────────────────────────────────────
# Import and register routes from separate files
# This keeps main.py clean and organized

# HTTP routes (Twilio webhooks)
from src.api.routes import router as api_router
app.include_router(
    api_router,
    prefix="/api/v1",    # All routes prefixed with /api/v1
    tags=["Voice API"]   # Group in docs
)

# WebSocket routes (Twilio Media Streams)
from src.api.websocket_routes import router as ws_router
app.include_router(
    ws_router,
    tags=["WebSocket"]
)


# ─────────────────────────────────────────────────────────────────
# DEVELOPMENT SERVER
# ─────────────────────────────────────────────────────────────────
# This only runs if you execute: python src/main.py
# Normally we use: uvicorn src.main:app --reload

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
    )
