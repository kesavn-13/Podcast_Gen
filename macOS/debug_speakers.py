#!/usr/bin/env python3
"""
Debug script to test speaker assignment in conversation styles
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.styles import TextProcessor

def test_speaker_assignment():
    """Test speaker assignment with sample content"""
    
    print("🔍 Testing Speaker Assignment")
    print("=" * 50)
    
    # Sample content segments
    test_content = [
        "The neural network architecture uses a novel attention mechanism for stereo matching.",
        "Experimental results show a 15% improvement in accuracy compared to previous methods.",
        "The algorithm processes endoscopic images in real-time at 42 FPS.",
        "Clinical applications include minimally invasive surgery and depth perception."
    ]
    
    # Test tech_interview style
    processor = TextProcessor("tech_interview")
    
    print("📝 Processing content with tech_interview style:")
    print()
    
    all_interactions = processor.process_full_content(test_content)
    
    print(f"✅ Generated {len(all_interactions)} total interactions")
    print()
    
    # Analyze speaker distribution
    host1_count = sum(1 for interaction in all_interactions if interaction["speaker"] == "host1")
    host2_count = sum(1 for interaction in all_interactions if interaction["speaker"] == "host2")
    
    print(f"🎭 Speaker Distribution:")
    print(f"   Host1 (Samantha): {host1_count} segments")
    print(f"   Host2 (Daniel): {host2_count} segments")
    print()
    
    print("📋 Detailed Breakdown:")
    for i, interaction in enumerate(all_interactions, 1):
        speaker = interaction["speaker"]
        text = interaction["text"][:100] + "..." if len(interaction["text"]) > 100 else interaction["text"]
        interaction_type = interaction.get("type", "unknown")
        
        print(f"   {i:2d}. {speaker} ({interaction_type}): {text}")
    
    print()
    print("🔍 Analysis:")
    if host1_count == 0:
        print("❌ No host1 segments - all content going to host2")
    elif host2_count == 0:
        print("❌ No host2 segments - all content going to host1")
    elif abs(host1_count - host2_count) > len(all_interactions) * 0.7:
        print("⚠️  Heavily unbalanced - one speaker dominates")
    else:
        print("✅ Reasonably balanced speaker distribution")

if __name__ == "__main__":
    test_speaker_assignment()
