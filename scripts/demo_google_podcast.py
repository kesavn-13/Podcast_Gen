#!/usr/bin/env python3
"""
Demo script showing complete Google Gemini + MP3 generation
Uses the working integration we've established
"""

import os
import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.tools.sm_client import create_clients
from app.agents.orchestrator import PodcastOrchestrator
from app.audio_generator import AudioGenerator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_google_podcast():
    """Demonstrate complete Google Gemini → MP3 podcast generation"""
    
    print("🚀 GOOGLE GEMINI PODCAST DEMO")
    print("=" * 50)
    
    # Create clients (should use Google Gemini from our integration)
    reasoner, embedder = create_clients()
    print(f"🤖 Using: {type(reasoner).__name__} + {type(embedder).__name__}")
    
    # Initialize orchestrator
    orchestrator = PodcastOrchestrator(reasoner, embedder)
    
    # Load a sample paper
    paper_path = project_root / "samples" / "papers" / "transformer_attention.txt"
    
    if not paper_path.exists():
        print(f"❌ Paper not found: {paper_path}")
        return
        
    with open(paper_path, 'r', encoding='utf-8') as f:
        paper_content = f.read()
    
    print(f"📄 Processing paper: {paper_path.name}")
    print(f"📝 Content length: {len(paper_content)} characters")
    
    # Process paper through orchestrator
    paper_id = "google_demo"
    
    try:
        # Index the paper
        orchestrator.index_paper(paper_id, paper_content, "Google Gemini Demo Paper")
        print("✅ Paper indexed successfully")
        
        # Generate outline
        outline_result = orchestrator.generate_outline(paper_id)
        print(f"📋 Outline generated: {outline_result.get('title', 'Unknown Title')}")
        print(f"🎬 Segments: {len(outline_result.get('segments', []))}")
        
        # Generate scripts for each segment
        segments = outline_result.get('segments', [])
        if not segments:
            print("❌ No segments generated")
            return
            
        # Process first segment for demo
        segment = segments[0]
        print(f"\n🎭 Processing segment: {segment.get('title', 'Untitled')}")
        
        # Generate segment script
        script_result = orchestrator.generate_segment_script(paper_id, segment)
        print(f"✅ Script generated: {len(script_result.get('script', []))} lines")
        
        # Fact-check the segment
        factcheck_result = orchestrator.fact_check_segment(paper_id, script_result)
        print(f"🔍 Fact-check score: {factcheck_result.get('factuality_score', 0)}")
        
        # Generate audio
        audio_gen = AudioGenerator()
        episode_info = {
            'id': f"{paper_id}_demo",
            'title': outline_result.get('title', 'Demo Episode'),
            'segments': [script_result]
        }
        
        print("\n🎵 Generating audio...")
        audio_path = audio_gen.generate_episode_audio(episode_info)
        
        if audio_path and Path(audio_path).exists():
            file_size = Path(audio_path).stat().st_size / (1024 * 1024)  # MB
            print(f"🎉 SUCCESS! Audio generated:")
            print(f"   📁 File: {audio_path}")
            print(f"   💾 Size: {file_size:.2f} MB")
            
            # Also check metadata file
            metadata_path = str(audio_path).replace('_final.mp3', '_metadata.json')
            if Path(metadata_path).exists():
                print(f"   📊 Metadata: {metadata_path}")
        else:
            print("❌ Audio generation failed")
            
    except Exception as e:
        logger.error(f"❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_google_podcast()