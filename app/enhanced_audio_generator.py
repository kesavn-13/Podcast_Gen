"""
Enhanced Audio Generation Pipeline for Long-Form Podcasts
Supports Google TTS and extended episode creation
"""

import os
import asyncio
import tempfile
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import subprocess
import logging
from pydub import AudioSegment as PyDubSegment
from pydub.silence import split_on_silence
import io

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


class EnhancedTTSEngine:
    """
    Enhanced TTS engine supporting both Google TTS and pyttsx3
    Optimized for long-form podcast generation
    """
    
    def __init__(self, 
                 audio_dir: str = "temp/audio",
                 use_google_tts: bool = True,
                 language: str = "en"):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.use_google_tts = use_google_tts
        self.language = language
        
        # Enhanced voice configurations for different speakers
        self.voices = {
            "host1": {
                "name": "Dr. Sarah Chen",
                "tld": "com.au",  # Australian accent for Google TTS
                "pyttsx3_index": 0,
                "rate": 170,
                "volume": 0.9,
                "personality": "curious, analytical",
                "google_slow": False
            },
            "host2": {
                "name": "Prof. Mike Rodriguez", 
                "tld": "com",  # US accent for Google TTS
                "pyttsx3_index": 1,
                "rate": 160,
                "volume": 0.95,
                "personality": "enthusiastic, explanatory",
                "google_slow": False
            },
            "narrator": {
                "name": "System Narrator",
                "tld": "co.uk",  # British accent for Google TTS
                "pyttsx3_index": 0,
                "rate": 180,
                "volume": 0.85,
                "personality": "clear, professional",
                "google_slow": True
            }
        }
        
        logger.info(f"🎤 Enhanced TTS Engine initialized (Google TTS: {use_google_tts})")
    
    async def synthesize_segment(self, segment: AudioSegment) -> str:
        """
        Enhanced TTS synthesis with better quality and longer content support
        
        Args:
            segment: AudioSegment to synthesize
            
        Returns:
            Path to generated audio file
        """
        # Create unique filename
        text_hash = abs(hash(segment.text[:100]))
        filename = f"{segment.speaker}_{text_hash}_{len(segment.text)}.mp3"
        output_path = self.audio_dir / filename
        
        try:
            if self.use_google_tts:
                await self._synthesize_with_google_tts(segment.text, segment.speaker, output_path)
            else:
                await self._synthesize_with_pyttsx3(segment.text, segment.speaker, output_path)
            
            # Calculate duration and update segment
            audio_duration = self._get_audio_duration(output_path)
            segment.audio_path = str(output_path)
            segment.duration = audio_duration
            
            logger.info(f"🎤 TTS Complete: {segment.speaker} - {len(segment.text)} chars → {audio_duration:.1f}s")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ TTS synthesis failed: {e}")
            # Create fallback silent audio
            await self._create_fallback_audio(output_path, segment, 5.0)
            return str(output_path)
    
    async def _synthesize_with_google_tts(self, text: str, speaker: str, output_path: Path):
        """Synthesize speech using Google Text-to-Speech"""
        try:
            from gtts import gTTS
            
            voice_config = self.voices.get(speaker, self.voices["narrator"])
            clean_text = self._clean_text_for_tts(text)
            
            # Split long text into chunks to avoid Google TTS limits
            chunks = self._split_text_into_chunks(clean_text, max_chars=5000)
            audio_segments = []
            
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                # Create TTS for chunk
                tts = gTTS(
                    text=chunk,
                    lang=self.language,
                    tld=voice_config["tld"],
                    slow=voice_config.get("google_slow", False)
                )
                
                # Save to temporary file
                chunk_path = output_path.parent / f"temp_chunk_{i}.mp3"
                tts.save(str(chunk_path))
                
                # Load audio segment
                audio_segment = PyDubSegment.from_mp3(str(chunk_path))
                audio_segments.append(audio_segment)
                
                # Clean up temp file
                chunk_path.unlink(missing_ok=True)
            
            # Combine all chunks with brief pauses
            if audio_segments:
                combined_audio = audio_segments[0]
                for segment in audio_segments[1:]:
                    # Add brief pause between chunks
                    pause = PyDubSegment.silent(duration=300)  # 300ms pause
                    combined_audio += pause + segment
                
                # Export final audio
                combined_audio.export(str(output_path), format="mp3")
            
            logger.info(f"✅ Google TTS: {speaker} - {len(chunks)} chunks combined")
            
        except ImportError:
            logger.warning("gtts not available, falling back to pyttsx3")
            await self._synthesize_with_pyttsx3(text, speaker, output_path)
        except Exception as e:
            logger.error(f"Google TTS synthesis failed: {e}")
            raise
    
    async def _synthesize_with_pyttsx3(self, text: str, speaker: str, output_path: Path):
        """Synthesize speech using pyttsx3 as fallback"""
        try:
            import pyttsx3
            
            # Initialize TTS engine
            engine = pyttsx3.init()
            voice_config = self.voices.get(speaker, self.voices["narrator"])
            
            # Configure voice
            voices = engine.getProperty('voices')
            if voices and len(voices) > voice_config["pyttsx3_index"]:
                engine.setProperty('voice', voices[voice_config["pyttsx3_index"]].id)
            
            engine.setProperty('rate', voice_config["rate"])
            engine.setProperty('volume', voice_config["volume"])
            
            # Clean and process text
            clean_text = self._clean_text_for_tts(text)
            
            # For long text, split into smaller segments to avoid memory issues
            chunks = self._split_text_into_chunks(clean_text, max_chars=1000)
            temp_files = []
            
            for i, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                chunk_path = output_path.parent / f"pyttsx3_chunk_{i}.wav"
                engine.save_to_file(chunk, str(chunk_path))
                engine.runAndWait()
                temp_files.append(chunk_path)
            
            # Combine WAV files into MP3
            if temp_files:
                await self._combine_audio_files(temp_files, output_path)
            
            # Clean up temporary files
            for temp_file in temp_files:
                temp_file.unlink(missing_ok=True)
            
        except ImportError:
            logger.warning("pyttsx3 not available")
            raise
    
    def _split_text_into_chunks(self, text: str, max_chars: int = 5000) -> List[str]:
        """Split long text into manageable chunks for TTS"""
        if len(text) <= max_chars:
            return [text]
        
        chunks = []
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_chars:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Enhanced text cleaning for better TTS pronunciation"""
        # Remove markdown and special formatting
        clean_text = text.replace('**', '').replace('*', '')
        clean_text = clean_text.replace('[Source', '. Source')
        clean_text = clean_text.replace(']', '.')
        
        # Handle technical terms
        replacements = {
            'AI': 'Artificial Intelligence',
            'ML': 'Machine Learning',
            'NLP': 'Natural Language Processing',
            'CNN': 'Convolutional Neural Network',
            'RNN': 'Recurrent Neural Network',
            'GPU': 'Graphics Processing Unit',
            'API': 'Application Programming Interface',
            'HTTP': 'H-T-T-P',
            'URL': 'U-R-L',
            'JSON': 'Jason format',
            'XML': 'X-M-L',
            'SQL': 'S-Q-L',
            'vs.': 'versus',
            'e.g.': 'for example',
            'i.e.': 'that is',
            'etc.': 'and so on'
        }
        
        for abbrev, full_form in replacements.items():
            clean_text = clean_text.replace(abbrev, full_form)
        
        # Add natural pauses
        clean_text = clean_text.replace('. ', '. ')
        clean_text = clean_text.replace('? ', '? ')
        clean_text = clean_text.replace('! ', '! ')
        clean_text = clean_text.replace(', ', ', ')
        
        return clean_text
    
    async def _combine_audio_files(self, audio_files: List[Path], output_path: Path):
        """Combine multiple audio files into one"""
        combined_audio = None
        
        for audio_file in audio_files:
            if audio_file.exists():
                if audio_file.suffix.lower() == '.wav':
                    segment = PyDubSegment.from_wav(str(audio_file))
                else:
                    segment = PyDubSegment.from_file(str(audio_file))
                
                if combined_audio is None:
                    combined_audio = segment
                else:
                    # Add small pause between segments
                    pause = PyDubSegment.silent(duration=200)
                    combined_audio += pause + segment
        
        if combined_audio:
            combined_audio.export(str(output_path), format="mp3")
    
    def _get_audio_duration(self, audio_path: Path) -> float:
        """Get duration of audio file in seconds"""
        try:
            audio = PyDubSegment.from_file(str(audio_path))
            return len(audio) / 1000.0  # Convert milliseconds to seconds
        except:
            return 0.0
    
    async def _create_fallback_audio(self, output_path: Path, segment: AudioSegment, duration: float):
        """Create fallback silent audio with beep"""
        try:
            # Create tone for fallback
            silence = PyDubSegment.silent(duration=int(duration * 1000))
            silence.export(str(output_path), format="mp3")
        except Exception as e:
            logger.error(f"Failed to create fallback audio: {e}")


class LongFormPodcastProducer:
    """
    Producer for creating long-form podcast episodes (15-30 minutes)
    Handles segment generation, audio synthesis, and episode assembly
    """
    
    def __init__(self, 
                 tts_engine: EnhancedTTSEngine,
                 output_dir: str = "temp/audio/episodes"):
        self.tts_engine = tts_engine
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("🎧 Long-form Podcast Producer initialized")
    
    async def create_episode(self, 
                           episode_script: Dict[str, Any],
                           episode_id: str = "episode") -> str:
        """
        Create a complete long-form podcast episode
        
        Args:
            episode_script: Complete episode script with segments
            episode_id: Unique identifier for the episode
            
        Returns:
            Path to final episode audio file
        """
        logger.info(f"🎬 Creating long-form episode: {episode_id}")
        
        # Generate audio for all segments
        segment_files = []
        total_duration = 0
        
        segments = episode_script.get("segments", [])
        
        for i, segment_data in enumerate(segments):
            logger.info(f"🎤 Processing segment {i+1}/{len(segments)}: {segment_data.get('type', 'unknown')}")
            
            # Process dialogue within segment
            segment_audio_files = []
            
            dialogue = segment_data.get("dialogue", [])
            for j, dialogue_item in enumerate(dialogue):
                speaker = dialogue_item.get("speaker", "narrator")
                text = dialogue_item.get("text", "")
                
                if not text.strip():
                    continue
                
                # Create audio segment
                audio_segment = AudioSegment(
                    text=text,
                    speaker=speaker,
                    emotion=dialogue_item.get("emotion", "neutral")
                )
                
                # Synthesize audio
                audio_path = await self.tts_engine.synthesize_segment(audio_segment)
                segment_audio_files.append(audio_path)
                total_duration += audio_segment.duration or 0
            
            # Combine segment audio files
            if segment_audio_files:
                segment_combined_path = await self._combine_segment_audio(
                    segment_audio_files, 
                    f"{episode_id}_segment_{i+1}"
                )
                segment_files.append(segment_combined_path)
        
        # Combine all segments into final episode
        final_episode_path = await self._create_final_episode(
            segment_files, 
            episode_id,
            episode_script
        )
        
        logger.info(f"🎉 Episode complete: {final_episode_path} ({total_duration:.1f}s)")
        return final_episode_path
    
    async def _combine_segment_audio(self, audio_files: List[str], segment_name: str) -> str:
        """Combine audio files for a single segment"""
        output_path = self.output_dir / f"{segment_name}.mp3"
        
        try:
            combined_audio = None
            
            for audio_file in audio_files:
                if not Path(audio_file).exists():
                    continue
                
                audio_segment = PyDubSegment.from_file(audio_file)
                
                if combined_audio is None:
                    combined_audio = audio_segment
                else:
                    # Add natural pause between speakers
                    pause = PyDubSegment.silent(duration=500)  # 500ms pause
                    combined_audio += pause + audio_segment
            
            if combined_audio:
                # Normalize audio levels
                combined_audio = combined_audio.normalize()
                combined_audio.export(str(output_path), format="mp3")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to combine segment audio: {e}")
            return ""
    
    async def _create_final_episode(self, 
                                  segment_files: List[str], 
                                  episode_id: str,
                                  episode_script: Dict[str, Any]) -> str:
        """Create the final combined episode with intro/outro music and effects"""
        output_path = self.output_dir / f"{episode_id}_final.mp3"
        
        try:
            # Load all segments
            episode_audio = None
            
            for i, segment_file in enumerate(segment_files):
                if not segment_file or not Path(segment_file).exists():
                    continue
                
                segment_audio = PyDubSegment.from_file(segment_file)
                
                if episode_audio is None:
                    episode_audio = segment_audio
                else:
                    # Add transition between segments
                    transition = PyDubSegment.silent(duration=1000)  # 1 second pause
                    episode_audio += transition + segment_audio
            
            if episode_audio:
                # Add intro/outro silence for professional feel
                intro_silence = PyDubSegment.silent(duration=2000)  # 2 seconds
                outro_silence = PyDubSegment.silent(duration=3000)  # 3 seconds
                
                final_episode = intro_silence + episode_audio + outro_silence
                
                # Normalize and apply gentle compression
                final_episode = final_episode.normalize()
                
                # Export final episode
                final_episode.export(str(output_path), 
                                   format="mp3", 
                                   bitrate="128k",
                                   tags={
                                       "title": episode_script.get("title", f"Episode {episode_id}"),
                                       "artist": "Paper to Podcast AI",
                                       "album": "Research Insights",
                                       "genre": "Educational"
                                   })
                
                # Get final duration
                duration_minutes = len(final_episode) / (1000 * 60)
                logger.info(f"🎵 Final episode: {duration_minutes:.1f} minutes")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ Failed to create final episode: {e}")
            return ""
    
    async def get_episode_stats(self, episode_path: str) -> Dict[str, Any]:
        """Get statistics about the generated episode"""
        try:
            if not Path(episode_path).exists():
                return {"error": "Episode file not found"}
            
            audio = PyDubSegment.from_file(episode_path)
            
            return {
                "duration_seconds": len(audio) / 1000,
                "duration_minutes": len(audio) / (1000 * 60),
                "file_size_mb": Path(episode_path).stat().st_size / (1024 * 1024),
                "format": "mp3",
                "sample_rate": audio.frame_rate,
                "channels": audio.channels,
                "bitrate": "128k"
            }
            
        except Exception as e:
            return {"error": str(e)}


# Factory function
def create_enhanced_audio_system(use_google_tts: bool = True) -> Tuple[EnhancedTTSEngine, LongFormPodcastProducer]:
    """
    Create enhanced audio system for long-form podcasts
    
    Args:
        use_google_tts: Whether to use Google TTS (better quality) or pyttsx3 (offline)
        
    Returns:
        Tuple of (TTS engine, Podcast producer)
    """
    tts_engine = EnhancedTTSEngine(use_google_tts=use_google_tts)
    podcast_producer = LongFormPodcastProducer(tts_engine)
    
    return tts_engine, podcast_producer