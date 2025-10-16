"""
Audio Generation Pipeline for Paper→Podcast
Supports both mock development and AWS Polly production
"""

import os
import asyncio
import tempfile
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import subprocess
import logging

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
    """Real TTS engine using pyttsx3 for actual speech synthesis"""
    
    def __init__(self, audio_dir: str = "temp/audio"):
        self.audio_dir = Path(audio_dir)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Voice configurations for different speakers
        self.voices = {
            "host1": {
                "name": "Dr. Sarah Chen",
                "voice_index": 0,  # Usually female voice
                "rate": 170,       # Words per minute
                "volume": 0.9
            },
            "host2": {
                "name": "Prof. Mike Rodriguez", 
                "voice_index": 1,  # Usually male voice
                "rate": 160,       # Slightly slower
                "volume": 0.95
            },
            "narrator": {
                "name": "System Narrator",
                "voice_index": 0,  # Clear voice
                "rate": 180,       # Slightly faster
                "volume": 0.85
            }
        }
    
    async def synthesize_segment(self, segment: AudioSegment) -> str:
        """
        Real TTS synthesis using pyttsx3
        
        Args:
            segment: AudioSegment to synthesize
            
        Returns:
            Path to generated audio file
        """
        filename = f"{segment.speaker}_{hash(segment.text[:50])}_{len(segment.text)}.wav"
        output_path = self.audio_dir / filename
        
        try:
            # Use real TTS with pyttsx3
            await self._synthesize_with_pyttsx3(segment.text, segment.speaker, output_path)
            
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
    
    async def _synthesize_with_pyttsx3(self, text: str, speaker: str, output_path: Path):
        """Synthesize speech using pyttsx3"""
        try:
            import pyttsx3
            
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
            
            # Set speech properties
            engine.setProperty('rate', voice_config["rate"])
            engine.setProperty('volume', voice_config["volume"])
            
            # Clean text for better TTS
            clean_text = self._clean_text_for_tts(text)
            
            # Generate speech to file
            engine.save_to_file(clean_text, str(output_path))
            engine.runAndWait()
            
            logger.info(f"✅ Generated speech: {speaker} - {len(clean_text)} chars")
            
        except ImportError:
            logger.warning("pyttsx3 not available, falling back to tone generation")
            raise
        except Exception as e:
            logger.error(f"pyttsx3 synthesis failed: {e}")
            raise
    
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
    """Main class for producing podcast audio from segments"""
    
    def __init__(self, use_aws: bool = False, use_real_tts: bool = True):
        self.use_aws = use_aws
        self.use_real_tts = use_real_tts
        
        if use_aws:
            self.tts_engine = AWSPollyEngine()
        elif use_real_tts:
            self.tts_engine = RealTTSEngine()
        else:
            self.tts_engine = MockTTSEngine()
        
        self.output_dir = Path("temp/audio/episodes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
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
            episode_id = f"episode_{hash(str(script_segments))}"
        
        logger.info(f"🎬 Generating podcast: {episode_id}")
        
        # Convert script to audio segments
        audio_segments = []
        for i, segment in enumerate(script_segments):
            audio_seg = AudioSegment(
                text=segment.get('text', ''),
                speaker=segment.get('speaker', 'narrator'),
                emotion=segment.get('emotion', 'neutral')
            )
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
def create_audio_producer(use_aws: bool = None, use_real_tts: bool = None) -> PodcastAudioProducer:
    """Create audio producer based on environment"""
    if use_aws is None:
        use_aws = os.getenv('USE_AWS_POLLY', 'false').lower() == 'true'
    
    if use_real_tts is None:
        use_real_tts = os.getenv('USE_REAL_TTS', 'true').lower() == 'true'
    
    return PodcastAudioProducer(use_aws=use_aws, use_real_tts=use_real_tts)


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