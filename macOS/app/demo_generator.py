"""
Demo Video Generation for Hackathon Submission
Creates screen recording + audio narration for 3-minute demo
"""

import asyncio
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DemoVideoScript:
    """Manages the hackathon demo video script and timing"""
    
    def __init__(self):
        self.total_duration = 180  # 3 minutes max
        self.segments = self._create_demo_script()
    
    def _create_demo_script(self) -> List[Dict[str, Any]]:
        """Create the demo script with timing"""
        return [
            {
                "timestamp": "0:00-0:30",
                "duration": 30,
                "type": "introduction",
                "visuals": "Project title + team info",
                "narration": """
                Welcome to Paper→Podcast: an agentic AI system that transforms dense research papers 
                into engaging, fact-checked podcast episodes. Built for the AWS & NVIDIA Hackathon 
                using llama-3.1-nemotron-nano-8B-v1 and Retrieval NIM on AWS SageMaker.
                """,
                "screen_actions": [
                    "Show project README",
                    "Highlight NVIDIA NIM integration", 
                    "Show AWS architecture diagram"
                ]
            },
            {
                "timestamp": "0:30-1:00", 
                "duration": 30,
                "type": "paper_upload",
                "visuals": "Streamlit UI - paper upload",
                "narration": """
                Let's see it in action. I'm uploading a research paper about transformer attention mechanisms.
                Watch as our system automatically parses the content, extracts key concepts, and builds 
                a retrieval index for fact-checking.
                """,
                "screen_actions": [
                    "Open Streamlit interface",
                    "Drag and drop PDF file",
                    "Show parsing progress",
                    "Display extracted concepts"
                ]
            },
            {
                "timestamp": "1:00-2:00",
                "duration": 60, 
                "type": "agentic_workflow",
                "visuals": "Backend logs + agent state machine",
                "narration": """
                Now the magic happens. Our agentic system uses multiple specialized AI agents that collaborate 
                to create the podcast. First, the Outline Agent uses RAG retrieval to structure the episode.
                Then the Script Agent writes conversational dialogue, while the Fact-Checker Agent verifies 
                every claim against the source material. Finally, the Rewriter Agent polishes the content 
                for clarity and engagement. Notice how each agent uses NVIDIA's llama-nemotron model for 
                reasoning and the Retrieval NIM for grounding in source facts.
                """,
                "screen_actions": [
                    "Show agent state machine diagram",
                    "Display RAG retrieval results", 
                    "Show fact-checking verification",
                    "Highlight NVIDIA NIM API calls",
                    "Show style adaptation process"
                ]
            },
            {
                "timestamp": "2:00-2:30",
                "duration": 30,
                "type": "generated_output", 
                "visuals": "Generated podcast + audio waveform",
                "narration": """
                The result: a professionally structured podcast episode with two AI hosts discussing 
                the transformer architecture. Every technical claim is verified and cited. The conversation 
                flows naturally while maintaining academic rigor. Let's listen to a sample.
                """,
                "screen_actions": [
                    "Show generated script",
                    "Play audio sample (10 seconds)",
                    "Display fact-check results",
                    "Show citation links"
                ]
            },
            {
                "timestamp": "2:30-3:00",
                "duration": 30,
                "type": "architecture_closing",
                "visuals": "AWS + NVIDIA architecture", 
                "narration": """
                This demonstrates true agentic AI: autonomous agents collaborating, making decisions, 
                and verifying their own work. Built on AWS SageMaker with NVIDIA NIM for production 
                scalability. Our solution solves the real problem of research accessibility while 
                preventing AI hallucinations through systematic verification. Thank you!
                """,
                "screen_actions": [
                    "Show full architecture diagram",
                    "Highlight agentic workflow",
                    "Display AWS SageMaker endpoints", 
                    "Show team contact info"
                ]
            }
        ]


class DemoVideoProducer:
    """Produces the demo video for hackathon submission"""
    
    def __init__(self):
        self.script = DemoVideoScript()
        self.output_dir = Path("demo")
        self.output_dir.mkdir(exist_ok=True)
    
    async def create_demo_video(self) -> str:
        """Create the complete demo video"""
        logger.info("🎬 Creating hackathon demo video")
        
        # Generate narration audio
        narration_file = await self._generate_narration_audio()
        
        # Create screen recording script
        recording_script = await self._create_recording_script()
        
        # Generate final instructions
        instructions_file = await self._create_demo_instructions()
        
        logger.info(f"✅ Demo video assets created in {self.output_dir}")
        return str(instructions_file)
    
    async def _generate_narration_audio(self) -> str:
        """Generate narration audio for the demo"""
        from app.audio_generator import create_audio_producer
        
        # Create narration segments
        narration_segments = []
        for segment in self.script.segments:
            narration_segments.append({
                "speaker": "narrator",
                "text": segment["narration"].strip(),
                "emotion": "professional"
            })
        
        # Generate audio
        audio_producer = create_audio_producer(use_aws=False)  # Use mock for now
        narration_file = await audio_producer.generate_podcast_audio(
            narration_segments, 
            "demo_narration"
        )
        
        return narration_file
    
    async def _create_recording_script(self) -> str:
        """Create detailed screen recording script"""
        script_path = self.output_dir / "recording_script.md"
        
        content = """# Demo Video Recording Script

## 🎯 **Target: Under 3 Minutes**

### Equipment Setup:
- Screen recording software (OBS Studio recommended)
- Good microphone for live narration 
- Multiple browser tabs pre-loaded
- Demo environment running locally

### Pre-Recording Checklist:
- [ ] Start FastAPI backend: `python -m uvicorn app.main:app --reload`
- [ ] Start Streamlit frontend: `streamlit run app/frontend.py` 
- [ ] Load sample paper: `samples/papers/transformer_attention.txt`
- [ ] Test complete workflow once
- [ ] Clear any previous demo data
- [ ] Close unnecessary applications

---

"""
        
        for i, segment in enumerate(self.script.segments, 1):
            content += f"""
## Segment {i}: {segment['type'].title().replace('_', ' ')} ({segment['timestamp']})

**Duration:** {segment['duration']} seconds

**Visuals:** {segment['visuals']}

**Narration Script:**
> {segment['narration'].strip()}

**Screen Actions:**
"""
            for action in segment['screen_actions']:
                content += f"- {action}\n"
            
            content += "\n**Timing Notes:**\n"
            content += f"- Keep this segment to exactly {segment['duration']} seconds\n"
            content += f"- Transition smoothly to next segment\n\n"
            content += "---\n"
        
        content += """

## 🎬 **Recording Tips:**

1. **Practice First:** Do a full run-through without recording
2. **Speak Clearly:** Enunciate technical terms carefully  
3. **Match Timing:** Use a timer to stay within segment limits
4. **Show, Don't Tell:** Let the visuals demonstrate functionality
5. **Smooth Transitions:** Plan transitions between segments

## 🚀 **Post-Production:**

1. **Trim to 3 minutes max**
2. **Add captions for accessibility** 
3. **Include team/contact info in final frame**
4. **Export as MP4 (1080p recommended)**
5. **Test playback before submission**

## 📋 **Backup Plan (If Live Demo Fails):**

Have pre-recorded screenshots showing:
- Successful paper upload
- Agent workflow logs  
- Generated podcast output
- Fact-checking results

This ensures you can still demonstrate functionality even if technical issues occur during recording.
"""
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(script_path)
    
    async def _create_demo_instructions(self) -> str:
        """Create comprehensive demo instructions"""
        instructions_path = self.output_dir / "DEMO_INSTRUCTIONS.md"
        
        content = """# 🏆 Hackathon Demo Instructions

## 🎯 **Goal: 3-Minute Demo Video**

Show judges how Paper→Podcast transforms research papers into verified podcasts using agentic AI.

## 🚀 **Quick Demo Setup (5 minutes)**

### 1. Start the System
```bash
# Terminal 1: Backend
cd Podcast_Gen
python -m uvicorn app.main:app --reload

# Terminal 2: Frontend  
streamlit run app/frontend.py

# Terminal 3: Test the RAG system
python scripts/test_rag_system.py
```

### 2. Pre-load Demo Content
- Browser tab 1: `http://localhost:8501` (Streamlit UI)
- Browser tab 2: `http://localhost:8000/docs` (FastAPI docs)
- Browser tab 3: Project README on GitHub
- Have `samples/papers/transformer_attention.txt` ready

### 3. Demo Flow (Follow narration script)
1. **[0-30s]** Show project overview and architecture
2. **[30-60s]** Upload paper and show parsing
3. **[60-120s]** Demonstrate agentic workflow  
4. **[120-150s]** Present generated podcast
5. **[150-180s]** Highlight AWS + NVIDIA integration

## 🎤 **Audio Options**

### Option A: Live Narration
- Record screen and speak the narration live
- More natural but requires good microphone
- Practice timing with script

### Option B: Pre-recorded Audio  
- Generate narration using our TTS system
- Overlay on screen recording in post-production
- More consistent timing

## 📹 **Recording Setup**

### Recommended Tools:
- **OBS Studio** (free screen recording)
- **Loom** (easy browser-based recording)
- **Zoom** (familiar interface, good quality)

### Settings:
- Resolution: 1080p (1920x1080)
- Frame rate: 30fps  
- Audio: 44.1kHz if recording live narration
- Format: MP4 for compatibility

## 🏆 **Judging Criteria Focus**

Make sure to highlight:

1. **Technological Implementation** (25%)
   - NVIDIA NIM integration (llama-3.1-nemotron-nano-8B-v1)
   - AWS SageMaker deployment readiness
   - Agentic behavior with multiple agents

2. **Design** (25%)  
   - Clean Streamlit interface
   - Intuitive workflow
   - Professional podcast output

3. **Potential Impact** (25%)
   - Solves real research accessibility problem
   - Prevents AI hallucinations through verification
   - Scalable to different audiences

4. **Quality of Idea** (25%)
   - Novel agentic approach
   - Practical application
   - Technical innovation

## ⚡ **Demo Script Key Points**

### Must-Show Features:
- ✅ Paper upload and parsing
- ✅ RAG retrieval with source grounding  
- ✅ Multi-agent collaboration
- ✅ Fact-checking verification loops
- ✅ Style-adapted conversation generation
- ✅ AWS + NVIDIA architecture

### Technical Highlights:
- ✅ llama-3.1-nemotron-nano-8B-v1 for reasoning
- ✅ Retrieval Embedding NIM for RAG
- ✅ SageMaker endpoint deployment
- ✅ Agentic state machine
- ✅ Source citation preservation

## 🚨 **Troubleshooting**

### If Demo Environment Fails:
1. Use pre-recorded screenshots 
2. Show logs/terminal output
3. Explain what would happen
4. Focus on architecture and innovation

### If Audio Generation Fails:
1. Show the generated text script
2. Explain TTS integration 
3. Play sample audio from `samples/`
4. Highlight AWS Polly integration

## 📤 **Submission Checklist**

- [ ] Demo video (under 3 minutes, MP4 format)
- [ ] Public GitHub repository with README
- [ ] Deployment instructions in README
- [ ] Text description of features and functionality
- [ ] All code committed and pushed

## 🎉 **Success Metrics**

A great demo will show:
1. **Problem → Solution** clear narrative
2. **Live functionality** actually working  
3. **Agentic behavior** agents making decisions
4. **Technical depth** without losing audience
5. **Professional presentation** within time limit

**Remember:** Judges want to see innovation + execution + impact. Your agentic verification approach is unique and addresses a real problem!
"""
        
        with open(instructions_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(instructions_path)


# Demo generator function
async def generate_demo_assets():
    """Generate all demo video assets"""
    producer = DemoVideoProducer()
    instructions_file = await producer.create_demo_video()
    print(f"📹 Demo assets created! Check: {instructions_file}")


if __name__ == "__main__":
    asyncio.run(generate_demo_assets())