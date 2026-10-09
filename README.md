# Multilingual Audio Scene Generator

A fun, automated pipeline that converts text scripts (English, Hindi, Kannada) into an emotional multi-speaker audio scene complete with background sounds and automatic audio ducking!

## Easy Setup

1. **Create and activate a virtual environment**, then install the required packages:
   ```bash
   cd audio-scene
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Download the background sounds** (ESC-50 Dataset):
   ```bash
   python scripts/download_esc50.py
   python ambient/build_bank.py
   ```

3. **Optional: configure Groq** by creating a `.env` file in this folder and adding:
   ```text
   GROQ_API_KEY=your_key_here
   ```
   Without a key, use local parser mode; it works offline and reads the explicit language, background, emotion, and speaker tags in the example scripts.

## Launch the App!

Run this command to open the interactive web UI:
```bash
python app.py
```

## Try the example scripts

The ready-to-run [English example](examples/en.txt), [Hindi example](examples/hi.txt), and [Kannada example](examples/kn.txt) each specify a background sound and an emotion for every speaker. Generate audio from the command line with the local parser:

```bash
python cli.py examples\en.txt --mode local --out output.wav
python cli.py examples\hi.txt --mode local --out output-hi.wav
python cli.py examples\kn.txt --mode local --out output-kn.wav
```

Script format:

```text
Language: en
Background: rain
Maya [fear] [female]: Did you hear that?
Arun [happy] [male]: I'm right here.
```

Supported emotions are `neutral`, `happy`, `sad`, `angry`, `fear`, `surprise`, and `disgust`. Backgrounds must use an ESC-50 label (for example `rain`, `thunderstorm`, or `footsteps`) or a configured synonym. English, Hindi, and Kannada dialogue should be written in their native scripts. The `female` and `male` tags select distinct pitch-shifted variants when both genders use the same base checkpoint; they are not separately recorded actors. MMS does not provide native emotional delivery, so the pipeline uses restrained speed, pitch, and tone effects to suggest emotion.

## How We Trained the Models
*(See `reports/PROJECT_REPORT.md` for the full scientific breakdown).*
This checkout uses Meta's multilingual MMS-TTS checkpoints as its base voices. Emotion and gender differences are approximated with audio processing unless you configure separate fine-tuned checkpoints. ESC-50 supplies background effects; it is not a music library. Treat generated voices as synthetic rather than human recordings.


## Demo
Check out the full demo of the workflow:
[Download/Watch Demo Video](demo_gen/demo.mp4)
