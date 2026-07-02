<p align="center">
  <img src="assets/banner.png" alt="Voice AI Platform Banner" width="100%">
</p>

# Voice AI Platform

A production-ready AI-powered voice platform for inbound customer service and outbound broadcast calls. Built for the Ghana market with ultra-low latency.

![Status](https://img.shields.io/badge/Status-Production_Ready-green?style=flat-square)
![Stack](https://img.shields.io/badge/Stack-FastAPI_+_Twilio_+_Groq-blue?style=flat-square)
![License](https://img.shields.io/badge/License-Proprietary-red?style=flat-square)

[![Python](https://img.shields.io/badge/Python-3.11+-green?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://docker.com)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Architecture](#architecture)
- [Security](#security)
- [Deployment](#deployment)
- [License](#license)
- [Maintainer](#maintainer)

---

## Overview

This platform provides enterprise-grade voice AI capabilities for businesses in Ghana and across Africa. It handles both inbound customer inquiries and outbound voice broadcasts with sub-second response times.

**Key Capabilities:**

- Real-time speech recognition with Deepgram Nova-2
- Ultra-fast AI responses with Groq LPU (10x faster than OpenAI)
- Natural voice synthesis with ElevenLabs
- Full call logging and analytics

---

## Features

✔️ **Inbound Voice Agent** — AI answers customer calls, understands questions, provides accurate responses

✔️ **Real-time Processing** — Speech-to-Text → AI → Text-to-Speech pipeline under 1 second

✔️ **Barge-in Support** — User can interrupt AI mid-speech for natural conversation

✔️ **Context Awareness** — Remembers conversation history for coherent dialogue

✔️ **Ghana Optimized** — Local phone numbers, optimized for African telecom infrastructure

✔️ **Auto Reconnect** — Handles network issues gracefully with Deepgram KeepAlive

---

## Tech Stack

| Component      | Technology                | Purpose                      |
| -------------- | ------------------------- | ---------------------------- |
| Telephony      | Twilio Media Streams      | Voice calls, WebSocket audio |
| Speech-to-Text | Deepgram Nova-2 Phonecall | Real-time transcription      |
| LLM            | Groq (llama-3.1-8b)       | Ultra-fast response (~200ms) |
| Text-to-Speech | ElevenLabs Flash v2.5     | Natural voice (~75ms)        |
| Backend        | FastAPI                   | Async Python API             |
| Audio Format   | mulaw 8kHz                | Twilio-native format         |

### Why This Stack?

| Component   | Choice      | Why                                         |
| ----------- | ----------- | ------------------------------------------- |
| STT         | Deepgram    | 6.84% WER, fastest real-time STT            |
| LLM         | Groq        | 10x faster than OpenAI, custom LPU hardware |
| TTS         | ElevenLabs  | Most natural voices, 75ms latency           |
| Telephony   | Twilio      | Industry standard, Ghana numbers available  |

---

## Project Structure
```plaintext
voice-ai-platform/
├── src/
│   ├── main.py                     # Application entry point
│   ├── config.py                   # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py               # HTTP webhook handlers
│   │   ├── websocket_routes.py     # WebSocket endpoint
│   │   └── websocket_handler.py    # Call handling logic
│   └── services/
│       ├── __init__.py
│       ├── deepgram_stream.py      # Speech-to-Text (streaming)
│       ├── llm_groq.py             # Language Model (Groq)
│       └── tts_elevenlabs.py       # Text-to-Speech (ElevenLabs)
├── tests/
│   ├── test_deepgram_stream.py
│   └── test_send_to_deepgram.py
├── assets/                         # Banner and images
├── .env.example                    # Environment template
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.11+
- Twilio Account (with phone number)
- Deepgram API Key
- Groq API Key
- ElevenLabs API Key

### Quick Start
```bash
# Clone the repository
git clone https://github.com/NiiOsa1/voice-ai.git
cd voice-ai

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### With Docker
```bash
docker-compose up --build
```

---

## Configuration

All configuration is managed through environment variables. See `.env.example` for the full list.

**Required Variables:**

| Variable                | Description                    |
| ----------------------- | ------------------------------ |
| `TWILIO_ACCOUNT_SID`    | Twilio account identifier      |
| `TWILIO_AUTH_TOKEN`     | Twilio authentication token    |
| `TWILIO_PHONE_NUMBER`   | Your Twilio phone number       |
| `DEEPGRAM_API_KEY`      | Deepgram API key               |
| `GROQ_API_KEY`          | Groq API key                   |
| `GROQ_MODEL`            | Model name (openai/gpt-oss-20b) |
| `ELEVENLABS_API_KEY`    | ElevenLabs API key             |
| `NGROK_WSS_URL`         | WebSocket URL for Twilio       |

---

## Usage

### Access Points

| Service      | URL                          |
| ------------ | ---------------------------- |
| API          | http://localhost:8000        |
| API Docs     | http://localhost:8000/docs   |
| Health Check | http://localhost:8000/health |

### Testing a Call

1. Start ngrok: `ngrok http 8000`
2. Update `.env` with ngrok URL
3. Configure Twilio webhook to `https://your-ngrok-url/api/v1/calls/inbound`
4. Call your Twilio number

---

## API Endpoints

| Endpoint                    | Method | Description              |
| --------------------------- | ------ | ------------------------ |
| `/`                         | GET    | API info                 |
| `/health`                   | GET    | Health check             |
| `/api/v1/test`              | GET    | Service status           |
| `/api/v1/calls/inbound`     | POST   | Twilio inbound webhook   |
| `/api/v1/calls/outbound`    | POST   | Twilio outbound webhook  |
| `/api/v1/calls/status`      | POST   | Call status callbacks    |
| `/ws/twilio-media-stream`   | WS     | Audio streaming endpoint |

---

## Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Customer  │────▶│   Twilio    │────▶│  FastAPI    │
│   (Phone)   │◀────│  (WebSocket)│◀────│  Server     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
             ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
             │  Deepgram   │           │    Groq     │           │ ElevenLabs  │
             │ Nova-2 STT  │           │   LLM       │           │  Flash TTS  │
             │  (~100ms)   │           │  (~200ms)   │           │  (~75ms)    │
             └─────────────┘           └─────────────┘           └─────────────┘
```

### Audio Flow
```
User speaks → Twilio → WebSocket → Deepgram (STT)
                                        ↓
                                   Transcript
                                        ↓
                                   Groq (LLM)
                                        ↓
                                   Response text
                                        ↓
                                   ElevenLabs (TTS)
                                        ↓
User hears  ← Twilio ← WebSocket ← Audio (mulaw)
```

---

## Security

- All API keys stored in environment variables (never in code)
- `.env` file excluded from git
- HTTPS enforced via ngrok/Render
- Webhook signature validation ready

---

## Deployment

### Render (Recommended)

1. Push to GitHub
2. Connect Render to repo
3. Set environment variables
4. Deploy

### Docker
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## Performance

| Metric              | Target    | Achieved  |
| ------------------- | --------- | --------- |
| STT Latency         | <300ms    | ~100ms    |
| LLM Latency         | <500ms    | ~200ms    |
| TTS Latency         | <200ms    | ~75ms     |
| Total Response Time | <1000ms   | ~500ms*   |

*When deployed on US servers (Render/AWS)

---

## License

Proprietary — NiiOsa Labs © 2025

---

## Maintainer

**Michael Mensah Ofeor**

🔗 GitHub — [@NiiOsa1](https://github.com/NiiOsa1)

📩 michaelofeor2011@yahoo.com

---

Built for real-world voice automation in Africa.
Powered by Twilio, Deepgram, Groq, and ElevenLabs.
