# macOS Setup Instructions for Podcast Generator

## Quick Setup for macOS

### 1. Install Required Dependencies
```bash
# Install macOS-specific TTS dependencies
pip3 install pyobjc-framework-Cocoa pyobjc-framework-AVFoundation pyobjc-framework-Speech

# Install other required packages
pip3 install pyttsx3 numpy google-generativeai PyMuPDF

# Optional: For better audio processing
pip3 install pydub
```

### 2. Replace Audio Generator
Replace your `app/audio_generator.py` with the provided `audio_generator_macos.py`:

```bash
# In your project directory
cp audio_generator_macos.py app/audio_generator.py
```

### 3. Set Your Google API Key
```bash
export GOOGLE_API_KEY="your-google-gemini-api-key-here"
```

### 4. Test the System
```bash
python3 scripts/test_new_pdf_paper_simplified.py
```

## What's Different in macOS Version?

1. **Better macOS TTS Support**: Properly handles macOS voice system
2. **Voice Differentiation**: 
   - host1 = Female voice (higher pitch)
   - host2 = Male voice (lower pitch)
3. **Enhanced Error Handling**: Better fallback when TTS fails
4. **macOS-Specific Optimizations**: Uses macOS native voice system

## Troubleshooting

### If you get "objc module not found":
```bash
pip3 install --upgrade pyobjc-framework-Cocoa pyobjc-framework-AVFoundation
```

### If voices sound the same:
- The macOS version automatically detects available voices
- Check the console output for voice selection messages

### If audio combination fails:
```bash
pip3 install pydub
```

## Testing Voice Differentiation

Run this quick test to verify different voices:
```bash
python3 -c "
import asyncio
import sys
sys.path.append('.')
from app.audio_generator import RealTTSEngine, AudioSegment

async def test():
    engine = RealTTSEngine()
    
    # Test female voice
    seg1 = AudioSegment('Hello, I am the female host', 'host1')
    await engine.synthesize_segment(seg1)
    
    # Test male voice  
    seg2 = AudioSegment('Hello, I am the male host', 'host2')
    await engine.synthesize_segment(seg2)
    
    print('✅ Voice test complete! Check temp/audio/ for different voices')

asyncio.run(test())
"
```

## Expected Output
- host1 should sound female (higher pitch)
- host2 should sound male (lower pitch)
- Both should be clearly different voices

## Support
If you encounter issues, the system will automatically fall back to tone-based audio that still differentiates speakers by frequency.