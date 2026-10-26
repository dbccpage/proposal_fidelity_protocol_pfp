# Symbol Game Media Suite: Animations & Voiceovers

This directory stores rendered animation keyframe previews, assembled voiceover audio tracks, and instructions for generating full MP4 animation video tracks.

---

## 1. Directory Structure

- `images/`: Rendered keyframe preview PNGs for each of the 5 Manim animation scenes.
- `voiceovers/`: Assembled narration audio tracks (`scene[1-5]_narration.mp3`) synthesized from timestamped transcripts in `scenes/narration/`.
- `videos/`: (Local output directory, git-ignored) Contains rendered MP4 video files multiplexed with audio.

---

## 2. Rendering Animation Video Tracks

To render all 5 scenes to MP4 and multiplex them with the narration audio:

```bash
# Fast draft quality (480p15, renders in ~2 minutes):
python omega_engine_education/scripts/render_all_animations.py --quality l --mux

# High definition (1080p60 for YouTube / production):
python omega_engine_education/scripts/render_all_animations.py --quality h --mux
```

The resulting video files are written to `omega_engine_education/media/videos/`:
- `scene1_with_voiceover.mp4` (State Machine & 3-Cycle Holonomy)
- `scene2_with_voiceover.mp4` ($S(N)$ Tower Construction)
- `scene3_with_voiceover.mp4` (Coboundaries $d^0, d^1$ & Defect Triad $\Phi_1, \Gamma_2$)
- `scene4_with_voiceover.mp4` (Token Manifold Collapse $125 \to 19 \to 1$)
- `scene5_with_voiceover.mp4` (Local Green, Global Red Boundary Conflicts)

---

## 3. Cloning Your Voice for Custom Narration

You do not need to manually record reading all transcripts. You can synthesize the entire script in your own voice using a 15–30 second clean `.wav` recording:

### A. Local Neural Voice Cloning (F5-TTS / Coqui XTTS-v2)
1. Record a 20-second sample of your voice using the included helper script:
   ```bash
   python omega_engine_education/scripts/record_voice_sample.py --output my_voice.wav
   ```
2. Run the renderer with your audio reference:
   ```bash
   python omega_engine_education/scripts/render_all_animations.py --voice-backend f5tts --reference-audio my_voice.wav --quality h --mux
   ```

### B. Cloud API (ElevenLabs)
1. Set your ElevenLabs API key:
   ```bash
   export ELEVEN_API_KEY="your_api_key_here"
   ```
2. Run the renderer:
   ```bash
   python omega_engine_education/scripts/render_all_animations.py --voice-backend elevenlabs --quality h --mux
   ```

### C. Offline Native Synthesis (Windows SAPI5)
Windows built-in speech engine requires zero configuration or API keys:
```bash
python omega_engine_education/scripts/render_all_animations.py --voice-backend sapi5 --quality l --mux
```
