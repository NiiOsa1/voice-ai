# =============================================================================
# VOICE AI PLATFORM - DOCKERFILE
# =============================================================================

# Step 1: Start with Python 3.11 (slim = smaller size)
FROM python:3.11-slim

# Step 2: Metadata (who made this, version info)
LABEL maintainer="Michael Mensah Ofeor <michaelofeor2011@yahoo.com>"
LABEL version="1.0.0"
LABEL description="Voice AI Platform for inbound/outbound calls"

# Step 3: Settings for Python inside container
#   PYTHONDONTWRITEBYTECODE=1  → Don't create .pyc files (saves space)
#   PYTHONUNBUFFERED=1         → Show print() output immediately (for logs)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Step 4: Create and enter the /app folder
WORKDIR /app

# Step 5: Install system tools we need
#   gcc        → C compiler (some Python packages need it)
#   libpq-dev  → PostgreSQL connector
#   curl       → For health checks
#   ffmpeg     → Audio processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Step 6: Copy requirements first (for faster rebuilds - Docker caches this)
COPY requirements.txt .

# Step 7: Install Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Step 8: Copy all project code into container
COPY . .

# Step 9: Create non-root user (security best practice)
#   Running as root inside container = dangerous
#   If hacker breaks in, they'd have full access!
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app

# Step 10: Switch to the safe user
USER appuser

# Step 11: Document which port we use (8000)
EXPOSE 8000

# Step 12: Health check - Docker pings this every 30 seconds
#   If it fails 3 times, container marked "unhealthy"
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Step 13: The command that runs when container starts
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]