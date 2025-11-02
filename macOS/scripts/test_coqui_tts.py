#!/usr/bin/env python3
"""
Quick test script for Coqui Studio TTS API integration.
Generates three short segments with different speakers.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.audio_generator import create_audio_producer


async def test_coqui_tts():
    print("🧪 Testing Coqui TTS Integration")
    print("=" * 60)

    api_key = os.getenv("COQUI_API_KEY")
    if not api_key:
        print("⚠️  COQUI_API_KEY not set")
        print("   Get an API key from https://coqui.ai/ and set:")
        print("   export COQUI_API_KEY='your_api_key'")
        return False

    # Optional: per-speaker voice IDs (recommended)
    print("🔧 Voice ID env (optional, recommended):")
    print(f"   COQUI_VOICE_HOST1: {os.getenv('COQUI_VOICE_HOST1') or '[unset]'}")
    print(f"   COQUI_VOICE_HOST2: {os.getenv('COQUI_VOICE_HOST2') or '[unset]'}")
    print(f"   COQUI_VOICE_NARRATOR: {os.getenv('COQUI_VOICE_NARRATOR') or '[unset]'}")
    print()

    test_segments = [
        {"speaker": "host1", "text": "Hello, this is host one with a natural Coqui voice.", "emotion": "neutral"},
        {"speaker": "host2", "text": "And I am host two. We are testing Coqui Studio API.", "emotion": "neutral"},
        {"speaker": "narrator", "text": "This narrator line should also sound natural and clear.", "emotion": "professional"},
    ]

    # Use Coqui engine via env flag
    os.environ["USE_COQUI_TTS"] = "true"

    try:
        print("🎤 Initializing Coqui TTS engine...")
        producer = create_audio_producer(use_coqui_tts=True)
        print()

        print("🎵 Generating test audio segments...")
        output_path = await producer.generate_podcast_audio(test_segments, episode_id="coqui_tts_test")

        if output_path and Path(output_path).exists():
            size = Path(output_path).stat().st_size
            print("\n============================================================")
            print("✅ SUCCESS! Coqui TTS test passed")
            print(f"📁 Generated file: {output_path}")
            print(f"📊 File size: {size:,} bytes")
            print("\n🎧 Listen to the file to verify:")
            print(f"   open {output_path}")
            return True
        else:
            print("❌ Coqui test failed: No output file generated")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


if __name__ == "__main__":
    ok = asyncio.run(test_coqui_tts())
    sys.exit(0 if ok else 1)
