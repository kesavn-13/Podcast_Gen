#!/usr/bin/env python3
"""
Quick test script for local Coqui TTS (coqui-ai/TTS).
Generates three short segments with different speakers using VCTK speakers.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.audio_generator import create_audio_producer


async def test_coqui_local_tts():
    print("🧪 Testing Coqui Local TTS (coqui-ai/TTS)")
    print("=" * 60)

    # Set env to select local Coqui (respects .env settings)
    os.environ["USE_COQUI_LOCAL_TTS"] = "true"
    os.environ["USE_COQUI_TTS"] = "false"

    # Model and speakers will use .env defaults (don't override)
    # If you want to test specific settings, set them in .env instead

    test_segments = [
        {"speaker": "host1", "text": "Hello, this is host one using local Coqui T T S.", "emotion": "neutral"},
        {"speaker": "host2", "text": "And I am host two. This runs locally without any billing.", "emotion": "neutral"},
        {"speaker": "narrator", "text": "Finally, the narrator voice should also sound natural.", "emotion": "professional"},
    ]

    try:
        print("🎤 Initializing Coqui Local TTS engine...")
        producer = create_audio_producer(use_coqui_local_tts=True)
        print()

        print("🎵 Generating test audio segments...")
        output_path = await producer.generate_podcast_audio(test_segments, episode_id="coqui_local_tts_test")

        if output_path and Path(output_path).exists():
            size = Path(output_path).stat().st_size
            print("\n============================================================")
            print("✅ SUCCESS! Coqui Local TTS test passed")
            print(f"📁 Generated file: {output_path}")
            print(f"📊 File size: {size:,} bytes")
            print("\n🎧 Listen to the file to verify:")
            print(f"   open {output_path}")
            return True
        else:
            print("❌ Coqui local test failed: No output file generated")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


if __name__ == "__main__":
    ok = asyncio.run(test_coqui_local_tts())
    sys.exit(0 if ok else 1)
