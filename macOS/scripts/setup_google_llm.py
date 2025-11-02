"""
Setup script for Google LLM + Long Podcast generation
Installs required dependencies and sets up environment
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"   stdout: {e.stdout}")
        if e.stderr:
            print(f"   stderr: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported")
        print("   Please upgrade to Python 3.8 or higher")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def setup_google_llm_environment():
    """Set up environment for Google LLM + Long Podcast generation"""
    
    print("🚀 SETTING UP GOOGLE LLM + LONG PODCAST ENVIRONMENT")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return False
    
    # Install core dependencies
    packages = [
        "google-generativeai",
        "google-ai-generativelanguage",
        "TTS",
        "pydub",
        "fastapi",
        "uvicorn[standard]",
        "pydantic",
        "pydantic-settings",
        "requests",
        "aiohttp",
        "pathlib",
        "python-dotenv"
    ]
    
    print(f"📦 Installing {len(packages)} packages...")
    for package in packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            print(f"⚠️  Failed to install {package}, continuing...")
    
    # Check if ffmpeg is available (required for pydub)
    print("🎵 Checking for ffmpeg (required for audio processing)...")
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ ffmpeg is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  ffmpeg not found - audio processing may have limitations")
        print("   Install ffmpeg:")
        print("   - Windows: Download from https://ffmpeg.org/download.html")
        print("   - macOS: brew install ffmpeg")
        print("   - Ubuntu: sudo apt install ffmpeg")
    
    # Create .env file template
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file template...")
        env_content = """# Google Gemini API Configuration
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_MODEL=gemini-1.5-pro
GOOGLE_EMBEDDING_MODEL=models/embedding-001

# Audio Settings
    # Coqui-only TTS
    # USE_COQUI_LOCAL_TTS=true
AUDIO_LANGUAGE=en

# Episode Settings
SEGMENTS_PER_EPISODE=8
WORDS_PER_SEGMENT=200
MAX_TOTAL_DURATION=1800

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created .env file template")
    else:
        print("✅ .env file already exists")
    
    # Test imports
    print("🧪 Testing imports...")
    test_imports = [
        ("google.generativeai", "Google Generative AI"),
        ("TTS.api", "Coqui TTS"),
        ("pydub", "PyDub audio processing"),
        ("fastapi", "FastAPI"),
        ("pydantic", "Pydantic")
    ]
    
    all_imports_ok = True
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✅ {name} import successful")
        except ImportError as e:
            print(f"❌ {name} import failed: {e}")
            all_imports_ok = False
    
    # Coqui TTS quick check
    try:
        from TTS.api import TTS as CoquiTTS
        print("✅ Coqui TTS import successful")
    except Exception as e:
        print(f"⚠️  Coqui TTS import failed: {e}")
    
    print("\n" + "=" * 60)
    print("🏁 SETUP COMPLETE!")
    print("=" * 60)
    
    if all_imports_ok:
        print("✅ All core dependencies installed successfully")
        print("\n📋 Next Steps:")
        print("1. Get your Google API key:")
        print("   https://makersuite.google.com/app/apikey")
        print("\n2. Update your .env file:")
        print("   GOOGLE_API_KEY=your-actual-api-key")
        print("\n3. Test the system:")
        print("   python scripts/test_google_llm_long_podcast.py")
        print("\n4. Start creating long-form podcasts! 🎉")
    else:
        print("⚠️  Some dependencies failed to install")
        print("   Please check the error messages above")
        print("   You may need to install packages manually")
    
    return all_imports_ok


if __name__ == "__main__":
    setup_google_llm_environment()