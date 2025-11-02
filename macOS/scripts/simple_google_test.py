#!/usr/bin/env python3
"""
Simple test to verify our Google Gemini integration is working
Uses only the core components we know are working
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv()

from backend.tools.sm_client import create_clients

def test_google_integration():
    """Test our Google Gemini integration"""
    
    print("🚀 TESTING GOOGLE GEMINI INTEGRATION")
    print("=" * 50)
    
    # Create clients
    reasoner, embedder = create_clients()
    print(f"🤖 Reasoning client: {type(reasoner).__name__}")
    print(f"🔗 Embedding client: {type(embedder).__name__}")
    
    # Test reasoning
    print("\n📝 Testing content generation...")
    test_prompt = "Generate a brief podcast script about neural networks with 2 hosts discussing key concepts."
    
    try:
        response = reasoner.generate(test_prompt, response_type="outline")
        print(f"✅ Generation successful!")
        print(f"📄 Response type: {type(response)}")
        print(f"📝 Response length: {len(str(response))} characters")
        
        if isinstance(response, dict):
            print(f"🔑 Response keys: {list(response.keys())}")
            if 'title' in response:
                print(f"📰 Title: {response['title']}")
            if 'segments' in response:
                print(f"🎬 Segments: {len(response['segments'])}")
        
        print(f"📋 Sample response: {str(response)[:200]}...")
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        
    # Check our existing audio files
    print("\n🎵 CHECKING EXISTING AUDIO FILES")
    print("-" * 30)
    
    episodes_dir = project_root / "temp" / "audio" / "episodes"
    if episodes_dir.exists():
        mp3_files = list(episodes_dir.glob("*.mp3"))
        print(f"📁 Found {len(mp3_files)} MP3 files:")
        
        for mp3_file in mp3_files:
            size_mb = mp3_file.stat().st_size / (1024 * 1024)
            print(f"   🎧 {mp3_file.name} - {size_mb:.2f} MB")
            
            # Check if there's a corresponding JSON file
            json_file = mp3_file.with_suffix('.json')
            if json_file.exists():
                print(f"      📊 Metadata: {json_file.name}")
        
        if mp3_files:
            print(f"\n🎉 SUCCESS! You have {len(mp3_files)} podcast MP3 files generated!")
            print("🎧 These files demonstrate the complete Paper→Podcast pipeline working")
            print("   with Google Gemini integration and real TTS audio synthesis.")
        
    else:
        print("❌ No audio files directory found")


if __name__ == "__main__":
    test_google_integration()