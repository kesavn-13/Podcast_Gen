#!/usr/bin/env python3
"""
Quick test for audio generation with fixed script format
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.audio_generator import PodcastAudioProducer


async def test_audio_generation():
    """Test audio generation with proper script format"""
    print("🎵 Testing Audio Generation with Fixed Script Format")
    print("=" * 60)
    
    # Sample script segments in the correct format (list of dialogue lines)
    sample_script_segments = [
        {
            'text': "Welcome to our discussion on LightEndoStereo, a groundbreaking research paper in medical imaging.",
            'speaker': 'host1',
            'emotion': 'neutral'
        },
        {
            'text': "That's right, Sarah. This paper presents a real-time stereo matching method specifically designed for endoscopy images.",
            'speaker': 'host2', 
            'emotion': 'neutral'
        },
        {
            'text': "The key challenge they're addressing is the need for accurate depth perception during minimally invasive surgery.",
            'speaker': 'host1',
            'emotion': 'neutral'
        },
        {
            'text': "Exactly! And they've achieved an impressive 42 frames per second performance while maintaining accuracy.",
            'speaker': 'host2',
            'emotion': 'excited'
        }
    ]
    
    print(f"📊 Testing with {len(sample_script_segments)} dialogue segments")
    for i, segment in enumerate(sample_script_segments, 1):
        print(f"   {i}. {segment['speaker']}: {segment['text'][:50]}...")
    
    # Create audio producer
    print("\n🎤 Initializing audio producer...")
    audio_producer = PodcastAudioProducer(use_coqui_local_tts=True)
    
    # Generate audio
    print("\n🎬 Generating podcast audio...")
    try:
        audio_file = await audio_producer.generate_podcast_audio(
            sample_script_segments,
            episode_id="test_audio_generation"
        )
        
        if audio_file and os.path.exists(audio_file):
            file_size = os.path.getsize(audio_file) / (1024 * 1024)  # MB
            print(f"✅ Audio generation successful!")
            print(f"📁 File: {audio_file}")
            print(f"📊 Size: {file_size:.2f} MB")
            
            # Check if it's a real audio file
            if file_size > 0:
                print(f"🎉 Generated audio file with content!")
            else:
                print(f"⚠️  Audio file is empty")
                
        else:
            print("❌ Audio generation failed - no file created")
            
    except Exception as e:
        print(f"❌ Audio generation error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_audio_generation())