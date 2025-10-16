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


class MockTTSEngine:
    """Mock TTS engine for development without AWS costs"""
    
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
        """Create a text placeholder when ffmpeg unavailable"""
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
        
        # Create empty .wav file
        output_path.touch()


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
    
    def __init__(self, use_aws: bool = False):
        self.use_aws = use_aws
        
        if use_aws:
            self.tts_engine = AWSPollyEngine()
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
        """Create mock combined audio file"""
        combined_metadata = {
            "episode_type": "combined_podcast",
            "segments": [],
            "total_duration": 0,
            "note": "Mock combined audio. Replace with real audio processing in production."
        }
        
        for audio_file in audio_files:
            if Path(audio_file).suffix == '.json':
                # Read mock metadata
                try:
                    with open(audio_file, 'r') as f:
                        segment_data = json.load(f)
                        combined_metadata["segments"].append(segment_data)
                        combined_metadata["total_duration"] += segment_data.get("estimated_duration", 3.0)
                except:
                    pass
        
        # Write combined metadata
        with open(output_path.with_suffix('.json'), 'w') as f:
            json.dump(combined_metadata, f, indent=2)
        
        # Create empty audio file
        output_path.touch()


# Factory function for easy use
def create_audio_producer(use_aws: bool = None) -> PodcastAudioProducer:
    """Create audio producer based on environment"""
    if use_aws is None:
        use_aws = os.getenv('USE_AWS_POLLY', 'false').lower() == 'true'
    
    return PodcastAudioProducer(use_aws=use_aws)


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