# How It Works: A Simple Explanation

This project is a **Multilingual Audio Scene Generator**. Think of it as an automatic audio-book director. You can give it a short prompt or a full text script, and it gives you back a fully produced audio track with voices, emotions, background sounds, and an optional music bed.

### The 5 Steps

1. **The Writer (LLM Story Generator)**: If you only have an idea, you can type a short prompt. The system uses Groq (an AI) to automatically write a formatted script with characters, emotions, and settings.
2. **The Reader & Translator (Parser)**: The system reads the script to figure out who is speaking, their emotion, and the background setting. If you requested a specific language (English, Hindi, or Kannada), the system will seamlessly translate the dialogue into that language using AI. You can also manually override the background scene!
3. **The Synthetic Voices (TTS & Emotion)**: We use Meta's MMS models to read the lines in English, Hindi, or Kannada. To add life, the system uses digital signal processing (DSP) to adjust speed, pitch, and tone, simulating emotions (like happy, angry, sad) and distinguishing genders.
4. **The Foley Artist & Musician (Ambient Sounds)**: The system grabs a matching real-world background effect from the **ESC-50 Dataset** (like rain, footsteps, or wind). It also selects an optional royalty-free music bed that fits the dominant emotion of the scene.
5. **The Audio Engineer (Mixer)**: Finally, the system stitches the voices together, layering them over the ambient sound and music. Whenever a character speaks, it automatically lowers the background volume (a technique called "ducking") so the dialogue is always clear.

### Audio Assets
*   **ESC-50**: Provides background sound effects.
*   **Music Bed**: Royalty-free tracks mapped to emotions (calm, happy, sad, tense).
*   **MMS-TTS**: The base multilingual speech models.

---

### How to Run It Quickly
1. Open PowerShell and go to your project folder.
2. Activate the environment: `.\venv\Scripts\Activate.ps1`
3. Start the app: `python app.py`
4. Open the web link it gives you. You can either type a story prompt for the AI to generate, or manually write a script, and hit Generate!
