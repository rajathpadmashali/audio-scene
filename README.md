# AudioScene: AI Multilingual Audiobook & Scene Generator

A fully automated, full-stack web application that converts text scripts (English, Hindi, Kannada) into an emotional multi-speaker audio scene complete with background sounds, cinematic themes, and automatic audio ducking!

## Demo
Watch the full demo of the workflow:

<video src="demo_gen/demo.mp4" width="100%" controls autoplay loop></video>

## Features

- **Cinematic Web UI**: A sleek, dark-mode-first interface to explore, create, and share audiobooks.
- **AI Story Generation**: Simply type a prompt (e.g., "A detective questioning a suspect"), pick a theme (Sci-Fi, Horror, Mystery, etc.), and the AI writes the script.
- **Manual Scripting**: Write your own dialogues with explicit character emotions and genders.
- **Animated Audio Player**: Listen to your scenes with a responsive visualizer, bouncing character avatars, and a scrolling teleprompter transcript.
- **Social Features**: Create an account, follow other users, and explore the community feed.
- **Smart Audio Mixing**: Uses Meta's multilingual MMS-TTS checkpoints and ESC-50 background effects. Automatically handles volume ducking (lowering background noise when characters speak).

---

## Complete Setup Guide

Follow these steps to run the entire project locally from scratch.

### 1. Install Dependencies
Ensure you have Python installed, then set up your virtual environment:
```bash
# Clone the repository and enter the directory
git clone https://github.com/your-username/audio-scene.git
cd audio-scene

# Create and activate a virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 2. Download the Ambient Audio Dataset
The project relies on the ESC-50 dataset for background sound effects (rain, thunderstorms, city streets, etc). Run these commands to download and index the audio bank:
```bash
python scripts/download_esc50.py
python ambient/build_bank.py
```

### 3. Configure API Keys
To use the **AI Generated** mode, you need a free Groq API key for the LLaMA-3.1 model. Create a `.env` file in the root directory and add:
```text
GROQ_API_KEY=your_groq_api_key_here
```
*(If you don't provide a key, you can still use the "Write Your Own" manual script mode!)*

### 4. Launch the Web Application!
Start the Flask server to initialize the database and run the interactive UI:
```bash
python server.py
```
Open your browser and navigate to **[http://localhost:5000](http://localhost:5000)** to sign up and start creating!

---

## Advanced: Command Line Interface

If you prefer to generate audio offline without the web UI, you can use the CLI tool with the example scripts provided.

```bash
python cli.py examples\en.txt --mode local --out output-en.wav
python cli.py examples\hi.txt --mode local --out output-hi.wav
python cli.py examples\kn.txt --mode local --out output-kn.wav
```

### Manual Script Format
When writing your own script (either in the Web UI or via text file), use the following syntax:

```text
Language: en
Background: rain
Context: Optional context description
Characters: Maya (female), Arun (male)

Maya [fear]: Did you hear that?
Arun [happy]: I'm right here, don't worry.
```

- **Supported Languages**: `en` (English), `hi` (Hindi), `kn` (Kannada).
- **Supported Emotions**: `neutral`, `happy`, `sad`, `angry`, `fear`, `surprise`, `disgust`.
- **Supported Backgrounds**: Any ESC-50 label (e.g., `rain`, `thunderstorm`, `footsteps`, `wind`).

---

## How It Works Under The Hood
*(See `reports/PROJECT_REPORT.md` for the full scientific breakdown).*
This project utilizes **Meta's MMS-TTS** checkpoints as its base voices. Emotion and gender differences are approximated dynamically with audio processing (pitch shifting and speed adjustment) since MMS does not provide native emotional delivery. Background effects are mapped using the ESC-50 dataset. Treat generated voices as synthetic rather than human recordings.
