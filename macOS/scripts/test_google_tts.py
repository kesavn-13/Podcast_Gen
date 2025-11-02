#!/usr/bin/env python3
"""
Deprecated: Google/gTTS test has been replaced by Coqui Local TTS.
This script now runs the Coqui Local TTS test.
"""
import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.audio_generator import create_audio_producer


async def test_google_tts():
    """Redirected to Coqui Local TTS test."""
    from scripts.test_coqui_local_tts import test_coqui_local_tts
    return await test_coqui_local_tts()


if __name__ == "__main__":
    print()
    result = asyncio.run(test_google_tts())
    print()
    sys.exit(0 if result else 1)
