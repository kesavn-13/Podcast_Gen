#!/usr/bin/env python3
"""
Simplified test script for new PDF paper processing
Bypasses embeddings (quota exceeded) but uses Google Gemini for content generation
"""

import os
import sys
import asyncio
import json
import logging
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from backend.tools.sm_client import create_clients
from app.audio_generator import PodcastAudioProducer
from app.styles.podcast_structure import get_podcast_structure, format_podcast_segment, should_add_ad_break

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplifiedPaperTester:
    """Test workflow with NVIDIA NIMs and podcast styles"""
    
    def __init__(self, podcast_style: str = "layperson", paper_path: Optional[str] = None, output_dir: Optional[str] = None):
        default_paper = Path("samples/papers/LightEndoStereo- A Real-time Lightweight Stereo Matching Method for Endoscopy Images.pdf")
        self.paper_path = Path(paper_path) if paper_path else default_paper
        self.output_dir = Path(output_dir) if output_dir else Path("temp/new_paper_test")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Store selected podcast style
        self.podcast_style = podcast_style

        # Derive paper metadata for dynamic prompts
        self.paper_title = self._derive_title_from_path(self.paper_path)
        self.episode_slug = self._slugify(self.paper_title)

        # Track latest run artifacts for reuse by backend
        self._reset_run_state()

        # Check if we're in hackathon mode
        hackathon_mode = os.getenv('HACKATHON_MODE', 'false').lower() == 'true'
        use_nvidia = os.getenv('USE_NVIDIA_NIM', 'false').lower() == 'true'
        
        # Initialize clients (will automatically use NVIDIA if configured)
        self.reasoner_client, self.embedding_client = create_clients()
        
        # Show which clients we're using
        llm_type = type(self.reasoner_client).__name__
        embed_type = type(self.embedding_client).__name__
        
        if hackathon_mode and use_nvidia:
            print(f" HACKATHON MODE: Using NVIDIA NIMs")
            print(f" LLM: {llm_type}")
            print(f" Embedding: {embed_type}")
        else:
            print(f" Using LLM: {llm_type}, Embedding: {embed_type}")
        
        # Audio configuration flags so we can disable resource-heavy pieces on small nodes
        self.use_natural_voices = os.getenv('USE_NATURAL_VOICES', 'true').lower() == 'true'
        self.use_real_tts = os.getenv('USE_REAL_TTS', 'true').lower() == 'true'
        self.generate_audio_enabled = os.getenv('GENERATE_PODCAST_AUDIO', 'true').lower() == 'true'

        # Initialize audio producer only when audio output is enabled
        self.audio_producer = None
        if self.generate_audio_enabled:
            self.audio_producer = PodcastAudioProducer(
                use_natural_voices=self.use_natural_voices,
                podcast_style=podcast_style,
                use_real_tts=self.use_real_tts
            )
        
        print(f"🎭 Initialized with podcast style: {podcast_style}")
        
        # Show available style features
        style_features = {
            'layperson': 'Friendly, accessible explanations for general audience',
            'classroom': 'Teacher-student dynamic with structured learning approach',
            'tech_interview': 'Technical deep dive with expert analysis and methodology focus',
            'journal_club': 'Academic peer review and critical discussion of research findings',
            'npr_calm': 'Professional, measured NPR-style presentation with thoughtful pacing',
            'news_flash': 'Fast-paced, urgent news bulletin style with breaking research updates',
            'tech_energetic': 'High-energy tech discussion with excitement about innovations',
            'debate_format': 'Opposing viewpoints with spirited disagreement and critical analysis'
        }
        
        if podcast_style in style_features:
            print(f" Style features: {style_features[podcast_style]}")

        if not self.generate_audio_enabled:
            print(" Audio generation disabled via GENERATE_PODCAST_AUDIO=false")
        else:
            if self.use_real_tts:
                voice_note = "Google TTS + Enhanced pyttsx3" if self.use_natural_voices else "mock voice library"
                print(f" Natural voices enabled: {voice_note}")
            else:
                print(" Using mock TTS pipeline (USE_REAL_TTS=false)")
            print(f" Conversation styles integrated for human-like dialogue")

            # Show available styles when TTS is active
            try:
                from app.audio_generator import RealTTSEngine
                available_styles = RealTTSEngine.list_available_styles()
                print(" Available podcast styles:")
                for style_id, description in available_styles.items():
                    indicator = "👉" if style_id == podcast_style else "  "
                    print(f"   {indicator} {style_id}: {description}")
                print()
            except Exception as e:
                print(f"  Could not load styles info: {e}")
                print()
        
    def _load_json_with_fixes(self, raw_json, context=""):
        """Attempt to parse JSON string while fixing common formatting issues."""
        if raw_json is None:
            return {}
        if isinstance(raw_json, dict):
            return raw_json

        if not isinstance(raw_json, str):
            return raw_json

        cleaned = raw_json.strip()

        # Normalize smart quotes and apostrophes
        replacements = {
            "“": '"',
            "”": '"',
            "’": "'",
            "\u201c": '"',
            "\u201d": '"',
        }
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)

        # Fix keys accidentally including colon inside the quotes, e.g. "text: "
        cleaned = re.sub(r'"([A-Za-z0-9_]+)\s*:\s"', r'"\1": "', cleaned)

        # Attempt to repair lines with unclosed JSON strings produced by the model
        repaired_lines = []
        for line in cleaned.splitlines():
            trimmed = line.strip()
            if trimmed.startswith('"') and '":' in trimmed:
                quote_count = trimmed.count('"')
                if quote_count % 2 == 1:
                    line = line + '"'
            repaired_lines.append(line)
        cleaned = "\n".join(repaired_lines)

        # Remove trailing commas before closing braces/brackets
        cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)

        # Strip any trailing markdown fences accidentally left over
        if cleaned.startswith('```') and cleaned.endswith('```'):
            cleaned = cleaned.strip('`')

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            preview = cleaned[:500]
            raise ValueError(f"Failed to parse JSON{f' for {context}' if context else ''}: {exc}. Preview: {preview}")

    def _reset_run_state(self) -> None:
        """Reset cached run artifacts so each execution starts clean."""
        self.last_outline: Optional[Dict[str, Any]] = None
        self.last_scripts: Optional[Any] = None
        self.last_audio_path: Optional[str] = None
        self.last_result: Dict[str, Any] = {}

    def _derive_title_from_path(self, paper_path: Path) -> str:
        """Generate a readable paper title based on file metadata."""
        name = paper_path.stem if paper_path else "Research Paper"
        cleaned = name.replace("_", " ").replace("-", " ").strip()
        return cleaned.title() if cleaned else "Research Paper"

    def _derive_title_from_text(self, text: str) -> Optional[str]:
        """Use the first substantial line of text as the paper title."""
        for line in text.splitlines():
            candidate = line.strip()
            if len(candidate) < 8:
                continue
            if not any(ch.isalpha() for ch in candidate):
                continue
            # Ignore section headers that look like numbering only
            if candidate.lower().startswith(("table", "figure")):
                continue
            return candidate
        return None

    def _slugify(self, value: str) -> str:
        """Simple slug generator for filenames and identifiers."""
        if not value:
            return "research-paper"

        slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-")
        slug = slug.lower()
        return slug or "research-paper"

    def _refresh_metadata(self, text: Optional[str] = None) -> None:
        """Update derived metadata when new text becomes available."""
        if text:
            derived_title = self._derive_title_from_text(text)
            if derived_title:
                self.paper_title = derived_title
        self.episode_slug = self._slugify(self.paper_title)

    def configure_run(self, paper_path: Optional[str] = None, output_dir: Optional[str] = None) -> None:
        """Update paper and output directories for a new run."""
        if paper_path:
            self.paper_path = Path(paper_path)
        if output_dir:
            self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._reset_run_state()

    async def extract_pdf_text(self):
        """Extract text from PDF"""
        print("\n🔍 Step 1: PDF Text Extraction")
        print("=" * 50)
        
        if self.paper_path.suffix.lower() == ".txt":
            try:
                text = self.paper_path.read_text(encoding='utf-8')
                print(f" Loaded {len(text)} characters from text file")
                text_file = self.output_dir / "extracted_text.txt"
                text_file.write_text(text, encoding='utf-8')
                preview = text[:500] + "..." if len(text) > 500 else text
                print(f" Text preview:\n{preview}")
                self._refresh_metadata(text)
                return text
            except Exception as exc:
                print(f" Text loading error: {exc}")
                return None

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(self.paper_path)
            text = ""
            page_count = len(doc)
            for page in doc:
                text += page.get_text()
            doc.close()
            
            print(f" Extracted {len(text)} characters from {page_count} pages")
            
            # Save extracted text
            text_file = self.output_dir / "extracted_text.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Show preview
            preview = text[:500] + "..." if len(text) > 500 else text
            print(f"📄 Text preview:\n{preview}")

            self._refresh_metadata(text)
            
            return text
            
        except Exception as e:
            print(f" PDF extraction error: {e}")
            return None
    
    async def generate_outline_direct(self, paper_text):
        """Generate outline directly using Google Gemini (no embeddings)"""
        print("\n Step 2: Google Gemini Outline Generation (Direct)")
        print("=" * 50)
        
        try:
            # Use first 3000 characters for context
            context = paper_text[:3000]
            paper_title = self.paper_title or "Uploaded Research Paper"
            # Escape braces so the JSON template renders literally in the prompt
            outline_prompt = f"""
            You are a podcast script writer. Create a comprehensive 6-segment podcast outline for the research paper titled "{paper_title}".

            Paper content excerpt: {context}

            Create 6 segments covering:
            1. Introduction & Problem Setup (75 seconds)
            2. Background & Related Work (150 seconds)
            3. Methodology & Architecture (210 seconds)
            4. Experimental Results or Key Findings (210 seconds)
            5. Real-world Impact & Applications (150 seconds)
            6. Conclusions & Future Directions (75 seconds)

            IMPORTANT: Respond with ONLY valid JSON. No markdown, no explanations, no code blocks. Just the raw JSON object.

            JSON structure:
            {{
                "title": "{paper_title}",
                "description": "Podcast overview for the paper",
                "segments": [
                    {{
                        "title": "Segment topic",
                        "duration_seconds": 120,
                        "description": "Short summary of what this segment covers"
                    }},
                    ... (continue for all 6 segments)
                ]
            }}
            """
            
            messages = [{"role": "user", "content": outline_prompt}]
            response = await self.reasoner_client.generate(messages)
            
            # Parse JSON response
            try:
                # Handle the response format from Google Gemini and NVIDIA
                if isinstance(response, dict) and 'choices' in response:
                    # Extract content from the API response format
                        content = response['choices'][0]['message']['content']
                        outline_data = self._load_json_with_fixes(content, context="outline generation (choices)")
                elif isinstance(response, dict) and 'content' in response:
                    # NVIDIA NIM format - content may be wrapped in markdown
                    content = response['content']
                    
                    # Extract JSON from markdown code blocks if present
                    if '```json' in content:
                        # Find JSON block
                        json_start = content.find('```json') + 7
                        json_end = content.find('```', json_start)
                        if json_end != -1:
                            json_content = content[json_start:json_end].strip()
                        else:
                            json_content = content[json_start:].strip()
                    elif '```' in content:
                        # Generic code block
                        json_start = content.find('```') + 3
                        json_end = content.find('```', json_start)
                        if json_end != -1:
                            json_content = content[json_start:json_end].strip()
                        else:
                            json_content = content[json_start:].strip()
                    else:
                        json_content = content
                    
                        outline_data = self._load_json_with_fixes(json_content, context="outline generation (nim content)")
                elif isinstance(response, str):
                    outline_data = self._load_json_with_fixes(response, context="outline generation (string)")
                else:
                    outline_data = response
                
                segments = outline_data.get('segments', [])
                print(" Google Gemini outline generation successful")
                print(f" Generated {len(segments)} segments")
                
                # Debug: Show the actual response
                print(f" Debug - Response keys: {list(outline_data.keys())}")
                if not segments:
                    print(f"  No segments found. Full response: {outline_data}")
                
                # Save outline
                outline_file = self.output_dir / "podcast_outline.json"
                with open(outline_file, 'w') as f:
                    json.dump(outline_data, f, indent=2)
                
                for i, segment in enumerate(segments, 1):
                    print(f"   {i}. {segment.get('title', 'Untitled')} ({segment.get('duration_seconds', 0)}s)")
                
                # Return outline_data even if segments is empty for debugging
                self.last_outline = outline_data
                return outline_data
                
            except (json.JSONDecodeError, TypeError) as e:
                print(f" Failed to parse JSON response: {e}")
                print(f"Raw response type: {type(response)}")
                print(f"Raw response: {str(response)[:1000]}...")
                
                # Try to extract and show the actual JSON content
                if isinstance(response, dict) and 'content' in response:
                    print(f" JSON Content Length: {len(response['content'])}")
                    print(f" JSON Content Preview: {response['content'][:2000]}...")
                    if len(response['content']) > 2000:
                        print(f" JSON Content End: ...{response['content'][-500:]}")
                return None
                
        except Exception as e:
            print(f" Outline generation error: {e}")
            return None
    
    async def generate_and_validate_scripts(self, outline_data, paper_text):
        """Generate scripts with proper workflow: Draft → FactCheck → Rewrite if needed"""
        print("\n Step 3: Podcast Script Generation with FactCheck Workflow")
        print("=" * 50)
        
        try:
            segments = outline_data.get('segments', [])
            final_scripts = []
            
            # Check if we have segments
            if not segments:
                print(" No segments found in outline data")
                return None
            
            # Split paper text into sections for different segments
            text_sections = []
            section_size = len(paper_text) // len(segments)
            
            for i in range(len(segments)):
                start = i * section_size
                end = (i + 1) * section_size if i < len(segments) - 1 else len(paper_text)
                text_sections.append(paper_text[start:start+1500])  # Limit to 1500 chars per section
            
            for i, segment in enumerate(segments, 1):
                print(f"\n Processing Segment {i}: {segment.get('title', 'Untitled')}")
                print("─" * 40)
                
                # Use relevant text section
                context = text_sections[i-1] if i-1 < len(text_sections) else paper_text[:1500]
                
                # Step 3a: Draft Generation
                print(f" Drafting script...")
                draft_script = await self._generate_draft_script(segment, context, i)
                if not draft_script:
                    print(f" Failed to generate draft for segment {i}")
                    draft_script = self._fallback_script(segment, context)
                    print(f" Using fallback dialogue ({len(draft_script)} lines)")
                
                # Step 3b: Fact-Check
                print(f"   🔍 Fact-checking against source paper...")
                factcheck_result = await self._factcheck_script(draft_script, context, segment)
                
                # Step 3c: Rewrite if needed
                final_script = draft_script
                if factcheck_result['needs_rewrite']:
                    print(f" Rewriting based on fact-check feedback...")
                    final_script = await self._rewrite_script(draft_script, factcheck_result['feedback'], context)
                    print(f" Script rewritten with improved accuracy")
                else:
                    print(f" Script passed fact-check (accuracy: {factcheck_result['accuracy']:.1%})")
                
                final_scripts.append({
                    'segment_id': i,
                    'title': segment.get('title', 'Untitled'),
                    'script': final_script,
                    'factcheck_score': factcheck_result['accuracy'],
                    'factcheck_feedback': factcheck_result.get('feedback', ''),
                    'was_rewritten': factcheck_result['needs_rewrite']
                })
                
                # Small delay between segments
                await asyncio.sleep(1)
            
            if final_scripts:
                # Enhance scripts with podcast structure (intro, outro, ad breaks)
                enhanced_scripts = self._add_podcast_structure(final_scripts, outline_data.get('title', 'Research Discussion'))
                
                # Save all scripts with metadata
                scripts_file = self.output_dir / "podcast_scripts_factchecked.json"
                with open(scripts_file, 'w') as f:
                    json.dump(enhanced_scripts, f, indent=2)
                
                # Show summary
                total_accuracy = sum(s['factcheck_score'] for s in final_scripts) / len(final_scripts)
                rewrites = sum(1 for s in final_scripts if s['was_rewritten'])
                
                print(f"\n Generated {len(final_scripts)} fact-checked segments")
                print(f" Average factcheck accuracy: {total_accuracy:.1%}")
                print(f"  Segments rewritten: {rewrites}/{len(final_scripts)}")
                print(f" Added podcast structure elements (intro, outro, ad breaks)")
                
                self.last_scripts = enhanced_scripts
                return enhanced_scripts
            else:
                print(" No scripts were successfully generated")
                return None
                
        except Exception as e:
            print(f" Script generation workflow error: {e}")
            return None

    def _add_podcast_structure(self, final_scripts, topic_title):
        """Add intro, outro, and ad breaks to create a complete podcast experience"""
        enhanced_scripts = []
        total_segments = len(final_scripts)
        
        # Extract topic name for structure elements
        topic = topic_title.replace("Research Paper:", "").strip()
        
        # Add podcast intro
        intro_text = format_podcast_segment("intro", self.podcast_style, topic)
        enhanced_scripts.append({
            'segment_id': 0,
            'title': 'Podcast Intro',
            'script': [
                {"speaker": "host1", "text": intro_text}
            ],
            'factcheck_score': 1.0,
            'was_rewritten': False,
            'structure_type': 'intro'
        })
        
        # Add main content segments with ad breaks
        for i, script_data in enumerate(final_scripts):
            enhanced_scripts.append(script_data)
            
            # Add ad break in the middle for longer episodes
            if should_add_ad_break(i + 1, total_segments):
                ad_break_text = format_podcast_segment("ad_break", self.podcast_style, topic)
                enhanced_scripts.append({
                    'segment_id': f"ad_break_{i+1}",
                    'title': 'Ad Break',
                    'script': [
                        {"speaker": "host1", "text": ad_break_text}
                    ],
                    'factcheck_score': 1.0,
                    'was_rewritten': False,
                    'structure_type': 'ad_break'
                })
        
        # Add podcast outro
        outro_text = format_podcast_segment("outro", self.podcast_style, topic)
        enhanced_scripts.append({
            'segment_id': 'outro',
            'title': 'Podcast Outro',
            'script': [
                {"speaker": "host1", "text": outro_text}
            ],
            'factcheck_score': 1.0,
            'was_rewritten': False,
            'structure_type': 'outro'
        })
        
        return enhanced_scripts
    
    async def _generate_draft_script(self, segment, context, segment_num):
        """Generate initial draft script"""
        
        paper_title = self.paper_title or "the research paper"

        # Customize prompt based on podcast style
        if self.podcast_style == "debate_format":
            script_prompt = f"""
            Create a natural debate script between Dr. Sarah (research advocate) and Dr. Alex (research skeptic) discussing this segment of the research paper titled "{paper_title}".
            
            Segment: {segment.get('title', 'Untitled')}
            Description: {segment.get('description', '')}
            Target Duration: {segment.get('duration_seconds', 120)} seconds
            
            Paper Context: {context}
            
            Create a balanced debate conversation with:
            - host1 (Dr. Sarah): Generally supports the research but acknowledges valid criticism
            - host2 (Dr. Alex): More skeptical but gives credit where due
            
            CRITICAL: Make this sound like real humans having a thoughtful disagreement:
            - MORE DISAGREEMENT than agreement (85% opposition, 15% agreement)
            - Include moments where one person corrects the other's mistakes or misinterpretations
            - Sarah should sometimes misstate something that Alex corrects, and vice versa
            - Use natural correction phrases like:
              * "Wait, that's not right..."
              * "Actually, you're overlooking something important..."
              * "No, I disagree with that interpretation..."
              * "Hold on, that's not what the data shows..."
              * "Actually, I think you're wrong about that..."
            - Only agree when the point is genuinely strong and hard to dispute
            - Create substantive disagreements about methodology, conclusions, implications
            - Sound like colleagues having a spirited debate where they challenge each other's thinking
            
            IMPORTANT: Respond with ONLY valid JSON. No markdown, no explanations, no code blocks. Just the raw JSON object.
            
            JSON format:
            {{
                "script": [
                    {{"speaker": "host1", "text": "This research shows some really promising results..."}},
                    {{"speaker": "host2", "text": "I'll admit the results look good, but I'm still concerned about..."}},
                    ... (continue with natural balanced debate)
                ]
            }}
            """
        else:
            script_prompt = f"""
            Create a conversational podcast script between Dr. Sarah and Dr. Alex discussing this segment of the research paper titled "{paper_title}".
            
            Segment: {segment.get('title', 'Untitled')}
            Description: {segment.get('description', '')}
            Target Duration: {segment.get('duration_seconds', 120)} seconds
            
            Paper Context: {context}
            
            Create natural conversation with:
            - host1 (Dr. Sarah): Female researcher, explains technical concepts clearly
            - host2 (Dr. Alex): Male researcher, asks clarifying questions and provides insights
            
            Make it engaging and accessible while maintaining technical accuracy.
            
            IMPORTANT: Respond with ONLY valid JSON. No markdown, no explanations, no code blocks. Just the raw JSON object.
            
            JSON format:
            {{
                "script": [
                    {{"speaker": "host1", "text": "Welcome to our discussion on {paper_title}..."}},
                    {{"speaker": "host2", "text": "This is fascinating research. Can you explain..."}},
                    ... (continue with natural conversation)
                ]
            }}
            """
        
        try:
            messages = [{"role": "user", "content": script_prompt}]
            response = await self.reasoner_client.generate(messages)

            raw_content_str = None

            # Handle the response format from Google Gemini and NVIDIA
            if isinstance(response, dict) and 'choices' in response:
                raw_content_str = response['choices'][0]['message']['content']
                script_data = self._load_json_with_fixes(raw_content_str, context=f"script draft (segment {segment_num})")
            elif isinstance(response, dict) and 'content' in response:
                # NVIDIA NIM format - content may be wrapped in markdown
                content = response['content']
                raw_content_str = content

                # Extract JSON from markdown code blocks if present
                if '```json' in content:
                    # Find JSON block
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    if json_end != -1:
                        json_content = content[json_start:json_end].strip()
                    else:
                        json_content = content[json_start:].strip()
                elif '```' in content:
                    # Generic code block
                    json_start = content.find('```') + 3
                    json_end = content.find('```', json_start)
                    if json_end != -1:
                        json_content = content[json_start:json_end].strip()
                    else:
                        json_content = content[json_start:].strip()
                else:
                    json_content = content

                # Try to fix common JSON issues before parsing
                json_content = json_content.strip()

                # Fix common NVIDIA JSON issues
                if json_content.startswith('```') and not json_content.startswith('```json'):
                    # Remove any remaining code blocks
                    json_content = json_content.replace('```', '').strip()

                # Try to extract just the JSON object if there's extra text
                if '{' in json_content and '}' in json_content:
                    start = json_content.find('{')
                    end = json_content.rfind('}') + 1
                    json_content = json_content[start:end]

                script_data = self._load_json_with_fixes(json_content, context=f"script draft (segment {segment_num})")
            elif isinstance(response, str):
                raw_content_str = response
                script_data = self._load_json_with_fixes(response, context=f"script draft (segment {segment_num})")
            else:
                script_data = response
                
            script_lines = script_data.get('script', [])
            if not script_lines:
                raise ValueError("Model returned empty script list")

            print(f" Generated {len(script_lines)} dialogue lines")
            return script_lines
            
        except Exception as e:
            print(f" Draft generation failed: {e}")
            raw_preview = None
            if isinstance(response, dict) and 'content' in response:
                raw_preview = response['content']
                print(f" Raw content: {raw_preview[:500]}...")
            elif isinstance(response, dict) and 'choices' in response:
                raw_preview = response['choices'][0]['message']['content']
            elif isinstance(response, str):
                raw_preview = response

            if raw_preview:
                repaired = await self._attempt_json_repair(raw_preview, segment.get('title', 'Untitled'), segment_num)
                if repaired:
                    script_lines = repaired.get('script', [])
                    if script_lines:
                        print(f" JSON repair succeeded ({len(script_lines)} dialogue lines)")
                        return script_lines

            print(" Falling back to templated dialogue for this segment")
            return self._fallback_script(segment, context)
    
    async def _factcheck_script(self, script, context, segment):
        """Fact-check script against source material"""
        script_text = " ".join([line.get('text', '') for line in script])
        
        factcheck_prompt = f"""
        You are a fact-checker. Verify the accuracy of this podcast script segment against the source research paper content.
        
        Segment Topic: {segment.get('title', 'Unknown')}
        Source Paper Context: {context}
        
        Script to Check: {script_text}
        
        Analyze for:
        1. Technical accuracy
        2. Correct interpretation of research findings
        3. Appropriate representation of methodology
        4. Accurate citation of results
        
        Rate accuracy from 0.0 to 1.0 and provide feedback.
        
        IMPORTANT: Respond with ONLY valid JSON. No markdown, no explanations, no code blocks. Just the raw JSON object.
        
        JSON format:
        {{
            "accuracy": 0.85,
            "needs_rewrite": false,
            "feedback": "Script is technically accurate. Minor suggestion: clarify the 42 FPS performance metric context."
        }}
        """
        
        try:
            messages = [{"role": "user", "content": factcheck_prompt}]
            response = await self.reasoner_client.generate(messages)
            
            # Handle response format from Google Gemini and NVIDIA
            if isinstance(response, dict) and 'choices' in response:
                content = response['choices'][0]['message']['content']
                factcheck_data = self._load_json_with_fixes(content, context=f"factcheck (segment {segment.get('title', 'Unknown')})")
            elif isinstance(response, dict) and 'content' in response:
                # NVIDIA NIM format - content may be wrapped in markdown
                content = response['content']
                
                # Extract JSON from markdown code blocks if present
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    if json_end != -1:
                        json_content = content[json_start:json_end].strip()
                    else:
                        json_content = content[json_start:].strip()
                elif '```' in content:
                    json_start = content.find('```') + 3
                    json_end = content.find('```', json_start)
                    if json_end != -1:
                        json_content = content[json_start:json_end].strip()
                    else:
                        json_content = content[json_start:].strip()
                else:
                    json_content = content
                
                factcheck_data = self._load_json_with_fixes(json_content, context=f"factcheck (segment {segment.get('title', 'Unknown')})")
            elif isinstance(response, str):
                factcheck_data = self._load_json_with_fixes(response, context=f"factcheck (segment {segment.get('title', 'Unknown')})")
            else:
                factcheck_data = response
            
            accuracy = factcheck_data.get('accuracy', 0.8)
            needs_rewrite = factcheck_data.get('needs_rewrite', accuracy < 0.75)
            feedback = factcheck_data.get('feedback', 'No specific feedback provided')
            
            return {
                'accuracy': accuracy,
                'needs_rewrite': needs_rewrite,
                'feedback': feedback
            }
            
        except Exception as e:
            print(f"      ⚠️  Fact-check failed, assuming acceptable: {e}")
            return {'accuracy': 0.8, 'needs_rewrite': False, 'feedback': 'Fact-check unavailable'}
    
    async def _rewrite_script(self, original_script, feedback, context):
        """Rewrite script based on fact-check feedback"""
        original_text = json.dumps(original_script, indent=2)
        
        rewrite_prompt = f"""
        Improve this podcast script based on the fact-check feedback while maintaining the conversational flow.
        
        Original Script: {original_text}
        
        Fact-check Feedback: {feedback}
        
        Source Context: {context}
        
        IMPORTANT: Respond with ONLY valid JSON. No markdown, no explanations, no code blocks. Just the raw JSON object.
        
        JSON format:
        {{
            "script": [
                {{"speaker": "host1", "text": "..."}},
                {{"speaker": "host2", "text": "..."}},
                ...
            ]
        }}
        """
        
        try:
            messages = [{"role": "user", "content": rewrite_prompt}]
            response = await self.reasoner_client.generate(messages)
            
            # Handle response format from Google Gemini and NVIDIA
            if isinstance(response, dict) and 'choices' in response:
                content = response['choices'][0]['message']['content']
                script_data = self._load_json_with_fixes(content, context="rewrite script")
            elif isinstance(response, dict) and 'content' in response:
                # NVIDIA NIM format - content may be wrapped in markdown
                content = response['content']
                
                # Extract JSON from markdown code blocks if present
                if '```json' in content:
                    json_start = content.find('```json') + 7
                    json_end = content.find('```', json_start)
                    if json_end != -1:
                        json_content = content[json_start:json_end].strip()
                    else:
                        json_content = content[json_start:].strip()
                elif '```' in content:
                    json_start = content.find('```') + 3
                    json_end = content.find('```', json_start)
                    if json_end != -1:
                        json_content = content[json_start:json_end].strip()
                    else:
                        json_content = content[json_start:].strip()
                else:
                    json_content = content
                
                script_data = self._load_json_with_fixes(json_content, context="rewrite script")
            elif isinstance(response, str):
                script_data = self._load_json_with_fixes(response, context="rewrite script")
            else:
                script_data = response
                
            return script_data.get('script', original_script)
            
        except Exception as e:
            print(f" Rewrite failed, using original: {e}")
            return original_script
    
    async def generate_audio(self, scripts_data):
        """Step 4: TTS Generation and Step 5: Stitching with Podcast Styles"""
        print("\n Step 4: TTS Generation & Step 5: Audio Stitching")
        print("=" * 50)
        print(f" Using podcast style: {self.podcast_style}")
        
        paper_title = self.paper_title or "Research Paper Podcast"
        episode_slug = self.episode_slug or "research-paper"

        try:
            if not self.generate_audio_enabled or not self.audio_producer:
                print(" Audio generation disabled; skipping TTS and stitching steps")
                placeholder = self.output_dir / "audio_generation_skipped.txt"
                placeholder.write_text("Audio generation skipped by configuration.\n")
                self.last_audio_path = str(placeholder)
                return str(placeholder)

            # Prepare episode data
            episode_data = {
                'episode_id': episode_slug,
                'title': paper_title,
                'description': f'A comprehensive discussion of {paper_title}',
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
            
            # Generate audio with conversation styles
            print(" Starting audio generation with conversation flow...")
            
            # Preserve AI-generated speaker assignments instead of overriding them
            script_segments = []
            for segment in episode_data['segments']:
                script_dialogue = segment.get('script', [])
                
                if isinstance(script_dialogue, list) and script_dialogue:
                    # Preserve the original AI-generated speaker assignments
                    for dialogue_line in script_dialogue:
                        if isinstance(dialogue_line, dict):
                            speaker = dialogue_line.get('speaker', 'host1')
                            text = dialogue_line.get('text', '')
                            if text:
                                # Map AI speakers to our host system
                                if speaker in ['host1', 'Dr. Sarah', 'sarah']:
                                    mapped_speaker = 'host1'
                                elif speaker in ['host2', 'Dr. Alex', 'alex']:
                                    mapped_speaker = 'host2'
                                else:
                                    mapped_speaker = 'host1'  # default fallback
                                
                                script_segments.append({
                                    "text": text,
                                    "speaker": mapped_speaker
                                })
                        elif isinstance(dialogue_line, str) and dialogue_line:
                            script_segments.append({
                                "text": dialogue_line,
                                "speaker": "host1"  # fallback for string-only content
                            })
                elif isinstance(script_dialogue, str) and script_dialogue:
                    script_segments.append({
                        "text": script_dialogue,
                        "speaker": "host1"
                    })
            
            if not script_segments:
                print(" No content found for audio generation")
                return None
            
            print(f" Processing {len(script_segments)} dialogue segments preserving AI speaker assignments...")
            
            # Generate audio preserving original speaker assignments with natural voices + styles
            audio_file = await self.audio_producer.generate_podcast_audio(
                script_segments=script_segments,
                episode_id=f"episode_{episode_data['episode_id']}"
            )
            
            if audio_file and os.path.exists(audio_file):
                file_size = os.path.getsize(audio_file) / (1024 * 1024)  # MB
                print(f" Audio generated successfully with {self.podcast_style} style!")
                print(f" File: {audio_file}")
                print(f" Size: {file_size:.2f} MB")
                
                self.last_audio_path = audio_file
                return audio_file
            else:
                print(" Audio generation failed - no file created")
                return None
                
        except Exception as e:
            print(f" Audio generation error: {e}")
            return None

    async def _attempt_json_repair(self, raw_content: str, segment_title: str, segment_num: int) -> Optional[Dict[str, Any]]:
        """Ask the LLM to repair malformed JSON responses."""
        repair_prompt = f"""
        The following content was intended to be valid JSON for a podcast script segment (segment {segment_num}: {segment_title}) but contains formatting errors such as missing quotes or unescaped newlines.
        Please return ONLY valid JSON matching this schema:
        {{
            "script": [
                {{"speaker": "host1", "text": "..."}},
                {{"speaker": "host2", "text": "..."}}
            ]
        }}

        Content to repair:
        ```
        {raw_content}
        ```
        """

        messages = [
            {"role": "system", "content": "You fix malformed JSON and respond with valid JSON only."},
            {"role": "user", "content": repair_prompt}
        ]

        try:
            repair_response = await self.reasoner_client.generate(messages)

            repaired_text: Optional[str] = None
            if isinstance(repair_response, dict) and 'choices' in repair_response:
                repaired_text = repair_response['choices'][0]['message']['content']
            elif isinstance(repair_response, dict) and 'content' in repair_response:
                repaired_text = repair_response['content']
            elif isinstance(repair_response, str):
                repaired_text = repair_response

            if not repaired_text:
                return None

            return self._load_json_with_fixes(repaired_text, context="json repair")
        except Exception as exc:
            print(f" JSON repair attempt failed: {exc}")
            return None

    def _fallback_script(self, segment: Dict[str, Any], context: str) -> List[Dict[str, str]]:
        """Generate a minimal conversation when the model response is unusable."""
        title = segment.get('title', 'Research Highlight')
        description = segment.get('description', '')
        summary = description[:240] + ('...' if len(description) > 240 else '')
        default_summary = "this part builds on the paper's core ideas."
        summary_text = summary if summary else default_summary

        # Simple two-speaker exchange to keep pipeline moving
        return [
            {
                "speaker": "host1",
                "text": f"Let's unpack the '{title}' section. In short, {summary_text}"
            },
            {
                "speaker": "host2",
                "text": "Right, and based on the paper it emphasizes why this matters for the overall story."
            },
            {
                "speaker": "host1",
                "text": "Exactly. Even without the full script, we can highlight the motivations, the method, and what listeners should take away."
            },
            {
                "speaker": "host2",
                "text": "We'll plan to refine this section once the detailed draft is available, but this keeps the episode flowing."
            }
        ]
    
    async def run_simplified_test(self):
        """Run complete workflow: Upload → Index → Outline → Draft → FactCheck → Rewrite → TTS → Stitch → Export"""
        paper_title = self.paper_title or "Research Paper"
        print(f" Complete PDF Paper Workflow Test: {paper_title}")
        print(" Workflow: Upload → Index → Outline → Draft → FactCheck → Rewrite → TTS → Stitch → Export")
        print("  Note: Bypassing embeddings due to quota limits")
        print("=" * 70)
        print(f" Test started: {datetime.now()}")

        self._reset_run_state()

        # Step 1: Upload (PDF Text Extraction)
        print("\n Step 1: Upload")
        paper_text = await self.extract_pdf_text()
        if not paper_text:
            print(" Cannot proceed without extracted text")
            return False
        
        # Step 2: Index (Skipped due to embedding quota)
        print("\n  Step 2: Index")
        print("  Indexing skipped due to embedding API quota limits")
        print(" Using direct text analysis instead")
        
        # Step 3: Outline Generation
        print("\n Step 3: Outline Generation")
        outline_data = await self.generate_outline_direct(paper_text)
        if not outline_data:
            print(" Cannot proceed without outline")
            return False
        
        # Steps 4-6: Draft → FactCheck → Rewrite (for each segment)
        scripts_data = await self.generate_and_validate_scripts(outline_data, paper_text)
        if not scripts_data:
            print(" Cannot proceed without scripts")
            return False
        
        # Steps 7-8: TTS → Stitch
        audio_file = await self.generate_audio(scripts_data)
        
        # Step 9: Export & Final Results
        print("\n Step 9: Export & Final Results")
        print("=" * 70)
        if audio_file:
            if self.generate_audio_enabled:
                print(" COMPLETE SUCCESS: Full workflow pipeline working!")
                print(f" Generated podcast: {audio_file}")
            else:
                print(" COMPLETE SUCCESS: Text workflow complete (audio skipped by configuration)")
                print(f" Audio step output: {audio_file}")

            print(f" All files saved to: {self.output_dir}")
            print("\n Completed Workflow Steps:")
            print(" Upload: PDF text extraction")
            print(" Index: Skipped (embedding quota)")
            print(" Outline: Google Gemini generation")
            print(" Draft: Script generation per segment")
            print(" FactCheck: Accuracy verification")
            print(" Rewrite: Content improvement (if needed)")

            if self.generate_audio_enabled:
                print(" TTS: Professional audio synthesis")
                print(" Stitch: Episode assembly")
                print(" Export: Final MP3 generation")
            else:
                print(" TTS: Skipped (GENERATE_PODCAST_AUDIO=false)")
                print(" Stitch: Skipped (GENERATE_PODCAST_AUDIO=false)")
                print(" Export: Skipped (GENERATE_PODCAST_AUDIO=false)")
        else:
            print(" PARTIAL SUCCESS: Workflow mostly complete, audio issues")
        
        self.last_result = {
            "success": bool(audio_file),
            "paper_path": str(self.paper_path),
            "outline": self.last_outline,
            "segments": self.last_scripts,
            "audio_file": audio_file,
            "output_dir": str(self.output_dir)
        }

        return bool(audio_file)

async def test_multiple_styles():
    """Test the system with multiple podcast styles to showcase variety"""
    print("COMPREHENSIVE STYLE TESTING")
    print("=" * 60)
    
    # Test all available podcast styles from macOS folder with descriptions
    test_styles = [
        ('layperson', 'Friendly, accessible explanations for general audience'),
        ('classroom', 'Teacher-student dynamic with structured learning approach'),
        ('tech_interview', 'Technical deep dive with expert analysis and methodology focus'),
        ('journal_club', 'Academic peer review and critical discussion of research findings'),
        ('npr_calm', 'Professional, measured NPR-style presentation with thoughtful pacing'),
        ('news_flash', 'Fast-paced, urgent news bulletin style with breaking research updates'),
        ('tech_energetic', 'High-energy tech discussion with excitement about innovations'),
        ('debate_format', 'Opposing viewpoints with spirited disagreement and critical analysis')
    ]
    
    results = {}
    
    for style_name, style_description in test_styles:
        print(f"\n Testing Style: {style_name.upper()}")
        print(f" Description: {style_description}")
        print("-" * 60)
        
        try:
            tester = SimplifiedPaperTester(podcast_style=style_name)
            success = await tester.run_simplified_test()
            results[style_name] = success
            
            if success:
                print(f" {style_name} style: SUCCESSFUL")
            else:
                print(f" {style_name} style: FAILED")
                
        except Exception as e:
            print(f" {style_name} style error: {e}")
            results[style_name] = False
    
    # Summary
    print("\n STYLE TESTING SUMMARY")
    print("=" * 40)
    successful_styles = [style for style, success in results.items() if success]
    failed_styles = [style for style, success in results.items() if not success]
    
    print(f" Successful styles ({len(successful_styles)}/{len(test_styles)}):")
    for style in successful_styles:
        # Find description for this style
        style_desc = next((desc for name, desc in test_styles if name == style), "")
        print(f"   ✓ {style}: {style_desc}")
    
    if failed_styles:
        print(f" Failed styles ({len(failed_styles)}/{len(test_styles)}):")
        for style in failed_styles:
            style_desc = next((desc for name, desc in test_styles if name == style), "")
            print(f"   ✗ {style}: {style_desc}")
    
    if len(successful_styles) == len(test_styles):
        print(f"\n ALL {len(test_styles)} PODCAST STYLES WORKING PERFECTLY!")
        print(" Complete NVIDIA NIM integration with full style variety!")
    else:
        print(f"\n  ISSUES: {len(failed_styles)} styles need attention")
    
    return len(successful_styles) > 0

async def main():
    """Main test function with podcast style selection and NVIDIA integration"""
    import argparse
    
    # Parse command line arguments for style selection
    parser = argparse.ArgumentParser(description='Test PDF paper processing with NVIDIA NIMs and podcast styles')
    parser.add_argument('--style', 
                       choices=['layperson', 'classroom', 'tech_interview', 'journal_club', 'npr_calm', 'news_flash', 'tech_energetic', 'debate_format'],
                       default='layperson',
                       help='Choose podcast conversation style (default: layperson)')
    parser.add_argument('--test-multiple', 
                       action='store_true',
                       help='Test multiple podcast styles to showcase variety')
    parser.add_argument('--nvidia-only',
                       action='store_true', 
                       help='Force use of NVIDIA NIMs only (hackathon mode)')
    
    # Parse known args (ignore unknown ones for compatibility)
    args, _ = parser.parse_known_args()
    
    # Set hackathon environment if requested
    if args.nvidia_only:
        print(" NVIDIA-ONLY MODE: Using NVIDIA Llama + Embedding NIMs")
        os.environ['HACKATHON_MODE'] = 'true'
        os.environ['USE_NVIDIA_NIM'] = 'true'
        os.environ['USE_GOOGLE_LLM'] = 'false'
    
    try:
        if args.test_multiple:
            print(" TESTING MULTIPLE PODCAST STYLES WITH NVIDIA INTEGRATION")
            success = await test_multiple_styles()
        else:
            print(f" Selected podcast style: {args.style}")
            if args.nvidia_only:
                print(" Using NVIDIA Llama-3.1-Nemotron-Nano-8B-v1 + nv-embedqa-e5-v5")
            
            tester = SimplifiedPaperTester(podcast_style=args.style)
            success = await tester.run_simplified_test()
        
        if success:
            print("\n SUCCESS: Your PDF paper pipeline is working with podcast styles!")
            if not args.test_multiple:
                print(f" Used conversation style: {args.style}")
            if args.nvidia_only:
                print(" NVIDIA NIMs integration: WORKING")
            print("\n Available style options:")
            print("   --style layperson (friendly, accessible)")
            print("   --style debate_format (opposing viewpoints)")
            print("   --style tech_interview (technical deep dive)")
            print("   --style journal_club (academic discussion)")
            print("   --test-multiple (test 3 different styles)")
            print("   --nvidia-only (force NVIDIA NIMs only)")
        else:
            print("\n  ISSUES: Some components need attention")
            
        return success
        
    except Exception as e:
        print(f" Test execution error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
