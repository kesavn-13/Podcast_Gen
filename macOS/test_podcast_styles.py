#!/usr/bin/env python3
"""
Test script for the podcast styles system
Demonstrates how to use different podcast conversation styles
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.audio_generator import RealTTSEngine, AudioSegment

async def test_podcast_styles():
    """Test different podcast styles with sample content"""
    
    # Sample research content
    sample_content = [
        "Researchers have developed a new neural network architecture that achieves unprecedented accuracy on language understanding tasks.",
        "The breakthrough comes from a novel attention mechanism that processes information 10 times more efficiently than previous methods.",
        "However, the model requires significant computational resources and the training process is quite complex.",
        "The implications for natural language processing are substantial, potentially revolutionizing how we build AI systems."
    ]
    
    print("🎙️ Testing Podcast Styles System\n")
    
    # List available styles
    styles = RealTTSEngine.list_available_styles()
    print("Available Podcast Styles:")
    for style_id, description in styles.items():
        print(f"  • {style_id}: {description}")
    print()
    
    # Test each style
    for style_name in ["friendly_chat", "tech_interview", "academic_discussion"]:
        print(f"🎭 Testing Style: {style_name}")
        print("=" * 50)
        
        try:
            # Create audio generator with style
            audio_gen = RealTTSEngine.with_style(style_name)
            
            # Show style info
            style_info = audio_gen.get_current_style_info()
            print(f"Style: {style_info['name']}")
            print(f"Description: {style_info['description']}")
            print(f"Use Case: {style_info['use_case']}")
            print()
            
            # Process content with style
            audio_segments = audio_gen.process_content_with_style(sample_content[:2])  # Use first 2 segments for demo
            
            print(f"Generated {len(audio_segments)} conversational segments:")
            for i, segment in enumerate(audio_segments):
                speaker_info = f"{segment.speaker}"
                if hasattr(segment, 'interaction_type'):
                    speaker_info += f" ({segment.interaction_type})"
                
                print(f"  {i+1}. {speaker_info}: {segment.text[:100]}...")
                
                # Optionally synthesize the first segment
                if i == 0:
                    print(f"     🎤 Synthesizing sample...")
                    try:
                        audio_path = await audio_gen.synthesize_segment(segment)
                        print(f"     ✅ Audio saved to: {audio_path}")
                    except Exception as e:
                        print(f"     ❌ Synthesis failed: {e}")
            
            print()
            
        except Exception as e:
            print(f"❌ Error testing style '{style_name}': {e}")
            print()
    
    print("🎉 Podcast styles testing complete!")

def demo_style_usage():
    """Demonstrate basic usage patterns"""
    print("📝 Usage Examples:\n")
    
    print("1. Create audio generator with specific style:")
    print("   audio_gen = RealTTSEngine.with_style('friendly_chat')")
    print()
    
    print("2. List available styles:")
    print("   styles = RealTTSEngine.list_available_styles()")
    print()
    
    print("3. Process content with conversation flow:")
    print("   segments = audio_gen.process_content_with_style(content_list)")
    print()
    
    print("4. Get style information:")
    print("   info = audio_gen.get_current_style_info()")
    print()

if __name__ == "__main__":
    print("🎙️ Podcast Styles Demo\n")
    
    # Show usage examples
    demo_style_usage()
    
    # Run async test
    try:
        asyncio.run(test_podcast_styles())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
