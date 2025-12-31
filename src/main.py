"""
Voice AI Platform - Main Application Entry Point.

This is the STARTING POINT of our application.
When you run: uvicorn src.main:app
              └── This tells uvicorn to look for 'app' in src/main.py

WHAT THIS FILE DOES:
1. Creates the FastAPI application
2. Sets up middleware (things that run on EVERY request)
3. Includes routes from other files
4. Provides health check endpoint
"""

# =============================================================================
# IMPORTS
# =============================================================================

# -----------------------------------------------------------------------------
# contextlib.asynccontextmanager - For startup/shutdown events
# -----------------------------------------------------------------------------
# WHAT: Lets us run code when app STARTS and when app STOPS
# WHY: We need to connect to database on startup, disconnect on shutdown
# -----------------------------------------------------------------------------
from contextlib import asynccontextmanager

# -----------------------------------------------------------------------------
# FastAPI imports
# -----------------------------------------------------------------------------
# FastAPI: The main class that creates our application
# Request: Represents an incoming HTTP request
# Response: Represents an outgoing HTTP response
# -----------------------------------------------------------------------------
from fastapi import FastAPI, Request, Response

# -----------------------------------------------------------------------------
# FastAPI middleware
# -----------------------------------------------------------------------------
# CORSMiddleware: Allows other websites/apps to call our API
# CORS = Cross-Origin Resource Sharing
#
# Without CORS: Only YOUR website can call your API
# With CORS: Other websites (like your React frontend) can call it too
# -----------------------------------------------------------------------------
from fastapi.middleware.cors import CORSMiddleware

# -----------------------------------------------------------------------------
# Standard library
# -----------------------------------------------------------------------------
# logging: Python's built-in way to record what's happening
# Better than print() because:
#   - Has levels (DEBUG, INFO, WARNING, ERROR)
#   - Can write to files
#   - Includes timestamps
#   - Can be turned off in production
# -----------------------------------------------------------------------------
import logging
from datetime import datetime

# -----------------------------------------------------------------------------
# Our modules
# -----------------------------------------------------------------------------
# settings: Our configuration from config.py
# -----------------------------------------------------------------------------
from src.config import settings


# =============================================================================
# LOGGING SETUP
# =============================================================================
# This configures HOW log messages appear
#
# %(asctime)s = Timestamp (2025-01-15 10:30:45)
# %(name)s = Logger name
# %(levelname)s = Level (INFO, ERROR, etc.)
# %(message)s = Your actual message
# -----------------------------------------------------------------------------

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create a logger for this file
# __name__ = "src.main" (the module name)
logger = logging.getLogger(__name__)


# =============================================================================
# LIFESPAN (Startup & Shutdown Events)
# =============================================================================
# This function runs:
#   - BEFORE the app starts serving requests (startup)
#   - AFTER the app stops serving requests (shutdown)
#
# @asynccontextmanager makes this work with 'async with' syntax
# The 'yield' separates startup (before) from shutdown (after)
# -----------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handle application startup and shutdown events.
    
    STARTUP (before yield):
        - Connect to databases
        - Load ML models
        - Initialize connections
    
    SHUTDOWN (after yield):
        - Close database connections
        - Clean up resources
        - Save any pending data
    """
    # -------------------------------------------------------------------------
    # STARTUP - Runs when app starts
    # -------------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info(" Starting Voice AI Platform...")
    logger.info(f" Environment: {settings.app_env}")
    logger.info(f" Debug mode: {settings.debug}")
    logger.info("=" * 60)
    
    # TODO: Add database connection here later
    # TODO: Add Redis connection here later
    
    logger.info("Startup complete!")
    
    # -------------------------------------------------------------------------
    # YIELD - App runs and serves requests here
    # -------------------------------------------------------------------------
    yield  # Everything after this runs on SHUTDOWN
    
    # -------------------------------------------------------------------------
    # SHUTDOWN - Runs when app stops
    # -------------------------------------------------------------------------
    logger.info("=" * 60)
    logger.info(" Shutting down Voice AI Platform...")
    
    # TODO: Close database connections here later
    # TODO: Close Redis connections here later
    
    logger.info("Shutdown complete. Goodbye!")
    logger.info("=" * 60)


# =============================================================================
# CREATE THE FASTAPI APPLICATION
# =============================================================================
# This is THE main application object.
# All routes, middleware, and settings attach to this.
# -----------------------------------------------------------------------------

app = FastAPI(
    # Basic info (shows in auto-generated docs)
    title=settings.app_name,
    description="AI-powered voice platform for inbound and outbound calls",
    version="1.0.0",
    
    # Lifespan handler (startup/shutdown)
    lifespan=lifespan,
    
    # API documentation URLs
    # Visit http://localhost:8000/docs to see interactive docs!
    docs_url="/docs",        # Swagger UI
    redoc_url="/redoc",      # ReDoc (alternative docs)
    openapi_url="/openapi.json",  # OpenAPI schema
)


# =============================================================================
# MIDDLEWARE
# =============================================================================
# Middleware = Code that runs on EVERY request, before/after your route
#
# Request → Middleware → Your Route → Middleware → Response
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# CORS Middleware
# -----------------------------------------------------------------------------
# Allows web browsers to call our API from different domains
#
# Without this: Browser blocks requests from other websites
# With this: Browser allows requests from allowed origins
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    # allow_origins: Which websites can call our API?
    # ["*"] = Everyone (for development)
    # In production: ["https://yourdomain.com"]
    allow_origins=["*"],
    
    # allow_credentials: Allow cookies/auth headers?
    allow_credentials=True,
    
    # allow_methods: Which HTTP methods are allowed?
    # ["*"] = All methods (GET, POST, PUT, DELETE, etc.)
    allow_methods=["*"],
    
    # allow_headers: Which headers are allowed?
    # ["*"] = All headers
    allow_headers=["*"],
)


# =============================================================================
# CUSTOM MIDDLEWARE - Request Logging
# =============================================================================
# This logs every request that comes in
# Useful for debugging and monitoring
# -----------------------------------------------------------------------------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Log every incoming request.
    
    HOW THIS WORKS:
    1. Request comes in
    2. This function runs FIRST
    3. We log the request details
    4. call_next(request) passes to actual route
    5. Route returns response
    6. We log the response details
    7. Return response to client
    
    Parameters:
        request: The incoming HTTP request
        call_next: Function to call the actual route handler
    
    Returns:
        Response: The HTTP response
    """
    # Record when request started
    start_time = datetime.now()
    
    # Log incoming request
    logger.info(f"📨 Incoming: {request.method} {request.url.path}")
    
    # Call the actual route and get response
    response: Response = await call_next(request)
    
    # Calculate how long it took
    duration = (datetime.now() - start_time).total_seconds() * 1000  # in ms
    
    # Log the response
    logger.info(
        f"📬 Response: {request.method} {request.url.path} "
        f"- Status: {response.status_code} - Duration: {duration:.2f}ms"
    )
    
    return response


# =============================================================================
# ROUTES (API Endpoints)
# =============================================================================
# Each route is a URL that does something
# @app.get("/path") = When someone visits GET /path, run this function
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Health Check Endpoint
# -----------------------------------------------------------------------------
# WHAT: A simple endpoint that says "I'm alive!"
# WHY: Used by:
#   - Docker to check if container is healthy
#   - Load balancers to know if server is working
#   - Monitoring tools to alert if server is down
#
# GET /health → {"status": "healthy", ...}
# -----------------------------------------------------------------------------
@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns basic info about the application status.
    Used by Docker HEALTHCHECK and monitoring tools.
    
    Returns:
        dict: Health status and app info
    """
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "timestamp": datetime.now().isoformat(),
    }


# -----------------------------------------------------------------------------
# Root Endpoint
# -----------------------------------------------------------------------------
# WHAT: The homepage of our API
# WHY: Friendly message when someone visits the base URL
#
# GET / → {"message": "Welcome to Voice AI Platform", ...}
# -----------------------------------------------------------------------------
@app.get("/")
async def root():
    """
    Root endpoint - API welcome message.
    
    Returns:
        dict: Welcome message and API info
    """
    return {
        "message": "Welcome to Voice AI Platform",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# -----------------------------------------------------------------------------
# Info Endpoint
# -----------------------------------------------------------------------------
# WHAT: Shows configuration info (non-sensitive)
# WHY: Useful for debugging - "which environment am I on?"
#
# GET /info → {"app_name": "...", "environment": "...", ...}
# -----------------------------------------------------------------------------
@app.get("/info")
async def info():
    """
    Application info endpoint.
    
    Returns non-sensitive configuration information.
    NEVER expose API keys or secrets here!
    
    Returns:
        dict: Application configuration (safe to share)
    """
    return {
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "debug": settings.debug,
        "python_version": "3.12",
    }


# =============================================================================
# INCLUDE ROUTERS (Routes from other files)
# =============================================================================
# As the app grows, we split routes into separate files
# Then include them here
#
# Example (we'll add these later):
#   from src.api.routes import router as api_router
#   app.include_router(api_router, prefix="/api/v1")
# -----------------------------------------------------------------------------

# TODO: Add routers here as we build them
from src.api.routes import router as api_router
app.include_router(api_router, prefix="/api/v1", tags=["Voice API"])


# =============================================================================
# RUN DIRECTLY (for development)
# =============================================================================
# This allows running: python src/main.py
# But normally we use: uvicorn src.main:app --reload
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    
    # Run the server
    uvicorn.run(
        "src.main:app",  # Path to app
        host=settings.host,  # 0.0.0.0
        port=settings.port,  # 8000
        reload=settings.is_development,  # Auto-reload on code changes
    )