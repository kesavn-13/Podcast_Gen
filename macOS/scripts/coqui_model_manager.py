#!/usr/bin/env python3
"""
Quick script to list available Coqui TTS models and test different voices.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

def list_models():
    """List some recommended Coqui TTS models"""
    print("🎤 Recommended Coqui Local TTS Models")
    print("=" * 70)
    print()
    
    models = {
        "🌟 BEST FOR NATURALNESS (Single Speaker)": [
            {
                "model": "tts_models/en/ljspeech/tacotron2-DDC",
                "quality": "⭐⭐⭐⭐⭐",
                "speed": "Fast",
                "voice": "Female (very natural)",
                "use_case": "Explainers, tutorials, professional narration"
            },
            {
                "model": "tts_models/en/ljspeech/glow-tts",
                "quality": "⭐⭐⭐⭐",
                "speed": "Very Fast",
                "voice": "Female (natural)",
                "use_case": "Quick generation, good quality"
            },
            {
                "model": "tts_models/en/jenny/jenny",
                "quality": "⭐⭐⭐⭐⭐",
                "speed": "Medium",
                "voice": "Female (professional)",
                "use_case": "Audiobooks, professional content"
            }
        ],
        "🎭 BEST FOR MULTIPLE SPEAKERS": [
            {
                "model": "tts_models/en/vctk/vits",
                "quality": "⭐⭐⭐",
                "speed": "Medium",
                "voice": "109 speakers (male/female)",
                "use_case": "Dialogue, debates, interviews",
                "note": "Use with speakers: p225 (F), p226 (M), p227 (M), p228 (F)"
            }
        ]
    }
    
    for category, model_list in models.items():
        print(f"\n{category}")
        print("-" * 70)
        for model_info in model_list:
            print(f"\n  Model: {model_info['model']}")
            print(f"  Quality: {model_info['quality']}")
            print(f"  Speed: {model_info['speed']}")
            print(f"  Voice: {model_info['voice']}")
            print(f"  Use Case: {model_info['use_case']}")
            if 'note' in model_info:
                print(f"  Note: {model_info['note']}")
    
    print("\n" + "=" * 70)
    print("\n💡 To use a model, add to your .env file:")
    print("   COQUI_LOCAL_MODEL=tts_models/en/ljspeech/tacotron2-DDC")
    print()
    print("   For multi-speaker models, also set:")
    print("   COQUI_LOCAL_SPEAKER_HOST1=p225")
    print("   COQUI_LOCAL_SPEAKER_HOST2=p226")
    print("   COQUI_LOCAL_SPEAKER_NARRATOR=p227")
    print()

def test_model():
    """Quick test of the configured model"""
    print("\n🧪 Testing current model configuration...")
    print("=" * 70)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    model = os.getenv('COQUI_LOCAL_MODEL', 'tts_models/en/ljspeech/tacotron2-DDC')
    print(f"\n📦 Current model: {model}")
    
    try:
        from TTS.api import TTS
        print(f"🔄 Loading model (this may take a minute on first use)...")
        tts = TTS(model_name=model, progress_bar=True, gpu=False)
        
        is_multi = hasattr(tts, 'speakers') and tts.speakers is not None
        
        if is_multi:
            print(f"✅ Multi-speaker model loaded successfully!")
            print(f"👥 Available speakers ({len(tts.speakers)}): {tts.speakers[:10]}...")
        else:
            print(f"✅ Single-speaker model loaded successfully!")
            print(f"🎤 This model uses one high-quality voice for all speakers")
        
        # Quick test synthesis
        output_path = Path("temp/audio/test") / "model_test.wav"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"\n🎵 Generating test audio...")
        test_text = "Hello! This is a test of the text to speech system."
        
        if is_multi and tts.speakers:
            # Use first speaker for multi-speaker
            speaker = tts.speakers[0]
            tts.tts_to_file(text=test_text, speaker=speaker, file_path=str(output_path))
            print(f"✅ Test audio generated with speaker '{speaker}'")
        else:
            tts.tts_to_file(text=test_text, file_path=str(output_path))
            print(f"✅ Test audio generated")
        
        print(f"📁 Saved to: {output_path}")
        print(f"\n🎧 Listen with: open {output_path}")
        
    except Exception as e:
        print(f"❌ Error testing model: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Coqui TTS Model Manager')
    parser.add_argument('--list', action='store_true', help='List recommended models')
    parser.add_argument('--test', action='store_true', help='Test current model configuration')
    
    args = parser.parse_args()
    
    if args.test:
        test_model()
    elif args.list or not (args.list or args.test):
        # Default to list if no args
        list_models()
