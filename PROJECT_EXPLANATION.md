# How It Works: A Simple Explanation

This project is a **Multilingual Audio Scene Generator**. Think of it as an automatic audio-book director. You give it a text script, and it gives you back a fully produced audio track with voices, emotions, and background sounds.

### The 4 Steps

1. **The Reader (Parser)**: You type a script. The system uses an AI called Groq to read it. It figures out who is speaking, what emotion they are feeling (happy, angry, sad), and what the background setting is (like a thunderstorm or a cafe).
2. **The Synthetic Voices (TTS & Emotion)**: We use Meta's MMS models to read the lines in English, Hindi, or Kannada. MMS does not natively act emotions or provide separate speakers in this setup, so restrained speed and pitch changes suggest the tagged emotion and distinguish gender variants. These effects improve pacing but do not make the output a human recording.
3. **The Foley Artist (Ambient Sounds)**: The system takes the background setting it found in step 1 and grabs a real-world sound effect from the **ESC-50 Dataset** (a massive library of 2,000 environmental sounds).
4. **The Audio Engineer (Mixer)**: Finally, the system stitches the voices together with short pauses. It plays the background sound underneath. Whenever a character speaks, it automatically lowers the volume of the background sound (a technique called "ducking") so you can hear the voices clearly.

### Audio assets
*   **ESC-50**: Provides background sound effects such as rain, wind, and footsteps after the sound bank is built.
*   **MMS-TTS**: The base multilingual speech models. Separate OpenSLR/LJSpeech fine-tuned checkpoints are not included in this checkout.

---

### How to Run It Quickly
1. Open PowerShell and go to your project folder.
2. Activate the environment: `.\venv\Scripts\Activate.ps1`
3. Start the app: `python app.py`
4. Open the web link it gives you, type a script, and hit Generate!
