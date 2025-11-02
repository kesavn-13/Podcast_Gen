#!/usr/bin/env python3
"""
macOS Setup Script for Podcast Generator

This script will install the required dependencies for macOS TTS support.
Run this before using the podcast generator on macOS.
"""

import subprocess
import sys
import platform

def run_command(command):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def install_macos_dependencies():
    """Install macOS-specific dependencies"""
    
    print("🍎 macOS Podcast Generator Setup")
    print("=" * 50)
    
    # Check if we're on macOS
    if platform.system() != 'Darwin':
        print("❌ This script is only for macOS systems")
        return False
    
    # List of required packages for macOS
    macos_packages = [
        "pyobjc-framework-Cocoa",
        "pyobjc-framework-AVFoundation", 
        "pyobjc-framework-Speech",
        "pyttsx3",
        "numpy",
        "wave"
    ]
    
    print("📦 Installing macOS-specific packages...")
    
    for package in macos_packages:
        print(f"   Installing {package}...")
        success, stdout, stderr = run_command(f"pip install {package}")
        
        if success:
            print(f"   ✅ {package} installed successfully")
        else:
            print(f"   ⚠️  {package} installation had issues: {stderr}")
    
    print("\n🧪 Testing TTS functionality...")
    
    # Test TTS
    try:
        import pyttsx3
        import objc
        
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        
        print(f"   ✅ TTS engine initialized")
        print(f"   🎤 Found {len(voices)} voices:")
        
        for i, voice in enumerate(voices[:3]):  # Show first 3 voices
            print(f"      {i}: {voice.name}")
        
        engine.stop()
        print("   ✅ TTS test completed successfully!")
        
    except Exception as e:
        print(f"   ❌ TTS test failed: {e}")
        print("   💡 You may need to run: pip install --upgrade pyobjc-framework-Cocoa")
        return False
    
    print("\n🎉 macOS setup complete!")
    print("You can now run: python3 scripts/test_new_pdf_paper_simplified.py")
    
    return True

if __name__ == "__main__":
    success = install_macos_dependencies()
    sys.exit(0 if success else 1)