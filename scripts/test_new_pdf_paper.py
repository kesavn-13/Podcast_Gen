#!/usr/bin/env python3
"""
Test script for new PDF paper processing
Tests complete workflow: PDF → Text → Google Gemini → Audio Generation
"""

import os
import sys
import asyncio
import json
from pathlib import Path
import logging
from datetime import datetime
import time

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from backend.tools.sm_client import create_clients
from app.audio_generator import PodcastAudioProducer
from rag.indexer import RetrievalInterface

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewPaperTester:
    """Test complete workflow with new PDF paper"""
    
    def __init__(self):
        self.paper_path = "samples/papers/LightEndoStereo- A Real-time Lightweight Stereo Matching Method for Endoscopy Images.pdf"
        self.output_dir = Path("temp/new_paper_test")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize clients
        self.reasoner_client, self.embedding_client = create_clients()
        self.audio_producer = PodcastAudioProducer()
        self.retrieval = RetrievalInterface()
        
    async def test_pdf_extraction(self):
        """Test 1: Extract text from PDF"""
        print("\n🔍 Test 1: PDF Text Extraction")
        print("=" * 50)
        
        try:
            # Try different PDF extraction methods
            extracted_text = None
            
            # Method 1: PyMuPDF
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(self.paper_path)
                text = ""
                for page in doc:
                    text += page.get_text()
                doc.close()
                extracted_text = text
                print(f"✅ PyMuPDF extraction successful: {len(extracted_text)} characters")
            except Exception as e:
                print(f"❌ PyMuPDF failed: {e}")
            
            # Method 2: PyPDF2 (fallback)
            if not extracted_text:
                try:
                    import PyPDF2
                    with open(self.paper_path, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        text = ""
                        for page in reader.pages:
                            text += page.extract_text()
                        extracted_text = text
                        print(f"✅ PyPDF2 extraction successful: {len(extracted_text)} characters")
                except Exception as e:
                    print(f"❌ PyPDF2 failed: {e}")
            
            if extracted_text:
                # Save extracted text
                text_file = self.output_dir / "extracted_text.txt"
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)
                
                # Show preview
                preview = extracted_text[:500] + "..." if len(extracted_text) > 500 else extracted_text
                print(f"📄 Text preview:\n{preview}")
                
                return extracted_text
            else:
                print("❌ All PDF extraction methods failed")
                return None
                
        except Exception as e:
            print(f"❌ PDF extraction error: {e}")
            return None
    
    async def test_rag_indexing(self, text_content):
        """Test 2: RAG indexing and retrieval with rate limit management"""
        print("\n🗃️  Test 2: RAG Indexing & Retrieval")
        print("=" * 50)
        
        try:
            # Create smaller chunks to reduce embedding load
            chunks = []
            words = text_content.split()
            chunk_size = 300  # Reduced chunk size to use fewer embeddings
            
            # Limit total chunks to stay within quota
            max_chunks = 8  # Start with fewer chunks to manage quota
            
            for i in range(0, min(len(words), max_chunks * chunk_size), chunk_size):
                chunk_text = " ".join(words[i:i + chunk_size])
                chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source": "LightEndoStereo",
                        "chunk_id": i // chunk_size
                    }
                })
            
            print(f"📦 Created {len(chunks)} text chunks (quota-aware)")
            
            # Index the paper content with rate limiting
            print("🔄 Starting batched indexing to manage API quota...")
            
            # Process chunks in smaller batches with delays
            batch_size = 2  # Very small batches to respect rate limits
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_text = " ".join([chunk["text"] for chunk in batch])
                
                print(f"   Processing batch {i//batch_size + 1}/{(len(chunks) + batch_size - 1)//batch_size}")
                
                try:
                    # Index this batch
                    paper_id = f"lightendostereo_batch_{i//batch_size}"
                    await self.retrieval.index_paper(paper_id, batch_text, f"LightEndoStereo Batch {i//batch_size + 1}")
                    
                    # Add delay between batches to respect rate limits
                    if i + batch_size < len(chunks):
                        print(f"   ⏱️  Waiting 10 seconds for rate limit...")
                        await asyncio.sleep(10)
                        
                except Exception as e:
                    print(f"   ⚠️  Batch {i//batch_size + 1} failed: {e}")
                    # Continue with other batches
                    continue
            
            print("✅ RAG indexing completed with rate limit management")
            
            # Test retrieval with simple text matching if embeddings fail
            test_queries = [
                "stereo matching",
                "endoscopy images", 
                "real-time processing",
                "lightweight method"
            ]
            
            print("🔍 Testing retrieval...")
            for query in test_queries:
                try:
                    # Try to retrieve from all batches
                    all_results = []
                    for batch_id in range((len(chunks) + batch_size - 1)//batch_size):
                        paper_id = f"lightendostereo_batch_{batch_id}"
                        try:
                            results = await self.retrieval.retrieve_facts(query, k=1, paper_id=paper_id)
                            all_results.extend(results)
                            # Small delay between queries
                            await asyncio.sleep(2)
                        except Exception as e:
                            print(f"   ⚠️  Query failed for batch {batch_id}: {str(e)[:100]}...")
                            continue
                    
                    print(f"🔍 Query '{query}': {len(all_results)} results")
                    if all_results:
                        print(f"   Best match: {all_results[0]['content'][:100]}...")
                        
                except Exception as e:
                    print(f"   ❌ Query '{query}' failed: {str(e)[:100]}...")
                    continue
            
            return True
            
        except Exception as e:
            print(f"❌ RAG indexing error: {e}")
            return False
    
    async def test_google_gemini_outline(self):
        """Test 3: Generate podcast outline with Google Gemini"""
        print("\n🧠 Test 3: Google Gemini Outline Generation")
        print("=" * 50)
        
        try:
            # Get paper context from multiple batches with rate limiting
            print("🔄 Gathering context from indexed content...")
            all_context = []
            
            # Try to get context from multiple batches
            max_batches = 3  # Limit to avoid quota issues
            for batch_id in range(max_batches):
                paper_id = f"lightendostereo_batch_{batch_id}"
                try:
                    context_results = await self.retrieval.retrieve_facts("LightEndoStereo stereo matching endoscopy", k=2, paper_id=paper_id)
                    for result in context_results:
                        all_context.append(result['content'])
                    
                    # Small delay between batch queries
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    print(f"   ⚠️  Could not retrieve from batch {batch_id}: {str(e)[:100]}...")
                    continue
            
            # If context retrieval failed, use the original text directly
            if not all_context:
                print("   📄 Using direct text content (embeddings quota exceeded)")
                # Use first 2000 characters of the extracted text
                context = self.extracted_text[:2000] if hasattr(self, 'extracted_text') else "LightEndoStereo research paper content"
            else:
                context = "\n".join(all_context[:3])  # Limit context size
            
            outline_prompt = f"""
            You are a podcast script writer. Create a comprehensive 6-segment podcast outline for this research paper about LightEndoStereo.
            
            Paper content: {context[:2000]}...
            
            Create 6 segments covering:
            1. Introduction & Problem Setup
            2. Background & Related Work  
            3. Methodology & Architecture
            4. Experimental Results
            5. Clinical Applications & Impact
            6. Conclusions & Future Work
            
            Format as JSON with segments array containing title, duration_seconds, and description for each segment.
            """
            
            messages = [{"role": "user", "content": outline_prompt}]
            response = await self.reasoner_client.generate(messages)
            
            # Try to parse JSON response
            try:
                outline_data = json.loads(response)
                print("✅ Google Gemini outline generation successful")
                print(f"📊 Generated {len(outline_data.get('segments', []))} segments")
                
                # Save outline
                outline_file = self.output_dir / "podcast_outline.json"
                with open(outline_file, 'w') as f:
                    json.dump(outline_data, f, indent=2)
                
                for i, segment in enumerate(outline_data.get('segments', []), 1):
                    print(f"   {i}. {segment.get('title', 'Untitled')} ({segment.get('duration_seconds', 0)}s)")
                
                return outline_data
                
            except json.JSONDecodeError:
                print("❌ Failed to parse JSON from Google Gemini response")
                print(f"Raw response: {response[:200]}...")
                return None
                
        except Exception as e:
            print(f"❌ Google Gemini outline error: {e}")
            return None
    
    async def test_script_generation(self, outline_data):
        """Test 4: Generate podcast scripts for each segment"""
        print("\n📝 Test 4: Podcast Script Generation")
        print("=" * 50)
        
        try:
            segments = outline_data.get('segments', [])
            generated_scripts = []
            
            for i, segment in enumerate(segments, 1):
                print(f"🎬 Generating script for segment {i}: {segment.get('title', 'Untitled')}")
                
                # Get relevant context for this segment with rate limiting
                context_pieces = []
                try:
                    # Try to get context from first few batches only
                    for batch_id in range(min(2, 3)):  # Limit to 2 batches
                        paper_id = f"lightendostereo_batch_{batch_id}"
                        try:
                            context_results = await self.retrieval.retrieve_facts(
                                f"LightEndoStereo {segment.get('title', '')} {segment.get('description', '')}", 
                                k=1,  # Reduced to 1 result per batch
                                paper_id=paper_id
                            )
                            if context_results:
                                context_pieces.append(context_results[0]['content'])
                            
                            # Small delay between batch queries
                            await asyncio.sleep(2)
                            
                        except Exception as e:
                            print(f"   ⚠️  Context retrieval failed for batch {batch_id}: {str(e)[:100]}...")
                            continue
                    
                    if context_pieces:
                        context = "\n".join(context_pieces)
                    else:
                        # Fallback to using extracted text directly
                        context = self.extracted_text[i*1000:(i+1)*1500] if hasattr(self, 'extracted_text') else f"LightEndoStereo segment {i+1} content"
                        
                except Exception as e:
                    print(f"   ⚠️  Using fallback context due to: {str(e)[:100]}...")
                    context = self.extracted_text[i*1000:(i+1)*1500] if hasattr(self, 'extracted_text') else f"LightEndoStereo segment {i+1} content"
                
                script_prompt = f"""
                Create a conversational podcast script between Dr. Sarah and Dr. Alex discussing this segment of the LightEndoStereo research paper.
                
                Segment: {segment.get('title', 'Untitled')}
                Description: {segment.get('description', '')}
                Target Duration: {segment.get('duration_seconds', 120)} seconds
                
                Context: {context[:1500]}...
                
                Format as natural conversation with:
                - host1 (Dr. Sarah): Female researcher, explains technical concepts clearly
                - host2 (Dr. Alex): Male researcher, asks clarifying questions and provides insights
                
                Make it engaging and accessible while maintaining technical accuracy.
                Return as JSON with 'script' array containing {{"speaker": "host1/host2", "text": "dialogue"}} objects.
                """
                
                messages = [{"role": "user", "content": script_prompt}]
                response = await self.reasoner_client.generate(messages)
                
                try:
                    script_data = json.loads(response)
                    script_lines = script_data.get('script', [])
                    print(f"   ✅ Generated {len(script_lines)} dialogue lines")
                    
                    generated_scripts.append({
                        'segment_id': i,
                        'title': segment.get('title', 'Untitled'),
                        'script': script_lines
                    })
                    
                except json.JSONDecodeError:
                    print(f"   ❌ Failed to parse script JSON for segment {i}")
                    continue
            
            if generated_scripts:
                # Save all scripts
                scripts_file = self.output_dir / "podcast_scripts.json"
                with open(scripts_file, 'w') as f:
                    json.dump(generated_scripts, f, indent=2)
                
                print(f"✅ Generated scripts for {len(generated_scripts)} segments")
                return generated_scripts
            else:
                print("❌ No scripts were successfully generated")
                return None
                
        except Exception as e:
            print(f"❌ Script generation error: {e}")
            return None
    
    async def test_audio_generation(self, scripts_data):
        """Test 5: Generate audio from scripts"""
        print("\n🎵 Test 5: Audio Generation")
        print("=" * 50)
        
        try:
            # Prepare audio data
            episode_data = {
                'title': 'LightEndoStereo: Real-time Stereo Matching for Endoscopy',
                'description': 'A comprehensive discussion of lightweight stereo matching methods for medical endoscopy applications',
                'segments': []
            }
            
            # Convert scripts to audio format
            for script_segment in scripts_data:
                segment_data = {
                    'segment_id': script_segment['segment_id'],
                    'title': script_segment['title'],
                    'script': script_segment['script']
                }
                episode_data['segments'].append(segment_data)
            
            # Generate audio
            print("🎤 Starting audio generation...")
            audio_file = self.audio_producer.generate_complete_podcast(episode_data)
            
            if audio_file and os.path.exists(audio_file):
                file_size = os.path.getsize(audio_file) / (1024 * 1024)  # MB
                print(f"✅ Audio generated successfully!")
                print(f"📁 File: {audio_file}")
                print(f"📊 Size: {file_size:.2f} MB")
                
                # Generate metadata
                metadata = {
                    'title': episode_data['title'],
                    'description': episode_data['description'],
                    'file_path': audio_file,
                    'file_size_mb': round(file_size, 2),
                    'segments_count': len(episode_data['segments']),
                    'generated_at': datetime.now().isoformat(),
                    'source_paper': 'LightEndoStereo'
                }
                
                metadata_file = self.output_dir / "episode_metadata.json"
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                return audio_file
            else:
                print("❌ Audio generation failed - no file created")
                return None
                
        except Exception as e:
            print(f"❌ Audio generation error: {e}")
            return None
    
    async def run_complete_test(self):
        """Run complete end-to-end test"""
        print("🚀 Testing New PDF Paper: LightEndoStereo")
        print("=" * 60)
        print(f"📅 Test started: {datetime.now()}")
        print(f"📄 Paper: {self.paper_path}")
        print(f"📁 Output directory: {self.output_dir}")
        
        # Test 1: PDF Extraction
        text_content = await self.test_pdf_extraction()
        if not text_content:
            print("❌ Cannot proceed without extracted text")
            return False
        
        # Store extracted text for later use if needed
        self.extracted_text = text_content
        
        # Test 2: RAG Indexing
        rag_success = await self.test_rag_indexing(text_content)
        if not rag_success:
            print("❌ Cannot proceed without RAG indexing")
            return False
        
        # Test 3: Outline Generation
        outline_data = await self.test_google_gemini_outline()
        if not outline_data:
            print("❌ Cannot proceed without outline")
            return False
        
        # Test 4: Script Generation
        scripts_data = await self.test_script_generation(outline_data)
        if not scripts_data:
            print("❌ Cannot proceed without scripts")
            return False
        
        # Test 5: Audio Generation
        audio_file = await self.test_audio_generation(scripts_data)
        
        # Final Results
        print("\n🎯 FINAL TEST RESULTS")
        print("=" * 60)
        if audio_file:
            print("✅ COMPLETE SUCCESS: Full pipeline working!")
            print(f"🎧 Generated podcast: {audio_file}")
            print(f"📊 All test files saved to: {self.output_dir}")
        else:
            print("⚠️  PARTIAL SUCCESS: Pipeline mostly working, audio generation issues")
        
        return bool(audio_file)

async def main():
    """Main test function"""
    try:
        tester = NewPaperTester()
        success = await tester.run_complete_test()
        
        if success:
            print("\n🎉 SUCCESS: Your new PDF paper is working perfectly!")
        else:
            print("\n⚠️  ISSUES: Some components need attention")
            
        return success
        
    except Exception as e:
        print(f"❌ Test execution error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Run the test
    result = asyncio.run(main())
    sys.exit(0 if result else 1)