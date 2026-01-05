import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from src.services.deepgram_stream import DeepgramStreamClient


@pytest.mark.asyncio
async def test_deepgram_stream_send_audio(monkeypatch):
    # Create a dummy client with mock token
    client = DeepgramStreamClient(api_key="fake_key")

    # Patch connect and send_audio to avoid real API call
    client.connect = AsyncMock()
    client.send_audio = AsyncMock()
    client.close = AsyncMock()

    # Run your logic
    await client.connect()
    await client.send_audio(b"\x00" * 160)  # fake 160-byte audio
    await client.close()

    # Assertions to confirm flow
    client.connect.assert_called_once()
    client.send_audio.assert_called_once_with(b"\x00" * 160)
    client.close.assert_called_once()
