# TTS Improvements - October 31, 2025

## Issues Fixed

### 1. Path Consistency: `tmp_audio` → `temp/audio/segments`
**Problem:** Audio segments were being saved to `./tmp_audio` but the final output went to `temp/audio/episodes`, creating confusion.

**Solution:** All TTS engines now consistently save to `temp/audio/segments/`, keeping everything organized in one place:
- Individual segments: `temp/audio/segments/*.mp3`
- Final combined podcast: `temp/audio/episodes/*_final.mp3`

### 2. Audio Naturalness Improvements
**Problem:** The default VCTK model voices (p225, p231, p240) sounded somewhat synthetic.

**Solution:** Switched to higher-quality models with better configuration:

#### New Default Model
- **tts_models/en/ljspeech/tacotron2-DDC**
  - Single speaker (all hosts use same voice)
  - Very natural-sounding female voice
  - Good for podcast-style content
  - Fast generation

#### Alternative Models (can set in .env)

**For Most Natural Single Voice:**
```bash
COQUI_LOCAL_MODEL=tts_models/en/ljspeech/tacotron2-DDC
```
or
```bash
COQUI_LOCAL_MODEL=tts_models/en/ljspeech/glow-tts  # Faster, still natural
```

**For Multiple Distinct Speakers:**
```bash
COQUI_LOCAL_MODEL=tts_models/en/vctk/vits
COQUI_LOCAL_SPEAKER_HOST1=p225  # Female (clearer)
COQUI_LOCAL_SPEAKER_HOST2=p226  # Male (better than p231)
COQUI_LOCAL_SPEAKER_NARRATOR=p227  # Male narrator
```

## Recommended Setup

### Best Balance (Current Default)
Single speaker with high naturalness - good for educational/explainer podcasts where voice consistency matters more than variety.

### If You Need Distinct Voices
Uncomment these lines in `.env`:
```bash
COQUI_LOCAL_MODEL=tts_models/en/vctk/vits
COQUI_LOCAL_SPEAKER_HOST1=p225
COQUI_LOCAL_SPEAKER_HOST2=p226
COQUI_LOCAL_SPEAKER_NARRATOR=p227
```

## Testing Your Changes

Run the script again to hear the improved audio:
```bash
python3 scripts/test_new_pdf_paper_simplified.py --style layperson
```

The audio will sound more natural now! Output location:
```
temp/audio/episodes/episode_lightendostereo_test_final.mp3
```

## Why This Matters

1. **Professionalism:** Better voices = more engaging podcasts
2. **Consistency:** All audio files in one organized location
3. **Flexibility:** Easy to switch models based on your needs
4. **No Cost:** All models run locally, no API fees


