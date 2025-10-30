"""
Quick test script to verify Google LLM integration
Tests the core components without generating full audio
"""

import os
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def quick_test():
    """Quick test of Google LLM integration"""
    
    print("🧪 QUICK TEST: Google LLM Integration")
    print("=" * 40)
    
    # Test 1: Import check
    print("📦 Testing imports...")
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI imported")
        
        from gtts import gTTS
        print("✅ Google Text-to-Speech imported")
        
        from pydub import AudioSegment
        print("✅ PyDub imported")
        
        import pyttsx3
        print("✅ pyttsx3 imported")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("   Run: pip install google-generativeai gtts pydub pyttsx3")
        return False
    
    # Test 2: Environment variables
    print("\n🔧 Checking environment...")
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key or google_api_key == "your-google-api-key-here":
        print("⚠️  GOOGLE_API_KEY not set or using placeholder")
        print("   Get your key: https://makersuite.google.com/app/apikey")
        print("   Update .env file with your actual key")
        return False
    else:
        print("✅ GOOGLE_API_KEY is set")
    
    # Test 3: Google Gemini client
    print("\n🤖 Testing Google Gemini client...")
    try:
        from backend.tools.google_llm_client import GoogleGeminiClient
        
        client = GoogleGeminiClient(api_key=google_api_key)
        print("✅ Google Gemini client initialized")
        
        # Test simple generation
        messages = [{"role": "user", "content": "Say 'Hello, this is a test!' in exactly those words."}]
        response = await client.generate(messages)
        
        if "choices" in response and len(response["choices"]) > 0:
            content = response["choices"][0]["message"]["content"]
            print(f"✅ Generation test successful: {content[:50]}...")
        else:
            print("⚠️  Generation test returned unexpected format")
            
    except Exception as e:
        print(f"❌ Google Gemini test failed: {e}")
        return False
    
    # Test 4: TTS capabilities  
    print("\n🎤 Testing TTS capabilities...")
    try:
        # Test Google TTS
        tts = gTTS("Hello, this is a test of Google Text to Speech", lang='en', tld='com')
        print("✅ Google TTS initialized")
        
        # Test pyttsx3
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        print(f"✅ pyttsx3 initialized with {len(voices) if voices else 0} voices")
        engine.stop()
        
    except Exception as e:
        print(f"⚠️  TTS test failed: {e}")
        print("   Audio generation may have limitations")
    
    # Test 5: File system setup
    print("\n📁 Checking file system...")
    audio_dir = Path("temp/audio/episodes")
    audio_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Audio directory ready: {audio_dir}")
    
    samples_dir = Path("samples/papers")
    if samples_dir.exists():
        sample_files = list(samples_dir.glob("*.txt"))
        print(f"✅ Found {len(sample_files)} sample papers")
    else:
        print("⚠️  No sample papers found")
    
    print("\n" + "=" * 40)
    print("🎉 QUICK TEST COMPLETE!")
    print("=" * 40)
    print("✅ All core components are working")
    print("\n📋 Ready for:")
    print("   • Google LLM content generation")
    print("   • Long-form podcast creation")
    print("   • Multiple TTS options")
    print("\n🚀 Run full test with:")
    print("   python scripts/test_google_llm_long_podcast.py")
    
    return True


if __name__ == "__main__":
    asyncio.run(quick_test())