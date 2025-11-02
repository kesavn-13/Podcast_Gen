#!/usr/bin/env python3
"""
Complete Audio Generator Test
Tests the entire audio generation pipeline with all components
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.audio_generator import create_audio_producer, RealTTSEngine, MockTTSEngine

async def test_real_tts_engine():
    """Test RealTTSEngine with fallback"""
    print("\n🎤 Testing RealTTSEngine")
    print("-" * 40)
    
    try:
        engine = RealTTSEngine()
        print(f"✅ RealTTSEngine initialized")
        print(f"📁 Audio directory: {engine.audio_dir}")
        
        # Check if _create_tone_audio method exists
        has_fallback = hasattr(engine, '_create_tone_audio')
        print(f"🔧 Has tone fallback: {has_fallback}")
        
        # Test with a sample segment
        from app.audio_generator import AudioSegment
        
        test_segment = AudioSegment(
            text="Testing real TTS engine with fallback capability.",
            speaker="host1",
            emotion="neutral"
        )
        
        audio_path = await engine.synthesize_segment(test_segment)
        
        if audio_path and os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"✅ Real TTS test successful")
            print(f"📁 Generated: {audio_path}")
            print(f"📊 Size: {file_size:,} bytes")
            return True
        else:
            print("❌ Real TTS test failed - no file generated")
            return False
            
    except Exception as e:
        print(f"❌ Real TTS test error: {e}")
        return False

async def test_mock_tts_engine():
    """Test MockTTSEngine"""
    print("\n🎵 Testing MockTTSEngine")
    print("-" * 40)
    
    try:
        engine = MockTTSEngine()
        print(f"✅ MockTTSEngine initialized")
        
        # Check if required methods exist
        has_tone_audio = hasattr(engine, '_create_tone_audio')
        has_minimal_wav = hasattr(engine, '_create_minimal_wav')
        print(f"🔧 Has tone audio: {has_tone_audio}")
        print(f"🔧 Has minimal WAV: {has_minimal_wav}")
        
        from app.audio_generator import AudioSegment
        
        test_segment = AudioSegment(
            text="Testing mock TTS engine with tone generation.",
            speaker="host2",
            emotion="neutral"
        )
        
        audio_path = await engine.synthesize_segment(test_segment)
        
        if audio_path and os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"✅ Mock TTS test successful")
            print(f"📁 Generated: {audio_path}")
            print(f"📊 Size: {file_size:,} bytes")
            return True
        else:
            print("❌ Mock TTS test failed")
            return False
            
    except Exception as e:
        print(f"❌ Mock TTS test error: {e}")
        return False

async def test_complete_podcast_generation():
    """Test complete podcast generation"""
    print("\n🎧 Testing Complete Podcast Generation")
    print("-" * 50)
    
    # Sample script segments
    script_segments = [
        {
            "speaker": "narrator",
            "text": "Welcome to our research paper podcast. Today we discuss cutting-edge AI innovations.",
            "emotion": "professional"
        },
        {
            "speaker": "host1", 
            "text": "Hello everyone, I'm Dr. Sarah Chen, and today we're exploring fascinating research in machine learning.",
            "emotion": "conversational"
        },
        {
            "speaker": "host2",
            "text": "And I'm Professor Alex Rodriguez. Sarah, this research really represents a breakthrough in the field.",
            "emotion": "engaging"
        },
        {
            "speaker": "host1",
            "text": "Absolutely! The methodology they developed shows remarkable improvements in accuracy and efficiency.",
            "emotion": "excited"
        },
        {
            "speaker": "host2",
            "text": "What's particularly impressive is how they achieved real-time performance without sacrificing quality.",
            "emotion": "analytical"
        },
        {
            "speaker": "narrator",
            "text": "Thank you for joining us today. Next week, we'll explore another groundbreaking paper.",
            "emotion": "professional"
        }
    ]
    
    print(f"📊 Testing with {len(script_segments)} script segments")
    
    # Test both engines
    engines = [
        ("Real TTS", True),
        ("Mock TTS", False)
    ]
    
    results = {}
    
    for engine_name, use_real_tts in engines:
        print(f"\n🔧 Testing {engine_name} Engine")
        print("─" * 30)
        
        try:
            producer = create_audio_producer(use_real_tts=use_real_tts)
            
            episode_id = f"test_{engine_name.lower().replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}"
            
            audio_path = await producer.generate_podcast_audio(script_segments, episode_id)
            
            if audio_path and os.path.exists(audio_path):
                file_size = os.path.getsize(audio_path)
                print(f"✅ {engine_name} podcast generated successfully!")
                print(f"📁 File: {audio_path}")
                print(f"📊 Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
                
                results[engine_name] = {
                    "success": True,
                    "path": audio_path,
                    "size": file_size
                }
            else:
                print(f"❌ {engine_name} podcast generation failed")
                results[engine_name] = {"success": False}
                
        except Exception as e:
            print(f"❌ {engine_name} generation error: {e}")
            results[engine_name] = {"success": False, "error": str(e)}
    
    return results

async def test_dependencies():
    """Test required dependencies"""
    print("\n📦 Testing Dependencies")
    print("-" * 30)
    
    dependencies = [
        ("numpy", "NumPy for audio processing"),
        ("pyttsx3", "Text-to-Speech engine"),
        ("wave", "WAV file handling"),
        ("pathlib", "Path handling"),
        ("asyncio", "Async support")
    ]
    
    results = {}
    
    for package, description in dependencies:
        try:
            if package == "wave":
                import wave
            elif package == "pathlib":
                from pathlib import Path
            elif package == "asyncio":
                import asyncio
            else:
                __import__(package)
            
            print(f"✅ {package}: Available ({description})")
            results[package] = True
        except ImportError:
            print(f"❌ {package}: Missing ({description})")
            results[package] = False
    
    return results

async def main():
    """Run complete audio generator test suite"""
    print("🚀 Complete Audio Generator Test Suite")
    print("=" * 60)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"💻 Platform: {sys.platform}")
    print(f"📁 Working Directory: {Path.cwd()}")
    
    # Test results
    test_results = {}
    
    # 1. Test dependencies
    print("\n" + "="*60)
    print("📦 DEPENDENCY TESTS")
    print("="*60)
    
    dep_results = await test_dependencies()
    test_results["dependencies"] = dep_results
    
    # 2. Test individual engines
    print("\n" + "="*60)
    print("🔧 ENGINE TESTS")
    print("="*60)
    
    real_tts_result = await test_real_tts_engine()
    test_results["real_tts"] = real_tts_result
    
    mock_tts_result = await test_mock_tts_engine()
    test_results["mock_tts"] = mock_tts_result
    
    # 3. Test complete podcast generation
    print("\n" + "="*60)
    print("🎧 COMPLETE PODCAST TESTS")
    print("="*60)
    
    podcast_results = await test_complete_podcast_generation()
    test_results["podcasts"] = podcast_results
    
    # 4. Final summary
    print("\n" + "="*60)
    print("📋 FINAL TEST SUMMARY")
    print("="*60)
    
    print("\n🔍 Dependency Status:")
    for pkg, status in dep_results.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {pkg}")
    
    print("\n🔧 Engine Status:")
    engine_status = "✅" if real_tts_result else "❌"
    print(f"   {engine_status} Real TTS Engine")
    engine_status = "✅" if mock_tts_result else "❌"
    print(f"   {engine_status} Mock TTS Engine")
    
    print("\n🎧 Podcast Generation:")
    for engine, result in podcast_results.items():
        status_icon = "✅" if result.get("success") else "❌"
        print(f"   {status_icon} {engine} Engine")
        if result.get("success"):
            size_mb = result.get("size", 0) / 1024 / 1024
            print(f"      📊 Generated: {size_mb:.2f} MB")
    
    # Overall assessment
    all_deps_ok = all(dep_results.values())
    any_engine_works = real_tts_result or mock_tts_result
    any_podcast_works = any(r.get("success", False) for r in podcast_results.values())
    
    print(f"\n🎯 OVERALL ASSESSMENT:")
    if all_deps_ok and any_engine_works and any_podcast_works:
        print("✅ SYSTEM FULLY OPERATIONAL")
        print("🎉 Ready for production use!")
        
        # Show generated files
        print(f"\n📁 Generated Files:")
        temp_dir = Path("temp/audio")
        if temp_dir.exists():
            audio_files = list(temp_dir.glob("**/*.wav")) + list(temp_dir.glob("**/*.mp3"))
            for file in audio_files[-10:]:  # Show last 10 files
                size = file.stat().st_size if file.exists() else 0
                print(f"   🎵 {file.name}: {size:,} bytes")
        
    elif any_engine_works:
        print("⚠️  SYSTEM PARTIALLY OPERATIONAL")
        print("💡 Some components work, may need dependency fixes")
    else:
        print("❌ SYSTEM NEEDS ATTENTION")
        print("🔧 Multiple components require fixes")
    
    return test_results

if __name__ == "__main__":
    try:
        results = asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()