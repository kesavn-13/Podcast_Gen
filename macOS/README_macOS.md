# Podcast Generator - macOS Version

This is the macOS-optimized version of the Podcast Generator with enhanced features including:

## 🎙️ **Complete Podcast Styles System**
- **9 Distinct Styles**: layperson, classroom, tech_interview, journal_club, npr_calm, news_flash, tech_energetic, investigative, debate_format
- **Professional Podcast Structure**: Intros, outros, and ad breaks that adapt to each style
- **Natural Conversation Flow**: Balanced debates, corrections, and authentic human-like dialogue

## 🎧 **macOS TTS Integration**
- **Native macOS Voices**: Samantha (female) and Daniel (male) with style-specific speech rates
- **Style-Aware Audio**: Different energy levels, pacing, and interruption patterns per style
- **Professional Output**: Complete MP3 episodes with seamless audio stitching

## 🚀 **Quick Start**

1. **Setup Environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure API Keys**:
   ```bash
   cp .env.example .env
   # Edit .env with your Google API credentials
   ```

3. **Test Podcast Generation**:
   ```bash
   # Try different styles
   python3 scripts/test_new_pdf_paper_simplified.py --style debate_format
   python3 scripts/test_new_pdf_paper_simplified.py --style npr_calm
   python3 scripts/test_new_pdf_paper_simplified.py --style tech_energetic
   ```

## 🎭 **Available Podcast Styles**

- **`layperson`**: Friendly, accessible discussion for general audiences
- **`classroom`**: Patient, pedagogical teaching style
- **`tech_interview`**: In-depth technical analysis for developers
- **`journal_club`**: Scholarly academic examination with peer review focus
- **`npr_calm`**: Thoughtful, measured NPR-style discussion
- **`news_flash`**: Urgent breaking news coverage
- **`tech_energetic`**: High-energy excitement for tech breakthroughs
- **`investigative`**: Probing analysis with healthy skepticism
- **`debate_format`**: Natural debate with opposition, agreement, and corrections

## 🎵 **Professional Features**

### Podcast Structure
- **Dynamic Intros**: Style-specific introductions that engage the audience
- **Natural Ad Breaks**: Realistic podcast breaks with return teasers
- **Engaging Outros**: Call-to-action and next episode previews

### Conversation Engine
- **Balanced Debates**: Real disagreements with corrections and concessions
- **Natural Language**: Human-like conversation patterns, not AI-sounding
- **Speaker Consistency**: Preserved AI-generated speaker assignments

### Audio Production
- **Professional TTS**: macOS native voices with style-specific settings
- **Seamless Stitching**: Combined audio with proper pacing
- **Quality Output**: Production-ready MP3 files

## 📁 **Project Structure**

```
macOS/
├── app/                     # Core application
│   ├── styles/             # Podcast styles system
│   │   ├── style_definitions.py
│   │   ├── conversation_engine.py
│   │   └── podcast_structure.py
│   └── audio_generator.py  # TTS and audio production
├── scripts/                # Testing and utilities
├── samples/                # Example papers and styles
└── docs/                   # Documentation
```

## 🔧 **Requirements**

- **macOS**: Required for native TTS voices (Samantha, Daniel)
- **Python 3.8+**: Core runtime
- **Google API**: For LLM content generation
- **pydub**: Audio processing and stitching

## 💡 **Usage Examples**

```bash
# Academic journal discussion
python3 scripts/test_new_pdf_paper_simplified.py --style journal_club

# Breaking news coverage
python3 scripts/test_new_pdf_paper_simplified.py --style news_flash

# Heated debate format
python3 scripts/test_new_pdf_paper_simplified.py --style debate_format
```

## 🎯 **Features**

✅ **Complete Podcast Experience**: Professional intro/outro/ad breaks  
✅ **9 Distinct Styles**: Each with unique personality and flow  
✅ **Natural Debates**: Real disagreements with corrections  
✅ **macOS Optimized**: Native TTS voices and audio processing  
✅ **Production Ready**: High-quality MP3 output  
✅ **Extensible**: Easy to add new styles and voices  

---

**Generated on macOS with ❤️ for authentic podcast experiences**
