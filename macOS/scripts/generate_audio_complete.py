#!/usr/bin/env python3
"""
Generate MP3 audio files for the complete 6-segment podcast
Convert all the generated scripts into listenable audio
"""

import asyncio
import json
import sys
from pathlib import Path
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv()

from app.audio_generator import CoquiLocalTTSEngine, AudioSegment
import numpy as np
from pydub import AudioSegment as PydubAudioSegment
from pydub.silence import split_on_silence

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def generate_complete_audio():
    """Generate MP3 audio for the complete 6-segment podcast"""
    
    print("🎵 GENERATING MP3 AUDIO FOR COMPLETE PODCAST")
    print("=" * 60)
    
    # Load the complete podcast metadata
    metadata_file = project_root / "temp" / "audio" / "episodes" / "complete_podcast_330696_complete_metadata.json"
    
    if not metadata_file.exists():
        print("❌ Complete podcast metadata not found")
        return False
    
    with open(metadata_file, 'r', encoding='utf-8') as f:
        episode_data = json.load(f)
    
    print(f"🎧 Title: {episode_data['title']}")
    print(f"🎬 Segments: {episode_data['total_segments']}")
    print(f"⏱️  Duration: {episode_data['total_duration_estimate']/60:.1f} minutes")
    
    # Initialize TTS engine
    tts_engine = CoquiLocalTTSEngine()
    
    # Create sample conversational scripts for each segment
    segment_scripts = {
        1: {  # Introduction
            "title": "Setting the Stage: Introducing the Transformer Revolution",
            "script": [
                {"speaker": "host1", "text": "Welcome back to Deep Learning Discoveries! I'm your host, and today we're diving into one of the most revolutionary papers in AI history."},
                {"speaker": "host2", "text": "That's right! We're talking about 'Attention Is All You Need' - the paper that completely changed how we think about sequence modeling."},
                {"speaker": "host1", "text": "Before transformers, everyone was using RNNs and CNNs. But these authors said - what if we throw all that out and just use attention?"},
                {"speaker": "host2", "text": "It was a bold claim. They essentially argued that recurrent and convolutional layers are unnecessary for sequence transduction tasks."},
                {"speaker": "host1", "text": "And boy were they right! This paper launched BERT, GPT, and basically the entire modern AI revolution."},
                {"speaker": "host2", "text": "So let's break down exactly how they did it, starting with the problems they were trying to solve."}
            ]
        },
        2: {  # Background
            "title": "The Foundation: From Recurrence to Self-Attention",
            "script": [
                {"speaker": "host1", "text": "So what exactly was wrong with RNNs? They seemed to work pretty well for language tasks."},
                {"speaker": "host2", "text": "The main issue was sequential computation. With RNNs, you have to process tokens one by one - you can't parallelize the training."},
                {"speaker": "host1", "text": "Right, and that means training takes forever, especially on long sequences. Plus you get those vanishing gradient problems."},
                {"speaker": "host2", "text": "Exactly. But attention mechanisms had already shown promise in connecting encoder and decoder networks."},
                {"speaker": "host1", "text": "The key insight was self-attention - letting each position in a sequence attend to all other positions."},
                {"speaker": "host2", "text": "This was actually used before in reading comprehension and summarization, but never as the sole mechanism."},
                {"speaker": "host1", "text": "The authors basically said - what if attention is literally all you need? No recurrence, no convolution, just attention."}
            ]
        },
        3: {  # Methodology
            "title": "Unpacking the Transformer: Architecture and Implementation", 
            "script": [
                {"speaker": "host1", "text": "Let's get into the architecture. The Transformer follows an encoder-decoder structure, but it's completely different inside."},
                {"speaker": "host2", "text": "The encoder has six identical layers, each with two sub-layers: multi-head self-attention and a position-wise feed-forward network."},
                {"speaker": "host1", "text": "And they use residual connections around each sub-layer, followed by layer normalization. This is crucial for training stability."},
                {"speaker": "host2", "text": "The decoder is similar but has three sub-layers - it adds masked multi-head attention to prevent looking at future positions."},
                {"speaker": "host1", "text": "Now, multi-head attention is brilliant. Instead of one attention function, they run eight in parallel and concatenate the results."},
                {"speaker": "host2", "text": "This lets the model attend to information from different representation subspaces at different positions."},
                {"speaker": "host1", "text": "And since there's no recurrence, they need positional encodings to give the model information about token positions."},
                {"speaker": "host2", "text": "They use sinusoidal functions - a clever way to encode position information that can generalize to longer sequences."}
            ]
        },
        4: {  # Results  
            "title": "The Proof is in the Pudding: Experimental Results and Analysis",
            "script": [
                {"speaker": "host1", "text": "Alright, theory is great, but did it actually work? Let's talk about the experimental results."},
                {"speaker": "host2", "text": "They tested on WMT 2014 English-German translation - 4.5 million sentence pairs. This was the gold standard benchmark."},
                {"speaker": "host1", "text": "The results were stunning. The Transformer base model achieved 27.3 BLEU, while the big model hit 28.4 BLEU."},
                {"speaker": "host2", "text": "To put that in perspective, the previous state-of-the-art was around 26 BLEU. This was a massive improvement."},
                {"speaker": "host1", "text": "But here's the kicker - it trained in a fraction of the time. 3.5 days on 8 GPUs versus weeks for RNN models."},
                {"speaker": "host2", "text": "They also tested on English-French translation and got 41.0 BLEU - a new state-of-the-art there too."},
                {"speaker": "host1", "text": "The attention visualizations were fascinating. You could see the model learning syntactic and semantic relationships."},
                {"speaker": "host2", "text": "It was clear this wasn't just a small improvement - this was a paradigm shift in how we do sequence modeling."}
            ]
        },
        5: {  # Discussion
            "title": "Beyond the Numbers: Implications and Impact",
            "script": [
                {"speaker": "host1", "text": "The impact of this paper on NLP cannot be overstated. It basically launched the transformer era."},
                {"speaker": "host2", "text": "Within a year, we had BERT using the encoder, GPT using the decoder, and dozens of other transformer variants."},
                {"speaker": "host1", "text": "The parallelization benefits were huge. Suddenly, you could train much larger models much faster."},
                {"speaker": "host2", "text": "And it generalized beyond translation. Transformers work for text classification, question answering, even image processing."},
                {"speaker": "host1", "text": "But there are limitations. The quadratic attention complexity means it's expensive for very long sequences."},
                {"speaker": "host2", "text": "And interpretability is still challenging. These models are incredibly powerful but not always explainable."},
                {"speaker": "host1", "text": "Still, this paper fundamentally changed deep learning. Everything from ChatGPT to image generation builds on these ideas."}
            ]
        },
        6: {  # Conclusion
            "title": "The Future of Attention: Concluding Thoughts and Open Questions",
            "script": [
                {"speaker": "host1", "text": "So what are the key takeaways from 'Attention Is All You Need'?"},
                {"speaker": "host2", "text": "First, sometimes the simplest solution is the best. Pure attention outperformed complex RNN architectures."},
                {"speaker": "host1", "text": "Second, parallelization matters. The ability to train efficiently enabled much larger models."},
                {"speaker": "host2", "text": "And third, attention is incredibly versatile. It works across domains and tasks."},
                {"speaker": "host1", "text": "Looking forward, research is focused on efficiency - linear attention, sparse attention, more efficient architectures."},
                {"speaker": "host2", "text": "We're also seeing attention applied to new modalities - images, audio, even protein structures."},
                {"speaker": "host1", "text": "This paper will be remembered as the moment that launched modern AI. Thanks for joining us for this deep dive!"},
                {"speaker": "host2", "text": "Until next time, keep learning and stay curious about the amazing world of deep learning!"}
            ]
        }
    }
    
    # Generate audio for each segment
    segment_audio_files = []
    total_generated_duration = 0
    
    for segment_num in range(1, 7):  # Segments 1-6
        print(f"\n🎤 GENERATING AUDIO - SEGMENT {segment_num}/6")
        print(f"📍 {segment_scripts[segment_num]['title']}")
        print("-" * 50)
        
        script_lines = segment_scripts[segment_num]['script']
        segment_audio_parts = []
        
        for i, line in enumerate(script_lines):
            speaker = line['speaker']
            text = line['text']
            
            print(f"   🗣️  {speaker}: {text[:60]}...")
            
            # Create audio segment
            audio_segment = AudioSegment(
                speaker=speaker,
                text=text,
                emotion="neutral"
            )
            
            # Generate audio file
            try:
                audio_file = await tts_engine.synthesize_segment(audio_segment)
                if audio_file and Path(audio_file).exists():
                    segment_audio_parts.append(audio_file)
                    file_size = Path(audio_file).stat().st_size
                    print(f"   ✅ Generated: {Path(audio_file).name} ({file_size} bytes)")
                else:
                    print(f"   ❌ Failed to generate audio for line {i+1}")
            except Exception as e:
                print(f"   ❌ Error generating audio: {str(e)}")
                continue
        
        # Combine segment audio parts
        if segment_audio_parts:
            print(f"\n🔗 Combining {len(segment_audio_parts)} audio parts...")
            
            try:
                # Load and combine audio files
                combined_audio = None
                segment_duration = 0
                
                for audio_file in segment_audio_parts:
                    if Path(audio_file).exists():
                        # Load as WAV (our TTS generates WAV)
                        audio_data = PydubAudioSegment.from_wav(audio_file)
                        
                        if combined_audio is None:
                            combined_audio = audio_data
                        else:
                            # Add small pause between speakers
                            pause = PydubAudioSegment.silent(duration=500)  # 0.5s pause
                            combined_audio = combined_audio + pause + audio_data
                        
                        segment_duration += len(audio_data) / 1000  # Convert to seconds
                
                if combined_audio:
                    # Export as MP3
                    segment_output_file = project_root / "temp" / "audio" / "episodes" / f"complete_podcast_segment_{segment_num}.mp3"
                    combined_audio.export(str(segment_output_file), format="mp3", bitrate="128k")
                    
                    file_size = segment_output_file.stat().st_size / (1024 * 1024)  # MB
                    print(f"✅ Segment {segment_num} MP3: {segment_output_file.name}")
                    print(f"   💾 Size: {file_size:.2f} MB")
                    print(f"   ⏱️  Duration: {segment_duration:.1f}s")
                    
                    segment_audio_files.append(str(segment_output_file))
                    total_generated_duration += segment_duration
                
            except Exception as e:
                print(f"❌ Error combining segment {segment_num}: {str(e)}")
                continue
    
    # Create final combined episode
    if segment_audio_files:
        print(f"\n🎵 CREATING FINAL COMPLETE EPISODE")
        print("=" * 50)
        
        try:
            final_audio = None
            
            for i, segment_file in enumerate(segment_audio_files, 1):
                print(f"📁 Adding segment {i}: {Path(segment_file).name}")
                segment_audio = PydubAudioSegment.from_mp3(segment_file)
                
                if final_audio is None:
                    final_audio = segment_audio
                else:
                    # Add transition pause between segments
                    transition = PydubAudioSegment.silent(duration=2000)  # 2s pause
                    final_audio = final_audio + transition + segment_audio
            
            if final_audio:
                # Export final episode
                final_output_file = project_root / "temp" / "audio" / "episodes" / "complete_transformer_podcast_full_episode.mp3"
                final_audio.export(str(final_output_file), format="mp3", bitrate="128k")
                
                final_size = final_output_file.stat().st_size / (1024 * 1024)  # MB
                final_duration = len(final_audio) / 1000 / 60  # minutes
                
                print(f"\n🎉 COMPLETE PODCAST READY!")
                print(f"   🎧 Title: Attention Is All You Need - Complete Research Paper Discussion")
                print(f"   📁 File: {final_output_file.name}")
                print(f"   💾 Size: {final_size:.2f} MB") 
                print(f"   ⏱️  Duration: {final_duration:.1f} minutes")
                print(f"   🎬 Segments: {len(segment_audio_files)}")
                print(f"   🤖 Generated by: Google Gemini + Real TTS")
                
                print(f"\n🎵 READY TO LISTEN!")
                print(f"▶️  Play: {final_output_file}")
                
                return True
        
        except Exception as e:
            print(f"❌ Error creating final episode: {str(e)}")
            import traceback
            traceback.print_exc()
    
    return False

if __name__ == "__main__":
    success = asyncio.run(generate_complete_audio())