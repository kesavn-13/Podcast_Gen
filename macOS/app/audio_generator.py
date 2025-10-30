"""
Audio Generation Pipeline for Paper→Podcast (macOS Version)
Supports both mock development and real TTS with macOS compatibility
Enhanced with podcast conversation styles
"""
import asyncio
import json
import logging
import os
import subprocess
import tempfile
import wave
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from pydub import AudioSegment as PyDubSegment

# Import styles system
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


class RealTTSEngine:
    """Real TTS engine using pyttsx3 for actual speech synthesis (macOS optimized)"""
    
    def __init__(self, audio_dir: str = "temp/audio", podcast_style: str = None):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize podcast style if available
        self.podcast_style = podcast_style
        self.text_processor = None
        
        if STYLES_AVAILABLE and podcast_style:
            try:
                self.text_processor = TextProcessor(podcast_style)
                logger.info(f"🎙️ Initialized with podcast style: {podcast_style}")
            except Exception as e:
                logger.warning(f"Failed to initialize podcast style '{podcast_style}': {e}")
                logger.info("Falling back to basic audio generation")
        
        # Voice configurations for different speakers (macOS optimized)
        self.voices = {
            "host1": {
                "name": "Dr. Sarah Chen",
                "voice_index": 1,  # Female voice (typically Samantha on macOS)
                "say_voice": "Samantha",
                "rate": 170,       # Words per minute
                "volume": 0.9
            },
            "host2": {
                "name": "Prof. Mike Rodriguez", 
                "voice_index": 0,  # Male voice (use Daniel or Fred if Alex missing)
                "say_voice": "Daniel",
                "rate": 160,       # Slightly slower
                "volume": 0.95
            },
            "narrator": {
                "name": "System Narrator",
                "voice_index": 1,  # Female voice for narrator
                "say_voice": "Moira",
                "rate": 180,       # Slightly faster
                "volume": 0.85
            }
        }
        
        # Update voice configurations based on podcast style
        if self.text_processor:
            self._update_voice_configs_for_style()
    
    def _update_voice_configs_for_style(self):
        """Update voice configurations based on the selected podcast style"""
        try:
            style_config = get_style_config(self.podcast_style)
            host_dynamics = style_config.get("host_dynamics", {})
            
            for speaker, voice_config in self.voices.items():
                if speaker in host_dynamics:
                    host_config = host_dynamics[speaker]
                    # Update speech rate from style
                    voice_config["rate"] = host_config.get("speech_rate", voice_config["rate"])
                    # Store style personality for reference
                    voice_config["personality"] = host_config.get("personality", "neutral")
                    voice_config["role"] = host_config.get("role", "host")
                    
            logger.info(f"✅ Updated voice configs for '{self.podcast_style}' style")
        except Exception as e:
            logger.warning(f"Failed to update voice configs: {e}")
    
    @classmethod
    def with_style(cls, style_name: str, audio_dir: str = "temp/audio"):
        """Factory method to create audio generator with specific podcast style"""
        if not STYLES_AVAILABLE:
            logger.warning("Styles system not available - creating basic audio generator")
            return cls(audio_dir=audio_dir)
        
        available_styles = get_available_styles()
        if style_name not in available_styles:
            raise ValueError(f"Style '{style_name}' not available. Choose from: {', '.join(available_styles)}")
        
        return cls(audio_dir=audio_dir, podcast_style=style_name)
    
    @staticmethod
    def list_available_styles() -> Dict[str, str]:
        """List all available podcast styles"""
        if not STYLES_AVAILABLE:
            return {"basic": "Basic audio generation without conversation styles"}
        
        return list_all_styles()
    
    def get_current_style_info(self) -> Dict[str, Any]:
        """Get information about the current podcast style"""
        if not self.podcast_style or not STYLES_AVAILABLE:
            return {"style": "basic", "description": "Basic audio generation"}
        
        try:
            style_config = get_style_config(self.podcast_style)
            return {
                "style": self.podcast_style,
                "name": style_config.get("name", "Unknown"),
                "description": style_config.get("description", "No description"),
                "use_case": style_config.get("use_case", "General"),
                "hosts": {
                    speaker: {
                        "role": config.get("role", "host"),
                        "personality": config.get("personality", "neutral"),
                        "speech_rate": config.get("speech_rate", 140)
                    }
                    for speaker, config in style_config.get("host_dynamics", {}).items()
                }
            }
        except Exception as e:
            logger.error(f"Error getting style info: {e}")
            return {"style": self.podcast_style, "error": str(e)}
    
    async def synthesize_segment(self, segment: AudioSegment) -> str:
        """
        Real TTS synthesis using pyttsx3 (macOS compatible)
        Enhanced with podcast conversation styles
        
        Args:
            segment: AudioSegment to synthesize
            
        Returns:
            Path to generated audio file
        """
        # Process text through style system if available
        processed_text = segment.text
        if self.text_processor and hasattr(segment, 'use_style_processing') and segment.use_style_processing:
            try:
                # Process text segment for natural conversation
                interactions = self.text_processor.process_text_segment(segment.text, segment.speaker)
                if interactions:
                    # Use the first interaction (primary text) for this segment
                    processed_text = interactions[0]["text"]
                    logger.info(f"🎭 Applied {self.podcast_style} style processing")
            except Exception as e:
                logger.warning(f"Style processing failed, using original text: {e}")
                processed_text = segment.text
        
        # Clean text for TTS
        final_text = self._clean_text_for_tts(processed_text)
        
        filename = f"{segment.speaker}_{hash(final_text[:50])}_{len(final_text)}.mp3"
        output_path = self.audio_dir / filename
        
        try:
            # Use real TTS with macOS say
            await self._synthesize_with_macos_say(final_text, segment.speaker, output_path)
            
            # Calculate actual duration based on text
            word_count = len(final_text.split())
            voice_config = self.voices.get(segment.speaker, self.voices["narrator"])
            estimated_duration = (word_count / voice_config["rate"]) * 60  # Convert to seconds
            
            segment.audio_path = str(output_path)
            segment.duration = estimated_duration
            
            style_info = f" ({self.podcast_style})" if self.podcast_style else ""
            logger.info(f"🎤 Real TTS{style_info}: {segment.speaker} - '{final_text[:50]}...' → {estimated_duration:.1f}s")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Real TTS failed: {e}")
            # Fallback to tone-based audio
            await self._create_tone_audio(output_path, segment.speaker, max(2.0, len(segment.text) / 10))
            return str(output_path)
    
    def process_content_with_style(self, content_segments: List[str]) -> List[AudioSegment]:
        """
        Process content segments using the podcast style to create natural conversation
        
        Args:
            content_segments: List of text content to process
            
        Returns:
            List of AudioSegment objects with conversation flow
        """
        if not self.text_processor:
            logger.info("No style processor available - creating basic segments")
            return [AudioSegment(text=segment, speaker="host1") for segment in content_segments]
        
        try:
            # Process all content through the style system
            all_interactions = self.text_processor.process_full_content(content_segments)
            
            # Convert interactions to AudioSegment objects
            audio_segments = []
            for interaction in all_interactions:
                segment = AudioSegment(
                    text=interaction["text"],
                    speaker=interaction["speaker"],
                    emotion=interaction.get("content_emotion", "neutral")
                )
                # Mark that this segment has been style-processed
                segment.use_style_processing = False  # Already processed
                segment.content_type = interaction.get("content_type", "general")
                segment.interaction_type = interaction.get("type", "primary")
                
                audio_segments.append(segment)
            
            logger.info(f"🎭 Created {len(audio_segments)} conversational segments using '{self.podcast_style}' style")
            return audio_segments
            
        except Exception as e:
            logger.error(f"Style processing failed: {e}")
            logger.info("Falling back to basic segment creation")
            return [AudioSegment(text=segment, speaker="host1") for segment in content_segments]
    
    # async def _synthesize_with_pyttsx3(self, text: str, speaker: str, output_path: Path):
    #     """Synthesize speech using pyttsx3 (macOS compatible)"""
    #     try:
    #         import pyttsx3
            
    #         # macOS-specific TTS setup
    #         try:
    #             import platform
    #             if platform.system() == 'Darwin':  # macOS
    #                 try:
    #                     import objc
    #                     logger.info("✅ macOS TTS dependencies available")
    #                 except ImportError:
    #                     logger.error("❌ macOS TTS setup failed: objc module not found")
    #                     logger.error("💡 Install with: pip3 install pyobjc-framework-Cocoa pyobjc-framework-AVFoundation pyobjc-framework-Speech")
    #                     raise ImportError("objc module required for macOS TTS - run: pip3 install pyobjc-framework-Cocoa pyobjc-framework-AVFoundation")
    #         except Exception as e:
    #             logger.warning(f"macOS TTS setup issue: {e}")
    #             raise
            
    #         # Initialize TTS engine
    #         engine = pyttsx3.init()
            
    #         # Get voice configuration
    #         voice_config = self.voices.get(speaker, self.voices["narrator"])
            
    #         # Get available voices
    #         voices = engine.getProperty('voices')
    #         logger.info(f"🎤 Found {len(voices)} available voices on macOS")
            
    #         # Debug: Log available voices for macOS
    #         for i, voice in enumerate(voices[:5]):  # Show first 5 voices
    #             logger.info(f"   Voice {i}: {voice.name}")
            
    #         # Set voice (try to use different voices for different speakers)
    #         if voices and len(voices) > voice_config["voice_index"]:
    #             selected_voice = voices[voice_config["voice_index"]]
    #             engine.setProperty('voice', selected_voice.id)
    #             logger.info(f"🔊 Selected voice for {speaker}: {selected_voice.name}")
    #         elif voices and len(voices) > 1:
    #             # Fallback: use different voices for different speakers
    #             voice_idx = 1 if speaker == "host1" else 0
    #             voice_idx = min(voice_idx, len(voices) - 1)
    #             selected_voice = voices[voice_idx]
    #             engine.setProperty('voice', selected_voice.id)
    #             logger.info(f"🔊 Fallback voice for {speaker}: {selected_voice.name}")
    #         else:
    #             logger.warning(f"⚠️  Using default voice for {speaker}")
            
    #         # Set speech properties
    #         engine.setProperty('rate', voice_config["rate"])
    #         engine.setProperty('volume', voice_config["volume"])
            
    #         # Clean text for better TTS
    #         clean_text = self._clean_text_for_tts(text)
            
    #         # Generate speech to file
    #         engine.save_to_file(clean_text, str(output_path))
    #         engine.runAndWait()
            
    #         # Cleanup engine
    #         engine.stop()
            
    #         logger.info(f"✅ Generated speech: {speaker} - {len(clean_text)} chars")
            
    #     except ImportError as e:
    #         logger.error(f"❌ TTS dependencies missing: {e}")
    #         logger.error("💡 For macOS, run: pip3 install pyttsx3 pyobjc-framework-Cocoa pyobjc-framework-AVFoundation")
    #         raise
    #     except Exception as e:
    #         logger.error(f"❌ pyttsx3 synthesis failed: {e}")
    #         raise

    

    async def _synthesize_with_macos_say(self, text, speaker, output_path):
        """Call macOS `say` to produce an AIFF file, convert to mp3 with pydub.

        Runs blocking work in threads so it can be awaited from async code.
        """
        aiff_path = str(output_path.with_suffix('.aiff'))
        # pick macOS say voice from config, fall back to Samantha
        voice = self.voices.get(speaker, {}).get('say_voice', 'Samantha')
        cmd = ["say", "-v", voice, "-o", aiff_path, text]

        try:
            logger.info(f"🔊 macOS say voice for {speaker}: {voice}")
            # Run the blocking subprocess in a thread
            await asyncio.to_thread(subprocess.run, cmd, check=True)

            # Convert AIFF -> mp3 using pydub in a thread
            audio = await asyncio.to_thread(PyDubSegment.from_file, aiff_path, 'aiff')
            await asyncio.to_thread(audio.export, str(output_path), format='mp3')

        finally:
            # Remove intermediate file if it exists
            try:
                if os.path.exists(aiff_path):
                    await asyncio.to_thread(os.remove, aiff_path)
            except Exception:
                pass
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for better TTS pronunciation"""
        # Remove markdown and special formatting
        clean_text = text.replace('**', '').replace('*', '')
        clean_text = clean_text.replace('[Source', '. Source')
        clean_text = clean_text.replace(']', '.')
        
        # Add pauses for better flow
        clean_text = clean_text.replace('. ', '. ... ')
        clean_text = clean_text.replace('? ', '? ... ')
        clean_text = clean_text.replace('! ', '! ... ')
        
        # Handle common abbreviations
        clean_text = clean_text.replace('AI', 'A.I.')
        clean_text = clean_text.replace('ML', 'M.L.')
        clean_text = clean_text.replace('NLP', 'N.L.P.')
        
        return clean_text
    
    async def _create_tone_audio(self, output_path: Path, speaker: str, duration: float):
        """Create actual playable tone-based audio for demo purposes (macOS compatible)"""
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
                logger.info(f"🎵 Generated silent audio fallback: {speaker} - {duration:.1f}s")
            except Exception:
                # Create empty file as absolute last resort
                output_path.touch()
                logger.warning(f"⚠️  Created empty file as last resort: {output_path}")


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
        filename = f"{segment.speaker}_{hash(segment.text[:50])}_{len(segment.text)}.mp3"
        output_path = self.audio_dir / filename
        
        # Estimate duration (rough: 150 words per minute)
        word_count = len(segment.text.split())
        estimated_duration = max(1.0, word_count / 2.5)  # seconds
        
        # Create playable audio file as placeholder
        await self._create_tone_audio(output_path, segment.speaker, estimated_duration)
        
        segment.audio_path = str(output_path)
        segment.duration = estimated_duration
        
        logger.info(f"🎤 Mock TTS: {segment.speaker} - {len(segment.text)} chars → {estimated_duration:.1f}s")
        return str(output_path)
    
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
                wav_file.setsampwidth(2)  # 2 bytes per sample
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


class PodcastAudioProducer:
    """Main class for producing podcast audio from segments (macOS optimized)"""
    
    def __init__(self, use_real_tts: bool = True, podcast_style: str = None):
        self.use_real_tts = use_real_tts
        self.podcast_style = podcast_style
        
        if use_real_tts:
            if podcast_style:
                self.tts_engine = RealTTSEngine.with_style(podcast_style)
                logger.info(f"🎤 Using Real TTS Engine with '{podcast_style}' style")
            else:
                self.tts_engine = RealTTSEngine()
                logger.info("🎤 Using Real TTS Engine (basic)")
        else:
            self.tts_engine = MockTTSEngine()
            logger.info("🎵 Using Mock TTS Engine")
        
        self.output_dir = Path("temp/audio/episodes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_podcast_audio(self, 
                                   script_segments: List[Dict[str, Any]], 
                                   episode_id: str = None,
                                   use_conversation_flow: bool = True) -> str:
        """
        Generate complete podcast audio from script segments
        
        Args:
            script_segments: List of script segments with speaker and text
            episode_id: Optional episode identifier
            use_conversation_flow: Whether to use style-based conversation flow
            
        Returns:
            Path to final podcast audio file
        """
        if not episode_id:
            episode_id = f"episode_{len(script_segments)}segments"
        
        logger.info(f"🎬 Generating podcast: {episode_id}")
        logger.info(f"📊 Processing {len(script_segments)} script segments")
        if self.podcast_style:
            logger.info(f"🎭 Using podcast style: {self.podcast_style}")
        
        # Check if speakers are already properly assigned in the script
        has_speaker_assignments = any(
            segment.get('speaker') and segment.get('speaker') != 'auto' 
            for segment in script_segments
        )
        
        # If we have a style and conversation flow is enabled AND no speakers are assigned, process content through styles
        if (hasattr(self.tts_engine, 'process_content_with_style') and 
            use_conversation_flow and 
            not has_speaker_assignments):
            # Extract text content for style processing
            content_texts = [segment.get('text', '') for segment in script_segments]
            
            logger.info("🎭 Processing content through conversation style system...")
            audio_segments = self.tts_engine.process_content_with_style(content_texts)
            
            logger.info(f"✅ Style processing complete: {len(audio_segments)} conversational segments")
        else:
            # Convert script to audio segments directly (preserving existing speaker assignments)
            if has_speaker_assignments:
                logger.info("🎯 Preserving existing AI-generated speaker assignments")
            else:
                logger.info("📝 Converting script segments directly")
            
            audio_segments = []
            for i, segment in enumerate(script_segments):
                try:
                    audio_segment = AudioSegment(
                        text=segment.get('text', ''),
                        speaker=segment.get('speaker', 'narrator'),
                        emotion=segment.get('emotion', 'neutral')
                    )
                    audio_segments.append(audio_segment)
                    logger.info(f"   Segment {i+1}: {audio_segment.speaker} - {len(audio_segment.text)} chars")
                except Exception as e:
                    logger.error(f"❌ Error processing segment {i+1}: {e}")
                    continue
        
        if not audio_segments:
            logger.error("❌ No valid audio segments to process")
            return None
        
        # Generate individual audio files
        audio_files = []
        for i, segment in enumerate(audio_segments):
            try:
                logger.info(f"🎤 Generating audio for segment {i+1}/{len(audio_segments)}: {segment.speaker}")
                audio_path = await self.tts_engine.synthesize_segment(segment)
                if audio_path and os.path.exists(audio_path):
                    audio_files.append(audio_path)
                    logger.info(f"✅ Generated: {os.path.basename(audio_path)}")
                else:
                    logger.warning(f"⚠️  Failed to generate audio for segment {i+1}")
            except Exception as e:
                logger.error(f"❌ Error generating audio for segment {i+1}: {e}")
        
        if not audio_files:
            logger.error("❌ No audio files generated")
            return None
        
        logger.info(f"🎵 Generated {len(audio_files)} audio files, combining...")
        
        # Combine audio files
        final_audio_path = await self._combine_audio_segments(audio_files, episode_id)
        
        if final_audio_path:
            file_size = os.path.getsize(final_audio_path)
            logger.info(f"🎉 Podcast complete: {final_audio_path}")
            logger.info(f"📊 Final size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
        
        return final_audio_path
    
    async def _combine_audio_segments(self, audio_files: List[str], episode_id: str) -> str:
        """Combine multiple audio files into single podcast (macOS compatible)"""
        output_path = self.output_dir / f"{episode_id}_final.mp3"
        
        try:
            # Try to use pydub if available (works well on macOS)
            try:
                from pydub import AudioSegment as PydubSegment
                
                logger.info("🔧 Using pydub for audio combination (recommended for macOS)")
                
                combined = None
                for i, audio_file in enumerate(audio_files):
                    try:
                        # Load audio file
                        if audio_file.endswith('.wav'):
                            segment_audio = PydubSegment.from_wav(audio_file)
                        else:
                            segment_audio = PydubSegment.from_file(audio_file)
                        
                        # Add to combined audio
                        if combined is None:
                            combined = segment_audio
                        else:
                            # Add a small pause between segments
                            pause = PydubSegment.silent(duration=500)  # 0.5s pause
                            combined = combined + pause + segment_audio
                            
                        logger.info(f"   ✅ Added segment {i+1}: {os.path.basename(audio_file)}")
                        
                    except Exception as e:
                        logger.error(f"   ❌ Failed to add segment {i+1}: {e}")
                
                if combined:
                    # Export as MP3
                    combined.export(str(output_path), format="mp3")
                    logger.info(f"✅ Combined audio exported: {output_path}")
                    return str(output_path)
                else:
                    logger.error("❌ No audio segments could be combined")
                    return None
                    
            except ImportError:
                logger.warning("⚠️  pydub not available, using fallback method")
                logger.info("💡 For better macOS audio support, install: pip3 install pydub")
                
                # Fallback: create a simple combined file
                return await self._create_combined_fallback(audio_files, output_path)
            
        except Exception as e:
            logger.error(f"❌ Audio combination failed: {e}")
            return None
    
    async def _create_combined_fallback(self, audio_files: List[str], output_path: Path) -> str:
        """Create a fallback combined audio file"""
        try:
            # Simple concatenation for WAV files
            combined_metadata = {
                "episode_type": "combined_podcast_macos", 
                "segments": [os.path.basename(f) for f in audio_files],
                "total_files": len(audio_files),
                "platform": "macOS",
                "note": "Combined audio from individual segments"
            }
            
            # Write metadata
            with open(output_path.with_suffix('.json'), 'w') as f:
                json.dump(combined_metadata, f, indent=2)
            
            # Create a simple combined file by copying the first audio file
            if audio_files:
                import shutil
                shutil.copy2(audio_files[0], output_path.with_suffix('.wav'))
                logger.info(f"✅ Created fallback combined file: {output_path.with_suffix('.wav')}")
                return str(output_path.with_suffix('.wav'))
            
        except Exception as e:
            logger.error(f"❌ Fallback combination failed: {e}")
        
        return None


# Factory function for easy use (macOS optimized)
def create_audio_producer(use_real_tts: bool = None) -> PodcastAudioProducer:
    """Create audio producer based on environment (macOS optimized)"""
    if use_real_tts is None:
        use_real_tts = os.getenv('USE_REAL_TTS', 'true').lower() == 'true'
    
    return PodcastAudioProducer(use_real_tts=use_real_tts)


# Demo function for macOS testing
async def demo_audio_generation():
    """Demo the audio generation system (macOS version)"""
    print("🍎 Testing macOS Audio Generation Pipeline")
    
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
    
    # Test audio generation
    producer = create_audio_producer(use_real_tts=True)
    audio_path = await producer.generate_podcast_audio(script_segments, "macos_demo_episode")
    
    if audio_path:
        print(f"✅ macOS podcast generated: {audio_path}")
    else:
        print("❌ macOS audio generation failed")


if __name__ == "__main__":
    print("🍎 macOS Audio Generator - Running Demo...")
    asyncio.run(demo_audio_generation())