"""
Enhanced Audio Generation Pipeline for Long-Form Podcasts
Coqui-only implementation (uses Coqui Local TTS under the hood)
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


from app.audio_generator import AudioSegment, CoquiLocalTTSEngine


class EnhancedTTSEngine:
    """
    Enhanced TTS engine delegating to Coqui Local TTS (Coqui-only)
    """

    def __init__(self, audio_dir: str = "temp/audio"):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.engine = CoquiLocalTTSEngine()
        # Legacy attributes kept to avoid static analysis errors in removed paths
        self.voices = {}
        self.language = "en"
        logger.info("🎤 Enhanced TTS Engine initialized (Coqui Local)")

    async def synthesize_segment(self, segment: AudioSegment) -> str:
        """Synthesize audio using Coqui Local TTS"""
        try:
            return await self.engine.synthesize_segment(segment)
        except Exception as e:
            logger.error(f"❌ TTS synthesis failed: {e}")
            # Create fallback silent audio
            text_hash = abs(hash(segment.text[:100]))
            filename = f"{segment.speaker}_{text_hash}_{len(segment.text)}.mp3"
            output_path = self.audio_dir / filename
            await self._create_fallback_audio(output_path, segment, 5.0)
            return str(output_path)
    
    async def _synthesize_with_google_tts(self, text: str, speaker: str, output_path: Path):
        """Removed: non-Coqui TTS path"""
        raise RuntimeError("Non-Coqui TTS has been removed")
            
    
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
def create_enhanced_audio_system() -> Tuple[EnhancedTTSEngine, LongFormPodcastProducer]:
    """
    Create enhanced audio system for long-form podcasts
    
    Returns:
        Tuple of (TTS engine, Podcast producer)
    """
    tts_engine = EnhancedTTSEngine()
    podcast_producer = LongFormPodcastProducer(tts_engine)
    
    return tts_engine, podcast_producer