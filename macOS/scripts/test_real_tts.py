"""
Test Real Text-to-Speech Generation
This will create actual spoken audio from text
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.audio_generator import CoquiLocalTTSEngine, AudioSegment, create_audio_producer

async def test_real_tts():
    """Test real text-to-speech functionality"""
    print("🎤 Testing Real Text-to-Speech...")
    
    # Create real TTS engine
    tts_engine = CoquiLocalTTSEngine()
    
    # Test segments with actual conversation content
    test_segments = [
        AudioSegment(
            text="Welcome to Paper to Podcast! I'm Dr. Sarah Chen, and today we're exploring fascinating research in artificial intelligence.",
            speaker="host1"
        ),
        AudioSegment(
            text="Hi everyone, I'm Professor Mike Rodriguez. Sarah, this paper we're discussing really challenges conventional thinking about neural networks, doesn't it?",
            speaker="host2"
        ),
        AudioSegment(
            text="Absolutely, Mike! The authors demonstrate that attention mechanisms can completely replace traditional recurrence and convolution in sequence modeling.",
            speaker="host1"
        ),
        AudioSegment(
            text="What's particularly impressive is the efficiency gains. They achieved state-of-the-art results while being significantly more parallelizable.",
            speaker="host2"
        ),
        AudioSegment(
            text="Thanks for listening to Paper to Podcast, where we bring cutting-edge research to life through engaging conversations.",
            speaker="narrator"
        )
    ]
    
    print(f"\n🎬 Generating {len(test_segments)} real speech segments...")
    
    generated_files = []
    for i, segment in enumerate(test_segments):
        print(f"\n{i+1}. Generating {segment.speaker}: {segment.text[:60]}...")
        
        audio_path = await tts_engine.synthesize_segment(segment)
        if audio_path and Path(audio_path).exists():
            file_size = Path(audio_path).stat().st_size
            generated_files.append(audio_path)
            print(f"   ✅ Generated: {Path(audio_path).name}")
            print(f"   📏 Size: {file_size} bytes")
            print(f"   ⏱️  Duration: {segment.duration:.1f}s")
            print(f"   🎧 Text: '{segment.text[:50]}...'")
        else:
            print(f"   ❌ Generation failed")
    
    print(f"\n🎉 Real TTS Generation Complete!")
    print(f"✅ Generated {len(generated_files)} speech files")
    
    # Test playback
    if generated_files:
        print(f"\n🎧 Test playback of first file:")
        print(f"   {generated_files[0]}")
        
        # Try to play the first file
        try:
            import subprocess
            subprocess.Popen(["start", generated_files[0]], shell=True)
            print("   🔊 Opened in default audio player")
        except:
            print("   🎵 File ready for manual playback")
    
    return generated_files

async def test_full_podcast_generation():
    """Test complete podcast generation with real TTS"""
    print("\n\n🎬 Testing Complete Podcast Generation...")
    
    # Create podcast script
    script_segments = [
        {
            "speaker": "narrator",
            "text": "Welcome to Paper to Podcast, episode 42.",
        },
        {
            "speaker": "host1", 
            "text": "Hi, I'm Dr. Sarah Chen. Today we're diving into transformer architecture.",
        },
        {
            "speaker": "host2",
            "text": "And I'm Professor Mike Rodriguez. This paper really changed everything, didn't it Sarah?",
        },
        {
            "speaker": "host1",
            "text": "Absolutely! The key insight is that attention is all you need for sequence modeling.",
        },
        {
            "speaker": "host2",
            "text": "The results speak for themselves. State-of-the-art performance with better parallelization.",
        },
        {
            "speaker": "narrator",
            "text": "Thanks for listening to Paper to Podcast. Subscribe for more research discussions.",
        }
    ]
    
    # Generate complete podcast with Coqui Local TTS
    producer = create_audio_producer(use_coqui_local_tts=True)
    
    print(f"🎙️ Generating complete podcast episode...")
    episode_path = await producer.generate_podcast_audio(script_segments, "real_tts_demo")
    
    if episode_path and Path(episode_path).exists():
        file_size = Path(episode_path).stat().st_size
        print(f"✅ Complete podcast generated!")
        print(f"   📁 File: {episode_path}")
        print(f"   📏 Size: {file_size} bytes")
        print(f"   🎧 Ready for playback!")
        
        return episode_path
    else:
        print(f"❌ Complete podcast generation failed")
        return None

async def main():
    """Main test function"""
    try:
        # Test individual TTS segments
        individual_files = await test_real_tts()
        
        # Test complete podcast generation
        episode_file = await test_full_podcast_generation()
        
        print(f"\n🏆 FINAL RESULTS:")
        print(f"   🎤 Individual speech files: {len(individual_files)}")
        print(f"   🎬 Complete episode: {'✅' if episode_file else '❌'}")
        
        if episode_file:
            print(f"\n🎉 SUCCESS! You now have real speech-based podcast audio!")
            print(f"🎧 Play: {episode_file}")
        
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())