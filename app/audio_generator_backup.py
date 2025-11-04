"""
Audio Generation Pipeline for Paper→Podcast (Enhanced Windows Version)
Supports both mock development and AWS Polly production
Enhanced with podcast conversation styles and humanized voices
"""

import os
import asyncio
import tempfile
import json
import re
import random
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import subprocess
import logging

# Import styles system for humanized conversations
try:
    from .styles import TextProcessor, get_available_styles, get_style_config, list_all_styles
    STYLES_AVAILABLE = True
except ImportError:
    STYLES_AVAILABLE = False
    logging.warning("Styles system not available - using basic audio generation")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioSegment:
    """Represents a single audio segment with metadata"""
    
    def __init__(self, 
                 text: str, 
                 speaker: str, 
                 voice_id: str = None,
                 emotion: str = "neutral",
                 duration: float = None):
        self.text = text
        self.speaker = speaker  # "host1", "host2", "narrator"
        self.voice_id = voice_id
        self.emotion = emotion
        self.duration = duration
        self.audio_path = None
        # Enhanced attributes for style system
        self.use_style_processing = False
        self.content_type = None
        self.interaction_type = None


class RealTTSEngine:
    """Enhanced Real TTS engine with humanized voices and style processing"""
    
    def __init__(self, audio_dir: str = "temp/audio/segments", style_name: str = "layperson", use_coqui: bool = True):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize style processing if available
        self.style_name = style_name
        self.text_processor = None
        if STYLES_AVAILABLE:
            try:
                self.text_processor = TextProcessor(style_name)
                logger.info(f"✅ Style system enabled: {style_name}")
            except Exception as e:
                logger.warning(f"⚠️ Style system initialization failed: {e}")
        
        # Determine which TTS engine to use for humanized voices
        self.use_coqui = use_coqui
        self.coqui_available = False
        
        # Try to initialize Coqui TTS for natural voices
        if use_coqui:
            try:
                import TTS
                self.coqui_available = True
                self._init_coqui_tts()
                logger.info(f"🎤 Coqui TTS initialized for natural voices")
            except ImportError:
                logger.warning("⚠️ Coqui TTS not available, falling back to pyttsx3")
                logger.info("   To install: pip install TTS")
                self.coqui_available = False
            except Exception as e:
                logger.warning(f"⚠️ Coqui TTS initialization failed: {e}")
                self.coqui_available = False
        
        # Try Google TTS as alternative to Coqui
        self.gtts_available = False
        if not self.coqui_available and use_coqui:
            try:
                import gtts
                self.gtts_available = True
                logger.info(f"🎤 Google TTS initialized for natural voices")
            except ImportError:
                logger.warning("⚠️ Google TTS not available")
                
        if not self.coqui_available and not self.gtts_available:
            logger.info(f"🎵 Using enhanced pyttsx3 with humanization features")
        
        # Initialize voices configuration (essential - must always exist)
        self._initialize_voice_config()
    
    def _initialize_voice_config(self):
        """Initialize voice configuration - this must always succeed"""
        # Enhanced voice configurations with humanized personality traits
        self.base_voices = {
            "host1": {
                "name": "Dr. Sarah Chen",
                "voice_index": 1,
                "base_rate": 165,
                "volume": 0.9,
                "personality": "curious_everyman",
                "energy": "warm-curious",
                "pitch_variation": 1.1,
                "conversation_traits": {
                    "question_enthusiasm": 1.08,
                    "explanation_patience": 0.95,
                    "excitement_boost": 1.12
                }
            },
            "host2": {
                "name": "Prof. Mike Rodriguez", 
                "voice_index": 0,
                "base_rate": 155,
                "volume": 0.95,
                "personality": "friendly_explainer",
                "energy": "warm-encouraging", 
                "pitch_variation": 0.9,
                "conversation_traits": {
                    "teaching_pace": 0.92,
                    "emphasis_strength": 1.05,
                    "technical_precision": 0.88
                }
            },
            "narrator": {
                "name": "System Narrator",
                "voice_index": 1,
                "base_rate": 175,
                "volume": 0.85,
                "personality": "professional",
                "energy": "clear-neutral",
                "pitch_variation": 1.0,
                "conversation_traits": {
                    "announcement_clarity": 0.98,
                    "transition_smoothness": 1.02
                }
            }
        }
        
        # Apply conversation style adjustments to base voice configurations
        try:
            self.voices = self._apply_style_voice_adjustments()
        except Exception as e:
            logger.warning(f"Could not apply style adjustments, using base voices: {e}")
            # Fallback to base voices without style adjustments
            self.voices = {}
            for speaker_id, base_config in self.base_voices.items():
                config = base_config.copy()
                config["rate"] = base_config["base_rate"]
                self.voices[speaker_id] = config
    
    def _init_coqui_tts(self):
        """Initialize Coqui TTS with natural voice models"""
        try:
            from TTS.api import TTS
            
            # Use the same high-quality models as macOS version
            # Primary: Tacotron2-DDC for very natural single voice
            try:
                self.coqui_model = TTS("tts_models/en/ljspeech/tacotron2-DDC")
                self.coqui_model_name = "tacotron2-DDC"
                logger.info("✅ Loaded Tacotron2-DDC model (highly natural voice)")
            except Exception as e:
                # Fallback: VCTK for multiple speakers
                self.coqui_model = TTS("tts_models/en/vctk/vits")
                self.coqui_model_name = "vctk"
                logger.info("✅ Loaded VCTK model (multiple speakers)")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Coqui TTS: {e}")
            raise
    
    def _get_coqui_speaker_for_role(self, speaker: str) -> str:
        """Get appropriate Coqui speaker ID based on role"""
        if self.coqui_model_name == "vctk":
            # Multiple speakers available
            speaker_map = {
                "host1": "p225",  # Clear female voice
                "host2": "p226",  # Clear male voice  
                "narrator": "p227"  # Narrator voice
            }
            return speaker_map.get(speaker, "p225")
        else:
            # Single speaker model (Tacotron2-DDC)
            return None
    
    def _get_gtts_config_for_speaker(self, speaker: str) -> dict:
        """Get Google TTS configuration for different speakers"""
        gtts_configs = {
            "host1": {
                "lang": "en",
                "tld": "com",  # US English - clear, professional
                "slow": False,
                "voice_name": "US English"
            },
            "host2": {
                "lang": "en", 
                "tld": "com.au",  # Australian English - different accent
                "slow": False,
                "voice_name": "Australian English"
            },
            "narrator": {
                "lang": "en",
                "tld": "co.uk",  # British English - authoritative narrator
                "slow": False, 
                "voice_name": "British English"
            }
        }
        return gtts_configs.get(speaker, gtts_configs["host1"])
    
    def _apply_style_voice_adjustments(self) -> Dict[str, Dict[str, Any]]:
        """Apply conversation style-specific adjustments to voice configurations"""
        adjusted_voices = {}
        
        # Get style-specific speech rate adjustments if text processor is available
        style_rate_multipliers = {"host1": 1.0, "host2": 1.0, "narrator": 1.0}
        
        if self.text_processor and hasattr(self.text_processor, 'conversation_engine'):
            try:
                # Get host dynamics from the conversation style
                host_configs = self.text_processor.conversation_engine.host_configs
                for speaker_id, base_config in self.base_voices.items():
                    if speaker_id in host_configs:
                        style_host_config = host_configs[speaker_id]
                        style_speech_rate = style_host_config.get("speech_rate", 130)
                        
                        # Calculate multiplier based on style's preferred rate vs base rate
                        base_rate = base_config["base_rate"]
                        style_rate_multipliers[speaker_id] = style_speech_rate / base_rate
                        
                        logger.debug(f"Style adjustment for {speaker_id}: {style_rate_multipliers[speaker_id]:.2f}x")
            except Exception as e:
                logger.debug(f"Could not apply style rate adjustments: {e}")
        
        # Apply adjustments to create final voice configurations
        for speaker_id, base_config in self.base_voices.items():
            adjusted_config = base_config.copy()
            
            # Apply style-based rate adjustment
            style_multiplier = style_rate_multipliers.get(speaker_id, 1.0)
            adjusted_rate = int(base_config["base_rate"] * style_multiplier)
            
            # Ensure rate stays within reasonable bounds
            adjusted_config["rate"] = max(80, min(250, adjusted_rate))
            
            adjusted_voices[speaker_id] = adjusted_config
            
        return adjusted_voices
    
    async def synthesize_segment(self, segment: AudioSegment) -> str:
        """
        Enhanced TTS synthesis with style processing and natural conversation flow
        
        Args:
            segment: AudioSegment to synthesize with optional style processing attributes
            
        Returns:
            Path to generated audio file
        """
        # Include style and content info in filename for better caching
        style_suffix = f"_{self.style_name}" if hasattr(self, 'style_name') else ""
        content_type = getattr(segment, 'content_type', 'general')
        interaction_type = getattr(segment, 'interaction_type', 'statement')
        
        filename = f"{segment.speaker}_{hash(segment.text[:50])}_{len(segment.text)}{style_suffix}_{content_type}_{interaction_type}.wav"
        output_path = self.audio_dir / filename
        
        try:
            # Use real TTS with priority: Coqui → Google TTS → pyttsx3
            await self._synthesize_speech(segment.text, segment.speaker, output_path)
            
            # Calculate actual duration based on text
            word_count = len(segment.text.split())
            voice_config = self.voices.get(segment.speaker, self.voices["narrator"])
            estimated_duration = (word_count / voice_config["rate"]) * 60  # Convert to seconds
            
            segment.audio_path = str(output_path)
            segment.duration = estimated_duration
            
            logger.info(f"🎤 Real TTS: {segment.speaker} - '{segment.text[:50]}...' → {estimated_duration:.1f}s")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Real TTS failed: {e}")
            # Fallback to tone-based audio
            await self._create_tone_audio(output_path, segment.speaker, max(2.0, len(segment.text) / 10))
            return str(output_path)
    
    async def _synthesize_speech(self, text: str, speaker: str, output_path: Path):
        """
        Main speech synthesis method with priority chain:
        1. Coqui TTS (best quality, if available)
        2. Google TTS (natural voices, cloud-based)
        3. Enhanced pyttsx3 (fallback, always available)
        """
        try:
            # Apply style processing if available
            processed_text = text
            if self.text_processor:
                try:
                    processed_segments = self.text_processor.process_text_segment(text, speaker)
                    if processed_segments:
                        processed_text = processed_segments[0].get("text", text)
                        logger.debug(f"✨ Applied style processing: {speaker}")
                except Exception as e:
                    logger.debug(f"Style processing failed, using original text: {e}")
            
            # Try Coqui TTS first (if available)
            if hasattr(self, 'coqui_available') and self.coqui_available:
                try:
                    await self._synthesize_with_coqui(processed_text, speaker, output_path)
                    return
                except Exception as e:
                    logger.warning(f"Coqui TTS failed, falling back to Google TTS: {e}")
            
            # Try Google TTS second (natural voices, no installation required)
            if hasattr(self, 'gtts_available') and self.gtts_available:
                try:
                    await self._synthesize_with_gtts(processed_text, speaker, output_path)
                    return
                except Exception as e:
                    logger.warning(f"Google TTS failed, falling back to pyttsx3: {e}")
            
            # Final fallback to enhanced pyttsx3
            await self._synthesize_with_pyttsx3(processed_text, speaker, output_path)
            
        except Exception as e:
            logger.error(f"❌ All TTS methods failed: {e}")
            raise e
    
    async def _synthesize_with_pyttsx3(self, text: str, speaker: str, output_path: Path):
        """Enhanced speech synthesis with style processing and personality variations"""
        # If Coqui is available, use it for much more natural voices
        if self.coqui_available:
            return await self._synthesize_with_coqui(text, speaker, output_path)
        
        # If Google TTS is available, use it for natural voices
        if self.gtts_available:
            return await self._synthesize_with_gtts(text, speaker, output_path)
        
        # Fallback to enhanced pyttsx3
        try:
            import pyttsx3
            import random
            
            # Apply style processing if available
            processed_text = text
            if self.text_processor:
                try:
                    voice_config = self.voices.get(speaker, self.voices["narrator"])
                    # Enhance text with conversational elements using the style system
                    processed_segments = self.text_processor.process_text_segment(text, speaker)
                    if processed_segments:
                        # Use the first enhanced segment's text
                        processed_text = processed_segments[0].get("text", text)
                        logger.debug(f"✨ Applied style processing for {speaker}")
                    else:
                        processed_text = text
                except Exception as e:
                    logger.debug(f"Style processing failed, using original text: {e}")
            
            # Initialize TTS engine
            engine = pyttsx3.init()
            
            # Get voice configuration
            voice_config = self.voices.get(speaker, self.voices["narrator"])
            
            # Get available voices
            voices = engine.getProperty('voices')
            
            # Set voice (try to use different voices for different speakers)
            if voices and len(voices) > voice_config["voice_index"]:
                engine.setProperty('voice', voices[voice_config["voice_index"]].id)
            elif voices and len(voices) > 1:
                # Fallback: use second voice for male speakers
                voice_idx = 1 if speaker == "host2" else 0
                voice_idx = min(voice_idx, len(voices) - 1)
                engine.setProperty('voice', voices[voice_idx].id)
            
            # Apply enhanced voice properties with personality variations
            base_rate = voice_config["rate"]
            base_volume = voice_config["volume"]
            
            # Add sophisticated personality-based variations for humanized speech
            personality = voice_config.get("personality", "default")
            energy = voice_config.get("energy", "neutral")
            
            # Enhanced personality-based speech patterns (EXTREMELY NOTICEABLE)
            if personality == "curious_everyman":
                # Very enthusiastic, engaging delivery with lots of natural curiosity
                rate_variation = random.uniform(0.75, 1.35)  # MUCH wider dynamic range
                volume_variation = random.uniform(0.92, 1.08) 
                # Add MUCH MORE excitement for questions and discoveries
                if "?" in processed_text or any(word in processed_text.lower() for word in ["wow", "amazing", "incredible", "breakthrough", "fascinating"]):
                    rate_variation *= 1.25  # MUCH faster when excited
                    volume_variation *= 1.08  # MUCH louder
                # Add lots of curiosity pauses and fillers
                processed_text = processed_text.replace("?", "? ... Hmm, that's really interesting! ")
                processed_text = processed_text.replace(" and ", " and, you know, ")
                processed_text = processed_text.replace(" so ", " so ... let me think about this ... ")
                
            elif personality == "friendly_explainer":
                # Very warm, patient teacher with super authoritative confidence
                rate_variation = random.uniform(0.70, 0.95)  # MUCH more measured and slow
                volume_variation = random.uniform(1.02, 1.08)
                # Slow down MUCH MORE for complex explanations
                if any(word in processed_text.lower() for word in ["however", "therefore", "specifically", "particularly", "methodology", "algorithm"]):
                    rate_variation *= 0.75  # MUCH slower for emphasis
                # Add lots of teaching pauses and explanatory phrases
                processed_text = processed_text.replace(". ", ". ... Now, this is really important ... ")
                processed_text = processed_text.replace(" because ", " because, and this is key, ")
                processed_text = processed_text.replace(" that ", " that absolutely fascinating ")
                
            elif personality == "professional":
                # Consistent, clear, broadcast-quality delivery
                rate_variation = random.uniform(0.97, 1.03)
                volume_variation = random.uniform(0.98, 1.01)
                # Even more consistent for announcements
                if speaker == "narrator":
                    rate_variation = random.uniform(0.99, 1.01)
            else:
                # Natural human variation - nobody speaks perfectly consistently
                rate_variation = random.uniform(0.95, 1.05)
                volume_variation = random.uniform(0.98, 1.02)
            
            # Add MORE NOTICEABLE contextual emotion-based adjustments
            text_lower = processed_text.lower()
            if any(word in text_lower for word in ["excited", "breakthrough", "amazing", "incredible", "revolutionary", "fascinating"]):
                rate_variation *= 1.08  # Noticeably faster delivery
                volume_variation *= 1.03  # More energetic
                # Add excitement emphasis
                processed_text = processed_text.replace("!", "! ... ")
            elif any(word in text_lower for word in ["concern", "problem", "limitation", "carefully", "however", "unfortunately"]):
                rate_variation *= 0.90  # Much more measured delivery
                volume_variation *= 1.02  # Slightly more serious
                # Add thoughtful pauses
                processed_text = processed_text.replace(", ", ", ... ")
            elif any(word in text_lower for word in ["think about", "consider", "imagine", "let me", "so basically"]):
                rate_variation *= 0.88  # Very thoughtful, pause-filled delivery
                # Add contemplative pauses
                processed_text = processed_text.replace(" about ", " about ... ")
                processed_text = processed_text.replace(" that ", " that ... ")
            
            # Apply variations
            engine.setProperty('rate', int(base_rate * rate_variation))
            engine.setProperty('volume', min(1.0, base_volume * volume_variation))
            
            # Clean text for better TTS with enhanced processing
            clean_text = self._clean_text_for_tts(processed_text)
            
            # Generate speech to file
            engine.save_to_file(clean_text, str(output_path))
            engine.runAndWait()
            
            logger.info(f"✅ Enhanced TTS: {speaker} ({personality}) - {len(clean_text)} chars")
            
        except ImportError:
            logger.warning("pyttsx3 not available, falling back to tone generation")
            raise
        except Exception as e:
            logger.error(f"Enhanced TTS synthesis failed: {e}")
            raise
    
    async def _synthesize_with_coqui(self, text: str, speaker: str, output_path: Path):
        """Synthesize speech using Coqui TTS for natural, human-like voices"""
        try:
            # Apply style processing if available (same as pyttsx3 path)
            processed_text = text
            if self.text_processor:
                try:
                    voice_config = self.voices.get(speaker, self.voices["narrator"])
                    processed_segments = self.text_processor.process_text_segment(text, speaker)
                    if processed_segments:
                        processed_text = processed_segments[0].get("text", text)
                        logger.debug(f"✨ Applied style processing for Coqui TTS: {speaker}")
                except Exception as e:
                    logger.debug(f"Style processing failed for Coqui, using original text: {e}")
            
            # Clean text for better TTS (reuse our enhanced cleaning)
            clean_text = self._clean_text_for_tts(processed_text)
            
            # Generate speech with Coqui TTS
            if self.coqui_model_name == "vctk":
                # Multiple speaker model
                coqui_speaker = self._get_coqui_speaker_for_role(speaker)
                self.coqui_model.tts_to_file(
                    text=clean_text,
                    speaker=coqui_speaker,
                    file_path=str(output_path)
                )
                logger.info(f"✅ Coqui TTS (VCTK-{coqui_speaker}): {speaker} - {len(clean_text)} chars")
            else:
                # Single speaker model (Tacotron2-DDC - very natural)
                self.coqui_model.tts_to_file(
                    text=clean_text,
                    file_path=str(output_path)
                )
                logger.info(f"✅ Coqui TTS (Tacotron2-DDC): {speaker} - {len(clean_text)} chars - NATURAL VOICE")
            
        except Exception as e:
            logger.error(f"❌ Coqui TTS synthesis failed: {e}")
            # Fallback to pyttsx3 if Coqui fails
            logger.info("🔄 Falling back to enhanced pyttsx3...")
            import pyttsx3
            import random
            
            # Use the original pyttsx3 synthesis code as fallback
            engine = pyttsx3.init()
            voice_config = self.voices.get(speaker, self.voices["narrator"])
            voices = engine.getProperty('voices')
            
            if voices and len(voices) > voice_config["voice_index"]:
                engine.setProperty('voice', voices[voice_config["voice_index"]].id)
            
            engine.setProperty('rate', voice_config["rate"])
            engine.setProperty('volume', voice_config["volume"])
            
            clean_text = self._clean_text_for_tts(processed_text)
            engine.save_to_file(clean_text, str(output_path))
            engine.runAndWait()
            
            logger.info(f"✅ Fallback pyttsx3: {speaker} - {len(clean_text)} chars")
    
    async def _synthesize_with_gtts(self, text: str, speaker: str, output_path: Path):
        """Synthesize speech using Google TTS for natural, human-like voices"""
        try:
            from gtts import gTTS
            import asyncio
            
            # Apply style processing if available (same as other paths)
            processed_text = text
            if self.text_processor:
                try:
                    processed_segments = self.text_processor.process_text_segment(text, speaker)
                    if processed_segments:
                        processed_text = processed_segments[0].get("text", text)
                        logger.debug(f"✨ Applied style processing for Google TTS: {speaker}")
                except Exception as e:
                    logger.debug(f"Style processing failed for Google TTS, using original text: {e}")
            
            # Clean text for better TTS (reuse our enhanced cleaning)
            clean_text = self._clean_text_for_tts(processed_text)
            
            # Get Google TTS configuration for this speaker
            gtts_config = self._get_gtts_config_for_speaker(speaker)
            
            # Generate speech with Google TTS
            def _gtts_synthesis():
                try:
                    tts = gTTS(
                        text=clean_text,
                        lang=gtts_config["lang"],
                        tld=gtts_config["tld"],
                        slow=gtts_config["slow"]
                    )
                    
                    # Save to a temporary MP3 file first
                    temp_mp3 = str(output_path).replace('.wav', '_temp.mp3')
                    tts.save(temp_mp3)
                    
                    # Convert MP3 to WAV if needed
                    if output_path.suffix.lower() == '.wav':
                        try:
                            # Properly convert MP3 to WAV using pydub
                            from pydub import AudioSegment as PyDubSegment
                            audio = PyDubSegment.from_mp3(temp_mp3)
                            audio.export(str(output_path), format="wav")
                            os.remove(temp_mp3)  # Clean up temp file
                            logger.debug(f"Google TTS: Converted MP3 to proper WAV format")
                        except ImportError:
                            # If pydub not available, fall back to enhanced pyttsx3
                            logger.info(f"📦 pydub not available for MP3->WAV conversion")
                            logger.info(f"💡 Install with: pip install pydub")
                            logger.info(f"🔄 Using enhanced pyttsx3 with humanization instead")
                            if os.path.exists(temp_mp3):
                                os.remove(temp_mp3)  # Clean up
                            return False  # This will trigger fallback
                        except Exception as e:
                            # If conversion fails, fall back to enhanced pyttsx3
                            if "ffmpeg" in str(e).lower() or "cannot find the file" in str(e).lower():
                                logger.info(f"🎵 Google TTS needs ffmpeg for WAV conversion")
                                logger.info(f"💡 Install ffmpeg or use enhanced pyttsx3 (works great!)")
                                logger.info(f"🔄 Using enhanced pyttsx3 with conversation styles")
                            else:
                                logger.warning(f"MP3->WAV conversion failed: {e}")
                            if os.path.exists(temp_mp3):
                                os.remove(temp_mp3)  # Clean up
                            return False  # This will trigger fallback
                    else:
                        # Output is MP3, just rename
                        import shutil
                        shutil.move(temp_mp3, str(output_path))
                        
                    return True
                except Exception as e:
                    logger.error(f"Google TTS synthesis error: {e}")
                    return False
            
            # Run in thread to avoid blocking
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(None, _gtts_synthesis)
            
            if success:
                voice_name = gtts_config["voice_name"]
                logger.info(f"✅ Google TTS ({voice_name}): {speaker} - {len(clean_text)} chars - NATURAL VOICE")
            else:
                raise Exception("Google TTS synthesis failed")
                
        except Exception as e:
            logger.error(f"❌ Google TTS synthesis failed: {e}")
            # Fallback to enhanced pyttsx3 if Google TTS fails
            logger.info("🔄 Falling back to enhanced pyttsx3...")
            
            import pyttsx3
            import random
            
            # Use the original pyttsx3 synthesis code as fallback
            engine = pyttsx3.init()
            voice_config = self.voices.get(speaker, self.voices["narrator"])
            voices = engine.getProperty('voices')
            
            if voices and len(voices) > voice_config["voice_index"]:
                engine.setProperty('voice', voices[voice_config["voice_index"]].id)
            
            engine.setProperty('rate', voice_config["rate"])
            engine.setProperty('volume', voice_config["volume"])
            
            clean_text = self._clean_text_for_tts(processed_text)
            engine.save_to_file(clean_text, str(output_path))
            engine.runAndWait()
            
            logger.info(f"✅ Fallback pyttsx3: {speaker} - {len(clean_text)} chars")
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Advanced text cleaning for highly humanized TTS pronunciation"""
        # Remove markdown and special formatting
        clean_text = text.replace('**', '').replace('*', '')
        clean_text = clean_text.replace('[Source', '. Source')
        clean_text = clean_text.replace(']', '.')
        
        # Handle conversational markers and natural speech patterns
        clean_text = clean_text.replace('...', ', ')  # Convert ellipses to natural pauses
        clean_text = clean_text.replace('--', ', ')   # Convert dashes to pauses
        clean_text = clean_text.replace('—', ', ')    # Em-dash to pause
        
        # Add sophisticated natural pauses based on content structure
        clean_text = clean_text.replace('. ', '... ')
        clean_text = clean_text.replace('? ', '? ... ')
        clean_text = clean_text.replace('! ', '! ... ')
        clean_text = clean_text.replace(': ', ':... ')  # Pause after colons
        clean_text = clean_text.replace('; ', ';... ')  # Pause after semicolons
        clean_text = clean_text.replace(', ', ', ')     # Slight pause for commas
        
        # Enhanced technical abbreviations for better pronunciation
        tech_replacements = {
            'AI': 'A.I.', 'ML': 'M.L.', 'NLP': 'N.L.P.', 'API': 'A.P.I.',
            'GPU': 'G.P.U.', 'CPU': 'C.P.U.', 'LLM': 'L.L.M.', 'GPT': 'G.P.T.',
            'CNN': 'C.N.N.', 'RNN': 'R.N.N.', 'GAN': 'G.A.N.', 'VAE': 'V.A.E.',
            'BERT': 'BERT', 'LSTM': 'L.S.T.M.', 'GRU': 'G.R.U.',
            'IoT': 'I.o.T.', 'AR': 'A.R.', 'VR': 'V.R.', 'XR': 'X.R.',
            'AWS': 'A.W.S.', 'GCP': 'G.C.P.', 'SQL': 'S.Q.L.', 'NoSQL': 'No S.Q.L.',
            'HTTP': 'H.T.T.P.', 'HTTPS': 'H.T.T.P.S.', 'REST': 'REST',
            'JSON': 'J.S.O.N.', 'XML': 'X.M.L.', 'CSV': 'C.S.V.',
            'PDF': 'P.D.F.', 'URL': 'U.R.L.', 'UI': 'U.I.', 'UX': 'U.X.'
        }
        
        for abbrev, replacement in tech_replacements.items():
            # Use word boundaries to avoid replacing parts of larger words
            clean_text = re.sub(rf'\b{abbrev}\b', replacement, clean_text)
        
        # Enhanced conversational fillers and transitions for natural flow
        conversational_replacements = {
            'So,': 'So...', 'Well,': 'Well...', 'Now,': 'Now...', 
            'Actually,': 'Actually...', 'Basically,': 'Basically...',
            'However,': 'However...', 'Furthermore,': 'Furthermore...',
            'Moreover,': 'Moreover...', 'Nevertheless,': 'Nevertheless...',
            'In fact,': 'In fact...', 'For instance,': 'For instance...',
            'On the other hand,': 'On the other hand...', 
            'That said,': 'That said...', 'In other words,': 'In other words...'
        }
        
        for phrase, replacement in conversational_replacements.items():
            clean_text = clean_text.replace(phrase, replacement)
        
        # Improve pronunciation of academic and research terms
        academic_replacements = {
            'et al.': 'and colleagues', 'i.e.': 'that is', 'e.g.': 'for example',
            'vs.': 'versus', 'vs': 'versus', 'cf.': 'compare', 'viz.': 'namely',
            'etc.': 'and so on', 'approx.': 'approximately', 'ca.': 'about',
            'Fig.': 'Figure', 'Eq.': 'Equation', 'Ref.': 'Reference',
            'Vol.': 'Volume', 'Ch.': 'Chapter', 'Sec.': 'Section', 'p.': 'page'
        }
        
        for term, replacement in academic_replacements.items():
            clean_text = clean_text.replace(term, replacement)
        
        # Add natural breathing pauses for long sentences
        sentences = clean_text.split('. ')
        enhanced_sentences = []
        
        for sentence in sentences:
            # Add mid-sentence pauses for very long sentences (>20 words)
            words = sentence.split()
            if len(words) > 20:
                # Insert pauses at natural break points
                for i in range(8, len(words)-5, 12):  # Every ~12 words starting at word 8
                    if words[i].endswith(',') or words[i].lower() in ['and', 'but', 'or', 'because', 'since', 'while']:
                        words[i] += '...'
                sentence = ' '.join(words)
            enhanced_sentences.append(sentence)
        
        clean_text = '. '.join(enhanced_sentences)
        
        # Handle numbers for better pronunciation
        clean_text = re.sub(r'(\d+)%', r'\1 percent', clean_text)
        clean_text = re.sub(r'\$(\d+)', r'\1 dollars', clean_text)
        clean_text = re.sub(r'(\d+)x', r'\1 times', clean_text)
        
        # Clean up excessive pauses and formatting
        clean_text = re.sub(r'\.{4,}', '...', clean_text)  # Limit consecutive dots
        clean_text = re.sub(r'\s+', ' ', clean_text)       # Clean up extra spaces
        clean_text = re.sub(r'\.{3}\s*\.{3}', '...', clean_text)  # Remove double ellipses
        
        return clean_text.strip()
    
    async def _create_tone_audio(self, output_path: Path, speaker: str, duration: float):
        """Create actual playable tone-based audio for demo purposes"""
        try:
            import numpy as np
            import wave
            
            sample_rate = 22050
            
            # Different tones for different speakers
            speaker_frequencies = {
                "host1": 440,    # A4 - higher pitch (female)
                "host2": 330,    # E4 - lower pitch (male) 
                "narrator": 385  # G4 - neutral pitch
            }
            
            base_freq = speaker_frequencies.get(speaker, 440)
            
            # Generate audio samples
            samples = int(sample_rate * duration)
            t = np.linspace(0, duration, samples)
            
            # Create a pleasant tone with some modulation
            audio = np.sin(2 * np.pi * base_freq * t) * 0.3
            audio += np.sin(2 * np.pi * base_freq * 1.5 * t) * 0.1  # Harmonic
            
            # Add envelope to avoid clicks
            envelope = np.exp(-t / (duration * 0.8))
            audio *= envelope
            
            # Convert to 16-bit integers
            audio_int = (audio * 32767).astype(np.int16)
            
            # Write WAV file
            with wave.open(str(output_path), 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes per sample
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_int.tobytes())
            
            logger.info(f"🎵 Generated tone audio: {speaker} - {duration:.1f}s at {base_freq}Hz")
            
        except Exception as e:
            logger.error(f"Failed to create tone audio: {e}")
            # Create silent WAV as last resort
            try:
                import wave
                with wave.open(str(output_path), 'w') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(22050)
                    wav_file.writeframes(b'\x00\x00' * int(22050 * max(1.0, duration)))
            except Exception:
                # Create empty file as absolute last resort
                output_path.touch()


class MockTTSEngine:
    """Mock TTS engine for development without real speech"""
    
    def __init__(self, audio_dir: str = "temp/audio"):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock voice configurations
        self.voices = {
            "host1": {
                "name": "Dr. Sarah Chen", 
                "style": "conversational, analytical",
                "pitch": "medium-high",
                "pace": "moderate"
            },
            "host2": {
                "name": "Prof. Mike Rodriguez",
                "style": "engaging, explanatory", 
                "pitch": "medium-low",
                "pace": "slightly slower"
            },
            "narrator": {
                "name": "System Narrator",
                "style": "clear, professional",
                "pitch": "medium", 
                "pace": "moderate"
            }
        }
    
    async def synthesize_segment(self, segment: AudioSegment) -> str:
        """
        Mock TTS synthesis - creates placeholder audio files
        
        Args:
            segment: AudioSegment to synthesize
            
        Returns:
            Path to generated audio file
        """
        # Create mock audio file (silent WAV)
        filename = f"{segment.speaker}_{hash(segment.text[:50])}_{len(segment.text)}.wav"
        output_path = self.audio_dir / filename
        
        # Estimate duration (rough: 150 words per minute)
        word_count = len(segment.text.split())
        estimated_duration = max(1.0, word_count / 2.5)  # seconds
        
        # Create silent audio file as placeholder
        try:
            # Use ffmpeg if available, otherwise create a simple placeholder
            if await self._check_ffmpeg():
                await self._create_silent_audio_ffmpeg(output_path, estimated_duration)
            else:
                await self._create_placeholder_file(output_path, segment, estimated_duration)
            
            segment.audio_path = str(output_path)
            segment.duration = estimated_duration
            
            logger.info(f"🎤 Mock TTS: {segment.speaker} - {len(segment.text)} chars → {estimated_duration:.1f}s")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Mock TTS failed: {e}")
            return None
    
    async def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except:
            return False
    
    async def _create_silent_audio_ffmpeg(self, output_path: Path, duration: float):
        """Create silent audio using ffmpeg"""
        cmd = [
            'ffmpeg', '-y',  # Overwrite output
            '-f', 'lavfi',   # Use lavfi input
            '-i', f'anullsrc=channel_layout=stereo:sample_rate=22050',
            '-t', str(duration),
            '-acodec', 'pcm_s16le',
            str(output_path)
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, 
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
    
    async def _create_placeholder_file(self, output_path: Path, segment: AudioSegment, duration: float):
        """Create a playable audio placeholder when ffmpeg unavailable"""
        metadata = {
            "text": segment.text,
            "speaker": segment.speaker,
            "voice_config": self.voices.get(segment.speaker, {}),
            "estimated_duration": duration,
            "emotion": segment.emotion,
            "note": "This is a mock audio file. Replace with real TTS in production."
        }
        
        # Write as JSON with .wav extension for compatibility
        with open(output_path.with_suffix('.json'), 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create actual playable audio file instead of empty file
        await self._create_tone_audio(output_path, segment.speaker, duration)
    
    async def _create_tone_audio(self, output_path: Path, speaker: str, duration: float):
        """Create actual playable tone-based audio for demo purposes"""
        try:
            import numpy as np
            import wave
            
            sample_rate = 22050
            
            # Different tones for different speakers
            speaker_frequencies = {
                "host1": 440,    # A4 - higher pitch (female)
                "host2": 330,    # E4 - lower pitch (male) 
                "narrator": 385  # G4 - neutral pitch
            }
            
            base_freq = speaker_frequencies.get(speaker, 440)
            
            # Generate audio data
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Create a more natural sounding tone with harmonics
            audio = np.sin(2 * np.pi * base_freq * t) * 0.3
            audio += np.sin(2 * np.pi * base_freq * 1.5 * t) * 0.1  # Harmonic
            audio += np.sin(2 * np.pi * base_freq * 0.5 * t) * 0.05  # Sub-harmonic
            
            # Add some variation to make it less monotonous
            audio *= (1 + 0.1 * np.sin(2 * np.pi * 0.5 * t))  # Amplitude modulation
            audio += 0.02 * np.random.normal(0, 0.1, len(t))    # Slight noise
            
            # Fade in/out to avoid clicks
            fade_samples = int(0.1 * sample_rate)  # 100ms fade
            audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
            audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
            
            # Convert to 16-bit integers
            audio_data = (audio * 32767).astype(np.int16)
            
            # Write WAV file
            with wave.open(str(output_path), 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
                
            logger.info(f"🎵 Generated {duration:.1f}s tone audio for {speaker} at {base_freq}Hz")
            
        except ImportError:
            logger.warning("NumPy not available, creating minimal WAV header")
            await self._create_minimal_wav(output_path, duration)
        except Exception as e:
            logger.error(f"Failed to create tone audio: {e}")
            # Fallback to minimal WAV
            await self._create_minimal_wav(output_path, duration)
    
    async def _create_minimal_wav(self, output_path: Path, duration: float):
        """Create a minimal valid WAV file without NumPy"""
        sample_rate = 22050
        samples = int(sample_rate * duration)
        
        # Create minimal WAV file header + silent audio
        with open(output_path, 'wb') as f:
            # WAV header (44 bytes)
            f.write(b'RIFF')                                    # ChunkID
            f.write((36 + samples * 2).to_bytes(4, 'little'))   # ChunkSize  
            f.write(b'WAVE')                                    # Format
            f.write(b'fmt ')                                    # Subchunk1ID
            f.write((16).to_bytes(4, 'little'))                 # Subchunk1Size
            f.write((1).to_bytes(2, 'little'))                  # AudioFormat (PCM)
            f.write((1).to_bytes(2, 'little'))                  # NumChannels (Mono)
            f.write(sample_rate.to_bytes(4, 'little'))          # SampleRate
            f.write((sample_rate * 2).to_bytes(4, 'little'))    # ByteRate
            f.write((2).to_bytes(2, 'little'))                  # BlockAlign
            f.write((16).to_bytes(2, 'little'))                 # BitsPerSample
            f.write(b'data')                                    # Subchunk2ID
            f.write((samples * 2).to_bytes(4, 'little'))        # Subchunk2Size
            
            # Silent audio data (16-bit, all zeros)
            f.write(b'\x00\x00' * samples)
            
        logger.info(f"🎵 Generated {duration:.1f}s silent WAV file")


class AWSPollyEngine:
    """AWS Polly TTS engine for production"""
    
    def __init__(self):
        self.voices = {
            "host1": {
                "VoiceId": "Joanna",     # US English, conversational
                "Engine": "neural",
                "LanguageCode": "en-US"
            },
            "host2": {
                "VoiceId": "Matthew",    # US English, deeper voice
                "Engine": "neural", 
                "LanguageCode": "en-US"
            },
            "narrator": {
                "VoiceId": "Salli",     # US English, clear
                "Engine": "neural",
                "LanguageCode": "en-US"
            }
        }
    
    async def synthesize_segment(self, segment: AudioSegment) -> str:
        """
        AWS Polly TTS synthesis
        
        Args:
            segment: AudioSegment to synthesize
            
        Returns:
            Path to generated audio file
        """
        try:
            import boto3
            
            polly_client = boto3.client('polly')
            voice_config = self.voices.get(segment.speaker, self.voices["narrator"])
            
            # Add SSML for better control
            ssml_text = self._create_ssml(segment.text, segment.emotion)
            
            response = polly_client.synthesize_speech(
                Text=ssml_text,
                TextType='ssml',
                OutputFormat='mp3',
                **voice_config
            )
            
            # Save audio file
            audio_dir = Path("temp/audio")
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{segment.speaker}_{hash(segment.text[:50])}.mp3"
            output_path = audio_dir / filename
            
            with open(output_path, 'wb') as f:
                f.write(response['AudioStream'].read())
            
            segment.audio_path = str(output_path)
            logger.info(f"🔊 AWS Polly: {segment.speaker} - {len(segment.text)} chars")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ AWS Polly failed: {e}")
            return None
    
    def _create_ssml(self, text: str, emotion: str = "neutral") -> str:
        """Create SSML markup for enhanced speech"""
        # Basic SSML wrapper
        ssml = f'<speak><prosody rate="medium">{text}</prosody></speak>'
        
        # Add emotion-specific adjustments
        if emotion == "excited":
            ssml = f'<speak><prosody rate="fast" pitch="+10%">{text}</prosody></speak>'
        elif emotion == "calm":
            ssml = f'<speak><prosody rate="slow" pitch="-5%">{text}</prosody></speak>'
        elif emotion == "emphasis":
            ssml = f'<speak><prosody volume="loud">{text}</prosody></speak>'
        
        return ssml


class PodcastAudioProducer:
    """Main class for producing podcast audio with humanized conversation styles"""
    
    def __init__(self, use_aws: bool = False, use_real_tts: bool = True, 
                 conversation_style: str = "layperson", use_natural_voices: bool = True,
                 podcast_style: str = None):
        """
        Initialize PodcastAudioProducer with natural voices and conversation styles
        
        Args:
            use_aws: Use AWS Polly instead of local TTS
            use_real_tts: Use real TTS engines instead of mock
            conversation_style: Style for conversation (legacy parameter)
            use_natural_voices: Enable Google TTS + enhanced pyttsx3
            podcast_style: Podcast style (takes priority over conversation_style)
        """
        self.use_aws = use_aws
        self.use_real_tts = use_real_tts
        
        # Support both parameter names for backward compatibility
        style_name = podcast_style if podcast_style is not None else conversation_style
        self.conversation_style = style_name
        self.podcast_style = style_name  # For compatibility with PDF workflow
        self.use_natural_voices = use_natural_voices
        
        logger.info(f"🎤 Initializing PodcastAudioProducer with style: {style_name}")
        logger.info(f"🎵 Natural voices enabled: {use_natural_voices}")
        
        if use_aws:
            self.tts_engine = AWSPollyEngine()
            logger.info("☁️ Using AWS Polly TTS")
        elif use_real_tts:
            # Use our enhanced RealTTSEngine with Google TTS + enhanced pyttsx3 + styles
            self.tts_engine = RealTTSEngine(
                style_name=style_name, 
                use_coqui=use_natural_voices  # This enables Google TTS priority
            )
            logger.info("🎙️ Using RealTTSEngine with natural voices and conversation styles")
        else:
            self.tts_engine = MockTTSEngine()
            logger.info("🎭 Using MockTTSEngine for testing")
        
        self.output_dir = Path("temp/audio/episodes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_available_styles(self) -> List[str]:
        """Get list of available conversation styles"""
        if STYLES_AVAILABLE:
            try:
                return get_available_styles()
            except Exception as e:
                logger.warning(f"Failed to get available styles: {e}")
        return ["layperson", "classroom", "tech_interview", "journal_club", "npr_calm", "news_flash", "tech_energetic", "investigative", "debate_format"]
    
    def set_conversation_style(self, style_name: str) -> bool:
        """Change the conversation style for the TTS engine"""
        try:
            if self.use_real_tts and hasattr(self.tts_engine, 'text_processor'):
                if STYLES_AVAILABLE:
                    self.tts_engine.text_processor = TextProcessor(style_name)
                    self.tts_engine.style_name = style_name
                    self.conversation_style = style_name
                    logger.info(f"✅ Conversation style changed to: {style_name}")
                    return True
                else:
                    logger.warning("Styles system not available")
            else:
                logger.warning("TTS engine does not support style processing")
            return False
        except Exception as e:
            logger.error(f"❌ Failed to set conversation style: {e}")
            return False
    
    async def generate_podcast_audio(self, 
                                   script_segments: List[Dict[str, Any]], 
                                   episode_id: str = None) -> str:
        """
        Generate complete podcast audio from script segments
        
        Args:
            script_segments: List of script segments with speaker and text
            episode_id: Optional episode identifier
            
        Returns:
            Path to final podcast audio file
        """
        if not episode_id:
            # Create a safe hash from script segments
            try:
                segment_texts = [seg.get('text', '')[:50] for seg in script_segments if isinstance(seg, dict)]
                hash_input = ''.join(segment_texts)
                episode_id = f"episode_{abs(hash(hash_input))}"
            except Exception:
                episode_id = f"episode_{len(script_segments)}_{hash('fallback')}"
        
        logger.info(f"🎬 Generating podcast: {episode_id}")
        
        # Debug: Log input data
        logger.info(f"📊 Processing {len(script_segments)} script segments")
        for i, segment in enumerate(script_segments):
            logger.info(f"   Segment {i+1}: {type(segment)} - {str(segment)[:100]}...")
        
        # Convert script to audio segments with enhanced style processing
        audio_segments = []
        for i, segment in enumerate(script_segments):
            if not isinstance(segment, dict):
                logger.error(f"❌ Segment {i} is not a dict: {type(segment)} - {segment}")
                continue
                
            audio_seg = AudioSegment(
                text=segment.get('text', ''),
                speaker=segment.get('speaker', 'narrator'),
                emotion=segment.get('emotion', 'neutral')
            )
            
            # Add style processing attributes if styles system is available
            if STYLES_AVAILABLE and hasattr(self.tts_engine, 'text_processor') and self.tts_engine.text_processor:
                audio_seg.use_style_processing = True
                audio_seg.content_type = segment.get('content_type', 'general')
                audio_seg.interaction_type = segment.get('interaction_type', 'statement')
                
                # Detect content type if not provided
                if audio_seg.content_type == 'general':
                    try:
                        audio_seg.content_type = self.tts_engine.text_processor.analyze_content_type(audio_seg.text)
                    except Exception as e:
                        logger.debug(f"Content type detection failed: {e}")
                        audio_seg.content_type = 'general'
                
                logger.debug(f"✨ Enhanced segment {i+1}: {audio_seg.speaker} - {audio_seg.content_type} ({audio_seg.interaction_type})")
            else:
                audio_seg.use_style_processing = False
            
            audio_segments.append(audio_seg)
        
        # Generate individual audio files
        audio_files = []
        for segment in audio_segments:
            audio_path = await self.tts_engine.synthesize_segment(segment)
            if audio_path:
                audio_files.append(audio_path)
        
        if not audio_files:
            logger.error("❌ No audio segments generated")
            return None
        
        # Combine audio files
        final_audio_path = await self._combine_audio_segments(audio_files, episode_id)
        
        logger.info(f"🎉 Podcast complete: {final_audio_path}")
        return final_audio_path
    
    async def _combine_audio_segments(self, audio_files: List[str], episode_id: str) -> str:
        """Combine multiple audio files into single podcast"""
        output_path = self.output_dir / f"{episode_id}_final.mp3"
        
        try:
            # Try using ffmpeg for proper audio concatenation
            if await self._check_ffmpeg():
                await self._combine_with_ffmpeg(audio_files, output_path)
            else:
                await self._combine_mock_files(audio_files, output_path)
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Audio combination failed: {e}")
            return None
    
    async def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available"""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            return result.returncode == 0
        except:
            return False
    
    async def _combine_with_ffmpeg(self, audio_files: List[str], output_path: Path):
        """Combine audio using ffmpeg"""
        # Create temporary file list for ffmpeg
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for audio_file in audio_files:
                f.write(f"file '{audio_file}'\n")
            filelist_path = f.name
        
        try:
            cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0', 
                '-i', filelist_path,
                '-c', 'copy',
                str(output_path)
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
        finally:
            # Clean up temporary file
            os.unlink(filelist_path)
    
    async def _combine_mock_files(self, audio_files: List[str], output_path: Path):
        """Create properly combined audio file from WAV segments"""
        combined_metadata = {
            "episode_type": "combined_podcast", 
            "segments": [],
            "total_duration": 0,
            "note": "Combined audio from individual WAV segments"
        }
        
        # Collect WAV files and metadata
        wav_files = []
        total_duration = 0
        
        for audio_file in audio_files:
            audio_path = Path(audio_file)
            
            # Add WAV file if it exists and has content
            if audio_path.suffix == '.wav' and audio_path.exists() and audio_path.stat().st_size > 0:
                wav_files.append(str(audio_path))
                
            # Read metadata if available
            if audio_path.suffix == '.json':
                try:
                    with open(audio_file, 'r') as f:
                        segment_data = json.load(f)
                        combined_metadata["segments"].append(segment_data)
                        total_duration += segment_data.get("estimated_duration", 3.0)
                except:
                    pass
        
        combined_metadata["total_duration"] = total_duration
        
        # Write combined metadata
        with open(output_path.with_suffix('.json'), 'w') as f:
            json.dump(combined_metadata, f, indent=2)
        
        # Combine WAV files into MP3
        if wav_files:
            try:
                await self._combine_wav_to_mp3(wav_files, output_path)
                logger.info(f"✅ Combined {len(wav_files)} WAV files into MP3")
            except Exception as e:
                logger.warning(f"⚠️ WAV combination failed: {e}, creating placeholder")
                await self._create_placeholder_mp3(output_path, total_duration)
        else:
            logger.info("🎵 No WAV files found, creating placeholder MP3")
            await self._create_placeholder_mp3(output_path, total_duration)
    
    async def _combine_wav_to_mp3(self, wav_files: List[str], output_path: Path):
        """Combine multiple WAV files into a single audio file"""
        try:
            import numpy as np
            import wave
            
            # Read and combine all WAV files
            combined_audio = []
            sample_rate = 22050
            
            logger.info(f"🔗 Combining {len(wav_files)} WAV files...")
            
            for wav_file in wav_files:
                try:
                    if Path(wav_file).exists() and Path(wav_file).stat().st_size > 0:
                        with wave.open(wav_file, 'rb') as wav:
                            frames = wav.readframes(wav.getnframes())
                            audio_data = np.frombuffer(frames, dtype=np.int16)
                            combined_audio.extend(audio_data)
                            logger.info(f"   ✅ Added {wav_file} ({len(audio_data)} samples)")
                            
                            # Add small silence between segments (0.5 seconds)
                            silence = np.zeros(int(0.5 * sample_rate), dtype=np.int16)
                            combined_audio.extend(silence)
                    else:
                        logger.warning(f"   ⚠️ Skipping empty/missing file: {wav_file}")
                        
                except Exception as e:
                    logger.warning(f"   ❌ Failed to read {wav_file}: {e}")
            
            if combined_audio:
                # Convert to numpy array
                combined_array = np.array(combined_audio, dtype=np.int16)
                logger.info(f"🎵 Combined audio: {len(combined_array)} samples ({len(combined_array)/sample_rate:.1f}s)")
                
                # Create combined WAV file first (always works)
                combined_wav = output_path.with_suffix('.combined.wav')
                with wave.open(str(combined_wav), 'wb') as wav_out:
                    wav_out.setnchannels(1)  # Mono
                    wav_out.setsampwidth(2)  # 16-bit
                    wav_out.setframerate(sample_rate)
                    wav_out.writeframes(combined_array.tobytes())
                
                logger.info(f"✅ Created combined WAV: {combined_wav}")
                
                # Try to create MP3, fallback to copying WAV
                try:
                    # Simple approach: just copy WAV to MP3 extension for compatibility
                    import shutil
                    shutil.copy2(str(combined_wav), str(output_path))
                    logger.info(f"✅ Created MP3 (WAV format): {output_path}")
                    
                    # Keep the WAV version too for compatibility
                    return str(output_path)
                    
                except Exception as e:
                    logger.error(f"Failed to create MP3: {e}")
                    # Just return the WAV path
                    return str(combined_wav)
            else:
                logger.warning("No audio data to combine")
                raise ValueError("No valid audio data found")
                    
        except ImportError:
            logger.warning("NumPy not available for audio combination")
            raise
    
    async def _create_placeholder_mp3(self, output_path: Path, duration: float):
        """Create a placeholder audio file"""
        try:
            # Simple approach: create a basic WAV file and copy to MP3 extension
            import wave
            
            sample_rate = 22050
            samples = int(sample_rate * max(1.0, duration))
            
            # Create simple audio data (sine wave pattern)
            audio_data = []
            for i in range(samples):
                # Simple sine wave at 440Hz
                sample = int(16000 * (i % 1000) / 1000.0)  # Simple sawtooth wave
                audio_data.append(sample)
            
            # Convert to bytes
            audio_bytes = b''.join(sample.to_bytes(2, 'little', signed=True) for sample in audio_data)
            
            # Create WAV file
            temp_wav = output_path.with_suffix('.placeholder.wav')
            with wave.open(str(temp_wav), 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_bytes)
            
            # Copy WAV to MP3 extension (for compatibility)
            import shutil
            shutil.copy2(str(temp_wav), str(output_path))
            
            # Clean up temp file
            temp_wav.unlink()
                
            logger.info(f"🎵 Created placeholder audio: {duration:.1f}s ({output_path.stat().st_size} bytes)")
            
        except Exception as e:
            logger.error(f"Failed to create placeholder audio: {e}")
            # Ultimate fallback: create minimal file with some content
            with open(output_path, 'wb') as f:
                # Write a basic audio file header + some data
                f.write(b'RIFF')
                f.write((1000).to_bytes(4, 'little'))
                f.write(b'WAVE')
                f.write(b'fmt ')
                f.write((16).to_bytes(4, 'little'))
                f.write(b'\x01\x00\x01\x00\x44\xAC\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00')
                f.write(b'data')
                f.write((100).to_bytes(4, 'little'))
                f.write(b'\x00' * 100)  # Silent audio data


# Factory function for easy use
def create_audio_producer(use_aws: bool = None, use_real_tts: bool = None, 
                         podcast_style: str = None, use_natural_voices: bool = None) -> PodcastAudioProducer:
    """Create audio producer based on environment with natural voices and styles support"""
    if use_aws is None:
        use_aws = os.getenv('USE_AWS_POLLY', 'false').lower() == 'true'
    
    if use_real_tts is None:
        use_real_tts = os.getenv('USE_REAL_TTS', 'true').lower() == 'true'
    
    if podcast_style is None:
        podcast_style = os.getenv('PODCAST_STYLE', 'layperson')
    
    if use_natural_voices is None:
        use_natural_voices = os.getenv('USE_NATURAL_VOICES', 'true').lower() == 'true'
    
    logger.info(f"🏭 Factory creating audio producer: style={podcast_style}, natural_voices={use_natural_voices}")
    
    return PodcastAudioProducer(
        use_aws=use_aws, 
        use_real_tts=use_real_tts,
        podcast_style=podcast_style,
        use_natural_voices=use_natural_voices
    )


# Demo function
async def demo_audio_generation():
    """Demo the audio generation system"""
    print("🎤 Testing Audio Generation Pipeline")
    
    # Sample podcast script
    script_segments = [
        {
            "speaker": "narrator",
            "text": "Welcome to Paper to Podcast, where we transform cutting-edge research into engaging conversations.",
            "emotion": "professional"
        },
        {
            "speaker": "host1", 
            "text": "Hi, I'm Dr. Sarah Chen, and today we're diving into a fascinating paper about transformer attention mechanisms.",
            "emotion": "conversational"
        },
        {
            "speaker": "host2",
            "text": "And I'm Professor Mike Rodriguez. Sarah, this paper really changed how we think about sequence modeling, didn't it?",
            "emotion": "engaging"
        },
        {
            "speaker": "host1",
            "text": "Absolutely! The key innovation here is that attention mechanisms can completely replace recurrence and convolution in neural networks.",
            "emotion": "excited"
        }
    ]
    
    # Test mock audio generation
    producer = create_audio_producer(use_aws=False)
    audio_path = await producer.generate_podcast_audio(script_segments, "demo_episode")
    
    if audio_path:
        print(f"✅ Mock podcast generated: {audio_path}")
    else:
        print("❌ Audio generation failed")


if __name__ == "__main__":
    asyncio.run(demo_audio_generation())