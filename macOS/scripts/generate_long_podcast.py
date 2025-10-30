"""
Main integration script for Google LLM + Long Podcast system
Combines paper processing, LLM generation, and audio synthesis
"""

import os
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PaperToPodcastGenerator:
    """
    Main class for generating long-form podcasts from research papers
    Uses Google Gemini for content generation and enhanced TTS for audio
    """
    
    def __init__(self, google_api_key: str = None):
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        
        if not self.google_api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable.")
        
        self.gemini_client = None
        self.tts_engine = None
        self.podcast_producer = None
        
        logger.info("🚀 Paper-to-Podcast Generator initialized")
    
    async def initialize(self):
        """Initialize all components"""
        try:
            # Initialize Google Gemini client
            from backend.tools.google_llm_client import GoogleGeminiClient
            self.gemini_client = GoogleGeminiClient(api_key=self.google_api_key)
            logger.info("✅ Google Gemini client ready")
            
            # Initialize audio system
            from app.enhanced_audio_generator import create_enhanced_audio_system
            use_google_tts = os.getenv("USE_GOOGLE_TTS", "true").lower() == "true"
            self.tts_engine, self.podcast_producer = create_enhanced_audio_system(use_google_tts=use_google_tts)
            logger.info(f"✅ Audio system ready (Google TTS: {use_google_tts})")
            
        except ImportError as e:
            logger.error(f"❌ Import error: {e}")
            logger.error("   Please run: python scripts/setup_google_llm.py")
            raise
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            raise
    
    async def process_paper_to_podcast(self, 
                                     paper_content: str,
                                     style: str = "tech_energetic",
                                     episode_id: str = None) -> Dict[str, Any]:
        """
        Complete pipeline: paper → outline → scripts → audio → final episode
        
        Args:
            paper_content: Text content of research paper
            style: Podcast style (tech_energetic, npr_calm, etc.)
            episode_id: Unique identifier for episode
            
        Returns:
            Dictionary with episode information and file paths
        """
        if not episode_id:
            episode_id = f"episode_{hash(paper_content[:100]) % 10000}"
        
        logger.info(f"🎬 Starting paper-to-podcast generation: {episode_id}")
        
        try:
            # Step 1: Generate podcast outline
            logger.info("📝 Generating podcast outline...")
            outline_response = await self.gemini_client.generate_podcast_outline(
                paper_content=paper_content,
                style=style
            )
            
            outline = self._parse_json_response(outline_response, "outline")
            logger.info(f"✅ Outline generated: {len(outline.get('segments', []))} segments")
            
            # Step 2: Generate detailed scripts for each segment
            logger.info("📜 Generating segment scripts...")
            episode_script = await self._generate_episode_scripts(outline, paper_content)
            logger.info(f"✅ Scripts generated: {episode_script['total_duration']:.1f}s estimated")
            
            # Step 3: Create audio episode
            logger.info("🎤 Creating audio episode...")
            episode_path = await self.podcast_producer.create_episode(
                episode_script=episode_script,
                episode_id=episode_id
            )
            
            # Step 4: Get episode statistics
            stats = await self.podcast_producer.get_episode_stats(episode_path)
            
            # Step 5: Save metadata
            metadata = {
                "episode_id": episode_id,
                "paper_content_length": len(paper_content),
                "style": style,
                "outline": outline,
                "episode_script": episode_script,
                "audio_stats": stats,
                "file_path": episode_path
            }
            
            metadata_path = Path(episode_path).parent / f"{episode_id}_metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info("🎉 SUCCESS! Complete podcast generated")
            logger.info(f"   📁 Audio: {episode_path}")
            logger.info(f"   📄 Metadata: {metadata_path}")
            logger.info(f"   ⏱️  Duration: {stats.get('duration_minutes', 0):.1f} minutes")
            
            return {
                "success": True,
                "episode_path": episode_path,
                "metadata_path": str(metadata_path),
                "duration_minutes": stats.get('duration_minutes', 0),
                "file_size_mb": stats.get('file_size_mb', 0),
                "segments_count": len(episode_script.get('segments', [])),
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "episode_id": episode_id
            }
    
    async def _generate_episode_scripts(self, outline: Dict[str, Any], paper_content: str) -> Dict[str, Any]:
        """Generate detailed scripts for all segments"""
        episode_script = {
            "title": outline.get("title", "AI Research Podcast"),
            "total_duration": 0,
            "segments": []
        }
        
        segments = outline.get("segments", [])
        previous_segments = []
        
        for i, segment in enumerate(segments):
            logger.info(f"   📝 Script {i+1}/{len(segments)}: {segment.get('type', 'unknown')}")
            
            # Generate script for this segment
            script_response = await self.gemini_client.generate_segment_script(
                outline_segment=segment,
                paper_context=paper_content,
                previous_segments=previous_segments[-2:]  # Last 2 segments for context
            )
            
            segment_script = self._parse_json_response(script_response, f"segment_{i}")
            
            # Ensure we have dialogue
            if "dialogue" not in segment_script or not segment_script["dialogue"]:
                segment_script["dialogue"] = self._create_fallback_dialogue(segment)
            
            episode_script["segments"].append(segment_script)
            
            # Update total duration and context
            segment_duration = sum(d.get("duration", 5.0) for d in segment_script.get("dialogue", []))
            episode_script["total_duration"] += segment_duration
            
            # Add to previous segments for context
            segment_text = " ".join(d.get("text", "") for d in segment_script.get("dialogue", []))
            previous_segments.append(segment_text[:500])  # Keep first 500 chars
        
        return episode_script
    
    def _parse_json_response(self, response: Dict[str, Any], context: str) -> Dict[str, Any]:
        """Parse JSON response from Gemini with fallbacks"""
        try:
            content = response["choices"][0]["message"]["content"]
            
            if content.startswith('{'):
                return json.loads(content)
            else:
                logger.warning(f"⚠️  {context}: Response not in JSON format, using fallback")
                return self._create_fallback_structure(context)
                
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            logger.warning(f"⚠️  {context}: Failed to parse response ({e}), using fallback")
            return self._create_fallback_structure(context)
    
    def _create_fallback_structure(self, context: str) -> Dict[str, Any]:
        """Create fallback structure when parsing fails"""
        if context == "outline":
            return {
                "title": "AI Research Discussion",
                "duration_estimate": 1200,
                "segments": [
                    {
                        "type": "intro",
                        "duration": 120,
                        "speakers": ["host1", "host2"],
                        "content": "Introduction to the research",
                        "key_points": ["Overview", "Significance", "What we'll cover"]
                    },
                    {
                        "type": "main_discussion",
                        "duration": 600,
                        "speakers": ["host1", "host2"],
                        "content": "Deep dive into the research",
                        "key_points": ["Methodology", "Key findings", "Innovation"]
                    },
                    {
                        "type": "outro",
                        "duration": 180,
                        "speakers": ["host1", "host2"],
                        "content": "Conclusions and implications",
                        "key_points": ["Summary", "Impact", "Future work"]
                    }
                ]
            }
        else:
            return {
                "segment_type": "discussion",
                "dialogue": self._create_fallback_dialogue({"type": "discussion"})
            }
    
    def _create_fallback_dialogue(self, segment: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create fallback dialogue when generation fails"""
        segment_type = segment.get("type", "discussion")
        content = segment.get("content", "this research topic")
        
        if segment_type == "intro":
            return [
                {
                    "speaker": "host1",
                    "text": f"Welcome to our deep dive into {content}. I'm excited to explore this fascinating research with you today.",
                    "duration": 10.0,
                    "emotion": "enthusiastic"
                },
                {
                    "speaker": "host2",
                    "text": "Thanks for having me! This research represents a significant breakthrough in artificial intelligence and machine learning.",
                    "duration": 8.0,
                    "emotion": "professional"
                }
            ]
        elif segment_type == "outro":
            return [
                {
                    "speaker": "host1",
                    "text": "This has been a fascinating discussion about cutting-edge AI research. The implications for the field are truly exciting.",
                    "duration": 10.0,
                    "emotion": "satisfied"
                },
                {
                    "speaker": "host2",
                    "text": "Absolutely! Thank you for joining us, and we look forward to exploring more groundbreaking research in future episodes.",
                    "duration": 8.0,
                    "emotion": "warm"
                }
            ]
        else:
            return [
                {
                    "speaker": "host1",
                    "text": f"Let's dive deeper into {content}. The methodology here is particularly interesting.",
                    "duration": 8.0,
                    "emotion": "analytical"
                },
                {
                    "speaker": "host2",
                    "text": "I agree. The results show significant improvements over previous approaches, which could have major implications for the field.",
                    "duration": 10.0,
                    "emotion": "excited"
                }
            ]
    
    async def process_paper_file(self, paper_path: str, **kwargs) -> Dict[str, Any]:
        """Process a paper file (PDF or TXT) and generate podcast"""
        paper_path = Path(paper_path)
        
        if not paper_path.exists():
            return {"success": False, "error": f"File not found: {paper_path}"}
        
        try:
            # Extract text content
            if paper_path.suffix.lower() == '.pdf':
                paper_content = self._extract_pdf_text(paper_path)
            elif paper_path.suffix.lower() == '.txt':
                with open(paper_path, 'r', encoding='utf-8') as f:
                    paper_content = f.read()
            else:
                return {"success": False, "error": f"Unsupported file type: {paper_path.suffix}"}
            
            # Generate episode ID from filename
            episode_id = paper_path.stem.replace(' ', '_').lower()
            
            # Process to podcast
            return await self.process_paper_to_podcast(
                paper_content=paper_content,
                episode_id=episode_id,
                **kwargs
            )
            
        except Exception as e:
            return {"success": False, "error": f"Failed to process file: {e}"}
    
    def _extract_pdf_text(self, pdf_path: Path) -> str:
        """Extract text from PDF file"""
        try:
            import PyPDF2
            
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
                
        except ImportError:
            raise ImportError("PyPDF2 required for PDF processing. Install with: pip install PyPDF2")
    
    def list_sample_papers(self) -> List[str]:
        """List available sample papers"""
        samples_dir = project_root / "samples" / "papers"
        if samples_dir.exists():
            return [str(f) for f in samples_dir.glob("*.txt")]
        return []


async def main():
    """Main function for command-line usage"""
    print("🚀 PAPER-TO-PODCAST GENERATOR")
    print("=" * 50)
    
    # Check for API key
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ GOOGLE_API_KEY environment variable not set")
        print("   Get your key: https://makersuite.google.com/app/apikey")
        print("   Set it: export GOOGLE_API_KEY='your-key-here'")
        return
    
    try:
        # Initialize generator
        generator = PaperToPodcastGenerator(google_api_key=google_api_key)
        await generator.initialize()
        
        # Check for paper file argument
        if len(sys.argv) > 1:
            paper_path = sys.argv[1]
            style = sys.argv[2] if len(sys.argv) > 2 else "tech_energetic"
            
            print(f"📄 Processing paper: {paper_path}")
            result = await generator.process_paper_file(paper_path, style=style)
            
        else:
            # Use sample content
            sample_papers = generator.list_sample_papers()
            
            if sample_papers:
                print(f"📚 Found {len(sample_papers)} sample papers")
                paper_path = sample_papers[0]
                print(f"📄 Processing sample: {Path(paper_path).name}")
                result = await generator.process_paper_file(paper_path)
            else:
                # Use built-in sample
                sample_content = """
                GPT-4 Technical Report
                
                We report the development of GPT-4, a large-scale, multimodal model which can accept 
                image and text inputs and produce text outputs. While less capable than humans in 
                many real-world scenarios, GPT-4 exhibits human-level performance on various 
                professional and academic benchmarks, including passing a simulated bar exam with 
                a score around the top 10% of test takers.
                
                GPT-4 is a Transformer-based model pre-trained to predict the next token in a document. 
                The post-training alignment process results in improved performance on measures of 
                factuality and adherence to desired behavior.
                """
                
                print("📄 Using built-in sample content")
                result = await generator.process_paper_to_podcast(
                    paper_content=sample_content,
                    episode_id="gpt4_demo"
                )
        
        # Display results
        if result["success"]:
            print("\n🎉 PODCAST GENERATION SUCCESSFUL!")
            print(f"   📁 Audio file: {result['episode_path']}")
            print(f"   ⏱️  Duration: {result['duration_minutes']:.1f} minutes")
            print(f"   💾 File size: {result['file_size_mb']:.1f} MB")
            print(f"   📊 Segments: {result['segments_count']}")
        else:
            print(f"\n❌ GENERATION FAILED: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())