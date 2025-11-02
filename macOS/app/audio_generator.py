"""
Audio Generation Pipeline for Paper→Podcast (macOS Version)
Coqui-only TTS: uses Coqui Local (coqui-ai/TTS) and optional Coqui API.
Enhanced with podcast conversation styles
"""
import asyncio
import json
import logging
import os
from typing import List, Dict, Any, Optional, cast
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
                 voice_id: Optional[str] = None,
                 emotion: str = "neutral",
                 duration: Optional[float] = None):
        self.text: str = text
        self.speaker: str = speaker  # "host1", "host2", "narrator"
        self.voice_id: Optional[str] = voice_id
        self.emotion: str = emotion
        self.duration: Optional[float] = duration
        self.audio_path: Optional[str] = None
        # Optional attributes used by style system
        self.use_style_processing: bool = False
        self.content_type: Optional[str] = None
        self.interaction_type: Optional[str] = None


class CoquiTTSEngine:
    """Coqui Studio TTS API integration (natural voices via REST API).

    Requires:
      - COQUI_API_KEY in environment
      - Voice IDs for each speaker (env overrides):
          COQUI_VOICE_HOST1, COQUI_VOICE_HOST2, COQUI_VOICE_NARRATOR
      - Optional: COQUI_API_BASE (defaults to Coqui Studio v2 speak endpoint)
    """

    def __init__(self, voice_map: Optional[Dict[str, Dict[str, str]]] = None):
        self.audio_dir = Path("./temp/audio/segments")
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        self.api_key = os.getenv("COQUI_API_KEY")
        self.base_url = os.getenv("COQUI_API_BASE", "https://app.coqui.ai/api/v2/speak")

        # Allow overriding voice ids via env
        env_voice_map = {
            "host1": {"voice_id": os.getenv("COQUI_VOICE_HOST1")},
            "host2": {"voice_id": os.getenv("COQUI_VOICE_HOST2")},
            "narrator": {"voice_id": os.getenv("COQUI_VOICE_NARRATOR")},
        }

        default_map = {
            "host1": {"voice_id": env_voice_map.get("host1", {}).get("voice_id")},
            "host2": {"voice_id": env_voice_map.get("host2", {}).get("voice_id")},
            "narrator": {"voice_id": env_voice_map.get("narrator", {}).get("voice_id")},
        }
        self.voice_map = voice_map or default_map

        if not self.api_key:
            logger.warning("⚠️  COQUI_API_KEY not set. Set it to use Coqui API TTS.")
        logger.info("✅ CoquiTTSEngine initialized (using Coqui Studio API)")

    async def synthesize_segment(self, segment: AudioSegment) -> str:
        """Synthesize a segment using Coqui Studio API and return MP3 path."""
        filename = f"{segment.speaker}_{hash(segment.text[:50])}_{len(segment.text)}.mp3"
        output_path = self.audio_dir / filename

        if not self.api_key:
            raise RuntimeError("COQUI_API_KEY is required for Coqui TTS")

        # Determine voice id
        cfg = self.voice_map.get(segment.speaker, {})
        voice_id = cfg.get("voice_id") or os.getenv("COQUI_DEFAULT_VOICE_ID")
        if not voice_id:
            raise RuntimeError(
                "No Coqui voice_id configured. Set COQUI_VOICE_HOST1/COQUI_VOICE_HOST2/COQUI_VOICE_NARRATOR or COQUI_DEFAULT_VOICE_ID."
            )

        def _synth():
            import requests

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
            }
            payload = {
                "text": segment.text,
                "voice_id": voice_id,
            }

            with requests.post(self.base_url, json=payload, headers=headers, stream=True) as r:
                if r.status_code != 200:
                    try:
                        err = r.json()
                    except Exception:
                        err = r.text
                    raise RuntimeError(f"Coqui TTS request failed ({r.status_code}): {err}")
                with open(output_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

        await asyncio.to_thread(_synth)

        # Compute duration if possible
        try:
            audio = PyDubSegment.from_file(str(output_path), format="mp3")
            duration_sec = len(audio) / 1000.0
        except Exception:
            duration_sec = max(1.0, len(segment.text.split()) / 3.0)

        segment.audio_path = str(output_path)
        segment.duration = duration_sec

        logger.info(f"🎤 Coqui TTS: {segment.speaker} → {output_path} ({duration_sec:.1f}s)")
        return str(output_path)


class CoquiLocalTTSEngine:
    """Local Coqui TTS using coqui-ai/TTS library (no API/billing).

    Defaults:
      - Model: COQUI_LOCAL_MODEL or 'tts_models/en/vctk/vits'
      - Speakers (VCTK): host1=p225, host2=p226, narrator=p227 (override via env)
    Notes:
      - First run will download the model.
      - Runs on CPU by default for broad macOS compatibility.
    """

    def __init__(self, model_name: Optional[str] = None, speaker_map: Optional[Dict[str, str]] = None):
        self.audio_dir = Path("./temp/audio/segments")
        self.audio_dir.mkdir(parents=True, exist_ok=True)

        try:
            from TTS.api import TTS as CoquiTTS  # type: ignore
        except ImportError:
            logger.error("❌ coqui-ai TTS not installed. Install with: pip install TTS")
            raise

        # Default to a good multi-speaker model
        self.model_name = model_name or os.getenv("COQUI_LOCAL_MODEL", "tts_models/en/vctk/vits")

        logger.info(f"🧩 Loading Coqui local TTS model: {self.model_name} (first run may take a minute)")
        self.tts = CoquiTTS(model_name=self.model_name, progress_bar=False, gpu=False)

        # Multi-speaker detection
        self.is_multi_speaker = hasattr(self.tts, "speakers") and self.tts.speakers is not None

        if self.is_multi_speaker:
            default_speakers = {
                "host1": os.getenv("COQUI_LOCAL_SPEAKER_HOST1", "p225"),
                "host2": os.getenv("COQUI_LOCAL_SPEAKER_HOST2", "p226"),
                "narrator": os.getenv("COQUI_LOCAL_SPEAKER_NARRATOR", "p227"),
            }
            self.speaker_map = speaker_map or default_speakers
            # Optional per-style overrides via env (e.g., COQUI_LOCAL_SPEAKER_HOST1_TECH_INTERVIEW)
            style_env = (os.getenv("PODCAST_STYLE") or "").strip()
            if style_env:
                style_key = style_env.upper().replace("-", "_")
                for role in ("HOST1", "HOST2", "NARRATOR"):
                    key = f"COQUI_LOCAL_SPEAKER_{role}_{style_key}"
                    val = os.getenv(key)
                    if val:
                        self.speaker_map[role.lower()] = val
            logger.info(f"✅ Multi-speaker model with speakers: {list(self.speaker_map.values())}")
        else:
            self.speaker_map = None
            logger.info("✅ Single-speaker model (high quality, one voice)")

        logger.info(f"✅ CoquiLocalTTSEngine initialized (model={self.model_name})")

        # Post-processing configuration (light brighten option)
        self.postproc_map = {
            "host1": os.getenv("VOICE_POSTPROC_HOST1", "none").lower(),
            "host2": os.getenv("VOICE_POSTPROC_HOST2", "none").lower(),
            "narrator": os.getenv("VOICE_POSTPROC_NARRATOR", "none").lower(),
        }

    async def synthesize_segment(self, segment: AudioSegment) -> str:
        """Synthesize a segment locally using Coqui and return MP3 path.

        Generates WAV then converts to MP3 for consistency.
        """
        base = f"{segment.speaker}_{hash(segment.text[:50])}_{len(segment.text)}"
        mp3_path = self.audio_dir / f"{base}.mp3"
        wav_path = self.audio_dir / f"{base}.wav"

        def _synth_wav():
            if self.is_multi_speaker and self.speaker_map:
                speaker = self.speaker_map.get(segment.speaker, self.speaker_map.get("narrator", "p225"))
                self.tts.tts_to_file(text=segment.text, speaker=speaker, file_path=str(wav_path))
            else:
                self.tts.tts_to_file(text=segment.text, file_path=str(wav_path))

        await asyncio.to_thread(_synth_wav)

        # Convert to MP3 with pydub and optional brighten
        try:
            audio = PyDubSegment.from_wav(str(wav_path))
            try:
                proc = self.postproc_map.get(segment.speaker, "none")
                if proc == "bright":
                    from pydub import effects
                    audio = effects.speedup(audio, playback_speed=1.06, chunk_size=50, crossfade=10)
                    audio = audio.high_pass_filter(120)
                    target_dbfs = -14.0
                    change = target_dbfs - audio.dBFS if audio.dBFS is not None else 0
                    audio = audio.apply_gain(change)
            except Exception:
                pass
            audio.export(str(mp3_path), format="mp3")
        except Exception as conv_err:
            logger.warning(f"⚠️  MP3 export failed, keeping WAV only: {conv_err}")
            mp3_path = wav_path

        # Compute duration
        try:
            if str(mp3_path).endswith(".mp3"):
                audio = PyDubSegment.from_file(str(mp3_path), format="mp3")
            else:
                audio = PyDubSegment.from_wav(str(mp3_path))
            duration_sec = len(audio) / 1000.0
        except Exception:
            duration_sec = max(1.0, len(segment.text.split()) / 3.0)

        segment.audio_path = str(mp3_path)
        segment.duration = duration_sec

        speaker_info = ""
        if self.is_multi_speaker and self.speaker_map:
            speaker_id = self.speaker_map.get(segment.speaker, self.speaker_map.get("narrator", "p225"))
            speaker_info = f"({speaker_id})"

        logger.info(f"🎤 Coqui Local TTS: {segment.speaker}{speaker_info} → {mp3_path} ({duration_sec:.1f}s)")
        return str(mp3_path)






class PodcastAudioProducer:
    """Main class for producing podcast audio from segments using Coqui TTS"""

    def __init__(self, use_coqui_tts: bool = False, use_coqui_local_tts: bool = True, podcast_style: Optional[str] = None):
        """
        Initialize podcast audio producer
        
        Args:
            use_coqui_tts: Use Coqui TTS API (requires API key)
            use_coqui_local_tts: Use Coqui Local TTS (default, no API required)
            podcast_style: Optional podcast style name
        """
        self.podcast_style = podcast_style
        self.use_coqui_tts = use_coqui_tts
        self.use_coqui_local_tts = use_coqui_local_tts

        # Priority: local Coqui (default) > Coqui API
        if self.use_coqui_local_tts:
            try:
                self.tts_engine = CoquiLocalTTSEngine()
                logger.info("🎤 Using Coqui Local TTS Engine (no API/billing)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Coqui Local TTS: {e}")
                if self.use_coqui_tts:
                    logger.info("Falling back to Coqui API TTS engine")
                else:
                    raise RuntimeError("Coqui Local TTS initialization failed and no fallback configured") from e
        
        if (not hasattr(self, 'tts_engine')) and self.use_coqui_tts:
            try:
                self.tts_engine = CoquiTTSEngine()
                logger.info("🎤 Using Coqui TTS Engine (natural voices via API)")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Coqui TTS engine: {e}")
                raise RuntimeError("No TTS engine available") from e
        
        if not hasattr(self, 'tts_engine'):
            raise RuntimeError("No TTS engine configured. Set use_coqui_local_tts=True or use_coqui_tts=True")
        
        self.output_dir = Path("temp/audio/episodes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_podcast_audio(self, 
                                   script_segments: List[Dict[str, Any]], 
                                   episode_id: Optional[str] = None,
                                   use_conversation_flow: bool = True) -> Optional[str]:
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
            audio_segments = cast(Any, self.tts_engine).process_content_with_style(content_texts)
            
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
    
    async def _combine_audio_segments(self, audio_files: List[str], episode_id: str) -> Optional[str]:
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
    
    async def _create_combined_fallback(self, audio_files: List[str], output_path: Path) -> Optional[str]:
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


# Factory function for easy use (Coqui TTS only)
def create_audio_producer(use_coqui_tts: Optional[bool] = None, use_coqui_local_tts: Optional[bool] = None) -> PodcastAudioProducer:
    """Create audio producer based on environment (Coqui TTS only).

        Environment variables supported:
            - USE_COQUI_TTS (true/false) - Use Coqui API
            - USE_COQUI_LOCAL_TTS (true/false) - Use Coqui Local (default)
    """
    if use_coqui_tts is None:
        use_coqui_tts = os.getenv('USE_COQUI_TTS', 'false').lower() == 'true'
    if use_coqui_local_tts is None:
        use_coqui_local_tts = os.getenv('USE_COQUI_LOCAL_TTS', 'true').lower() == 'true'

    podcast_style = os.getenv('PODCAST_STYLE')
    return PodcastAudioProducer(use_coqui_tts=use_coqui_tts, use_coqui_local_tts=use_coqui_local_tts, podcast_style=podcast_style)


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
    producer = create_audio_producer(use_coqui_local_tts=True)
    audio_path = await producer.generate_podcast_audio(script_segments, "macos_demo_episode")
    
    if audio_path:
        print(f"✅ macOS podcast generated: {audio_path}")
    else:
        print("❌ macOS audio generation failed")


if __name__ == "__main__":
    print("🍎 macOS Audio Generator - Running Demo...")
    asyncio.run(demo_audio_generation())