#!/usr/bin/env python3
"""
Generate a COMPLETE research paper podcast with multiple segments
This addresses the user's requirement for full paper coverage
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv()

from backend.tools.sm_client import create_clients

async def generate_complete_paper_outline():
    """Generate a complete multi-segment outline for a research paper"""
    
    print("🚀 GENERATING COMPLETE RESEARCH PAPER PODCAST")
    print("=" * 60)
    
    # Create clients
    reasoner, embedder = create_clients()
    print(f"🤖 Using: {type(reasoner).__name__}")
    
    # Load the transformer paper
    paper_path = project_root / "samples" / "papers" / "transformer_attention.txt"
    with open(paper_path, 'r', encoding='utf-8') as f:
        paper_content = f.read()
    
    print(f"📄 Paper: {paper_path.name}")
    print(f"📝 Length: {len(paper_content)} characters")
    
    # Create a comprehensive outline prompt
    outline_prompt = f"""
    You are a podcast planning agent. Generate a COMPLETE episode outline for this research paper.
    
    Paper Content:
    {paper_content}
    
    Create a comprehensive podcast with 5-6 segments covering:
    1. Introduction & Paper Overview (60-90 seconds)
    2. Background & Related Work (120-180 seconds) 
    3. Methodology & Approach (180-240 seconds)
    4. Key Results & Findings (180-240 seconds)
    5. Discussion & Implications (120-180 seconds)
    6. Conclusions & Future Work (60-90 seconds)
    
    For each segment, include:
    - title: Clear segment title
    - type: intro/background/methodology/results/discussion/conclusion
    - duration_target: Target duration in seconds
    - key_points: Array of 3-5 main discussion points
    - conversation_starters: Questions/hooks for natural dialogue
    
    Format as JSON:
    {{
        "title": "Full Paper Title",
        "summary": "2-sentence paper summary",
        "segments": [array of segment objects],
        "total_duration_estimate": total_seconds,
        "complexity_score": 0.0-1.0
    }}
    
    Make this a COMPLETE research paper discussion, not just a summary.
    """
    
    try:
        # Generate the outline
        print("\n🎯 Generating comprehensive outline...")
        outline_response = await reasoner.generate([{"role": "user", "content": outline_prompt}], response_type="outline")
        
        print(f"✅ Outline generated: {type(outline_response)}")
        
        # Parse and display the outline
        if isinstance(outline_response, dict):
            outline_data = outline_response
        else:
            # Try to extract from response
            print(f"Response content: {str(outline_response)[:500]}...")
            return
        
        print(f"\n📋 COMPLETE PODCAST OUTLINE:")
        print(f"🎧 Title: {outline_data.get('title', 'Unknown')}")
        print(f"📝 Summary: {outline_data.get('summary', 'No summary')}")
        
        segments = outline_data.get('segments', [])
        print(f"🎬 Total Segments: {len(segments)}")
        
        total_duration = 0
        for i, segment in enumerate(segments, 1):
            duration = segment.get('duration_target', 0)
            total_duration += duration
            print(f"\n   {i}. {segment.get('title', 'Untitled')}")
            print(f"      Type: {segment.get('type', 'unknown')}")
            print(f"      Duration: {duration}s ({duration/60:.1f} min)")
            print(f"      Key Points: {len(segment.get('key_points', []))}")
            
            # Show first few key points
            key_points = segment.get('key_points', [])[:3]
            for point in key_points:
                print(f"        • {point}")
        
        print(f"\n⏱️ Total Duration: {total_duration}s ({total_duration/60:.1f} minutes)")
        print(f"🧠 Complexity Score: {outline_data.get('complexity_score', 'Unknown')}")
        
        # Save the complete outline
        output_file = project_root / "temp" / "complete_outline.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(outline_data, f, indent=2)
        
        print(f"\n💾 Saved outline to: {output_file}")
        
        if len(segments) >= 5:
            print(f"\n🎉 SUCCESS! Generated {len(segments)} segments for complete paper coverage")
            print("✅ This is a proper research paper podcast, not just a summary!")
            return True
        else:
            print(f"\n⚠️ Only {len(segments)} segments generated. Need 5-6 for complete coverage.")
            return False
            
    except Exception as e:
        print(f"❌ Outline generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(generate_complete_paper_outline())