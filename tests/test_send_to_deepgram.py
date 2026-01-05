import sys
import os
import asyncio

# Fix Python path so it can find the src module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.deepgram_stream import DeepgramStreamClient
from src.config import settings


async def main():
    audio_path = "test-mulaw.raw"

    if not os.path.exists(audio_path):
        print(f"❌ File not found: {audio_path}")
        return

    print(f"📤 Sending audio file to Deepgram: {audio_path}")

    # Callback for final transcript
    async def on_final(transcript):
        print(f"✅ Final transcript: {transcript}")

    # Callback for partial transcript
    async def on_partial(transcript):
        print(f"🟡 Partial transcript: {transcript}")

    deepgram = DeepgramStreamClient(api_key=settings.deepgram_api_key)
    await deepgram.connect(on_partial=on_partial, on_final=on_final)

    # Load and send audio
    with open(audio_path, "rb") as f:
        while chunk := f.read(160):
            await deepgram.send_audio(chunk)
            await asyncio.sleep(0.02)  # Mimic real-time stream (~50 packets/sec)

    await deepgram.close()
    print("🎤 Finished sending test audio.")


if __name__ == "__main__":
    asyncio.run(main())
