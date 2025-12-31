<p align="center">
  <img src="assets/banner.png" alt="Voice AI Platform Banner" width="100%">
</p>

# Voice AI Platform

A production-ready AI-powered voice platform for inbound customer service and outbound broadcast calls. Built for the Ghana market.

![Status](https://img.shields.io/badge/Status-In_Development-yellow?style=flat-square)
![Stack](https://img.shields.io/badge/Stack-FastAPI_+_Twilio_+_OpenAI-blue?style=flat-square)
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

- Real-time speech recognition and natural language understanding
- AI-powered response generation with anti-hallucination guardrails
- Automated outbound voice campaigns
- Full call logging and analytics dashboard

---

## Features

✔️ **Inbound Voice Agent** — AI answers customer calls, understands questions, provides accurate responses

✔️ **Outbound Broadcasts** — Send personalized voice messages to customer lists at scale

✔️ **Real-time Processing** — Speech-to-Text → AI → Text-to-Speech pipeline under 1 second

✔️ **RAG Knowledge Base** — Ground responses in client documents to prevent hallucinations

✔️ **Human Escalation** — Seamless transfer to live agents when needed

✔️ **Admin Dashboard** — Manage calls, view analytics, update knowledge base

✔️ **Call Recording** — Encrypted storage with full audit trail

✔️ **Ghana Optimized** — Local phone numbers, optimized for African telecom infrastructure

---

## Tech Stack

| Component      | Technology         | Purpose                    |
| -------------- | ------------------ | -------------------------- |
| Telephony      | Twilio             | Voice calls, Ghana numbers |
| Speech-to-Text | Deepgram Nova-3    | Real-time transcription    |
| LLM            | OpenAI GPT-4o-mini | Response generation        |
| Text-to-Speech | Amazon Polly       | Voice synthesis            |
| Backend        | FastAPI            | Async Python API           |
| Database       | PostgreSQL         | Call logs, analytics       |
| Cache          | Redis              | Session management         |
| Containers     | Docker             | Deployment                 |

---

## Project Structure

```plaintext
voice-ai-platform/
├── src/
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py           # API endpoint handlers
│   └── services/
│       ├── __init__.py
│       ├── stt.py              # Speech-to-Text service
│       ├── llm.py              # Language Model service
│       └── tts.py              # Text-to-Speech service
├── tests/
│   └── __init__.py
├── assets/                     # Banner and images
├── .env.example                # Environment template
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
- Docker & Docker Compose
- Twilio Account (with Ghana number)
- Deepgram API Key
- OpenAI API Key
- AWS Account (for Polly)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/NiiOsa1/voice-ai-platform.git
cd voice-ai-platform

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Run with Docker
docker-compose up --build
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Configuration

All configuration is managed through environment variables. See `.env.example` for the full list.

**Required Variables:**

| Variable                  | Description                  |
| ------------------------- | ---------------------------- |
| `TWILIO_ACCOUNT_SID`    | Twilio account identifier    |
| `TWILIO_AUTH_TOKEN`     | Twilio authentication token  |
| `TWILIO_PHONE_NUMBER`   | Ghana phone number (+233...) |
| `DEEPGRAM_API_KEY`      | Deepgram API key             |
| `OPENAI_API_KEY`        | OpenAI API key               |
| `AWS_ACCESS_KEY_ID`     | AWS access key for Polly     |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key               |
| `DATABASE_URL`          | PostgreSQL connection string |

---

## Usage

### Access Points

| Service      | URL                          |
| ------------ | ---------------------------- |
| API          | http://localhost:8000        |
| API Docs     | http://localhost:8000/docs   |
| Health Check | http://localhost:8000/health |

### Running Tests

```bash
pytest tests/ -v
```

---

## API Endpoints

| Endpoint            | Method | Description                |
| ------------------- | ------ | -------------------------- |
| `/health`         | GET    | Service health check       |
| `/webhook/voice`  | POST   | Twilio voice webhook       |
| `/webhook/status` | POST   | Call status callbacks      |
| `/broadcast`      | POST   | Initiate outbound campaign |
| `/calls`          | GET    | List call history          |
| `/calls/{id}`     | GET    | Get call details           |
| `/knowledge`      | POST   | Update knowledge base      |

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Customer  │────▶│   Twilio    │────▶│  FastAPI    │
│   (Phone)   │◀────│  (Ghana #)  │◀────│  Server     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                    ┌──────────────────────────┼──────────────────────────┐
                    │                          │                          │
                    ▼                          ▼                          ▼
             ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
             │  Deepgram   │           │   OpenAI    │           │   Polly     │
             │    (STT)    │           │   (LLM)     │           │   (TTS)     │
             └─────────────┘           └─────────────┘           └─────────────┘
```

---

## Security

- All API keys stored in environment variables (never in code)
- HTTPS enforced in production
- Call recordings encrypted at rest (AES-256)
- PII redacted from logs
- Role-based access control for admin dashboard
- Webhook signature validation

---

## Deployment

### Docker (Recommended)

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### AWS EC2

See `deploy/` folder for:

- Terraform infrastructure scripts
- NGINX reverse proxy configuration
- SSL certificate setup via Certbot

---

## License

Proprietary — NiiOsa Labs © 2025

---

## Maintainer

**Michael Mensah Ofeor**

🔗 GitHub — [@NiiOsa1](https://github.com/NiiOsa1)

📩 michaelofeor2011@yahoo.com

---

Built for real-world voice automation.
Powered by Twilio, Deepgram, OpenAI, and clean engineering.
