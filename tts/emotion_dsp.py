import librosa
import numpy as np
import scipy.signal

# ────────────────────────────────────────────────────────────────────
# Emotion presets
# ────────────────────────────────────────────────────────────────────
# Rates kept close to 1.0 to minimize time-stretch robotic artifacts
EMOTION_PRESETS = {
    "neutral":  {"rate": 1.0,  "pitch": 0,    "gain": 0,  "extra": None},
    "happy":    {"rate": 1.05, "pitch": 1.0,  "gain": 1,  "extra": None},
    "sad":      {"rate": 0.9,  "pitch": -1.0, "gain": -2, "extra": "lp4000"},
    "angry":    {"rate": 1.1,  "pitch": 0.5,  "gain": 2,  "extra": None},
    "fear":     {"rate": 1.1,  "pitch": 1.0,  "gain": -1, "extra": None},
    "surprise": {"rate": 1.05, "pitch": 2.0,  "gain": 1,  "extra": None},
    "disgust":  {"rate": 0.95, "pitch": -0.5, "gain": 0,  "extra": None},
}

def apply_emotion_dsp(
    audio: np.ndarray,
    sr: int,
    emotion: str,
    gender_shift: float = 0.0,
    speaker_shift: float = 0.0,
) -> np.ndarray:
    """
    Cleaned up DSP pipeline to minimize robotic artifacts and noise.
    Removed pink noise and aggressive time stretching.
    """
    params = EMOTION_PRESETS.get(emotion, EMOTION_PRESETS["neutral"])

    # ── 1. & 2. Time-stretch and Pitch shift removed ──
    # Emotion rate and pitch are now handled natively via the TTS engine 
    # (e.g. Edge-TTS SSML) to avoid phase-vocoder robotic artifacts.

    # ── 3. Emotion-specific effects ──
    extra = params["extra"]
    if extra == "lp4000":
        # Low-pass filter for sadness (muffles the voice slightly)
        freq = min(4000, sr * 0.45)
        sos = scipy.signal.butter(4, freq / (sr / 2), "low", output="sos")
        padlen = min(3 * (2 * len(sos) + 1), max(0, len(audio) - 1))
        audio = scipy.signal.sosfiltfilt(sos, audio, padlen=padlen)

    # ── 4. Gain adjustment ──
    gain_db = params["gain"]
    if gain_db != 0:
        gain_linear = 10 ** (gain_db / 20)
        audio = audio * gain_linear

    # ── 5. Peak limiting ──
    peak = np.max(np.abs(audio)) if len(audio) else 0.0
    if peak > 0.95:
        audio = audio * (0.95 / peak)

    return audio.astype(np.float32, copy=False)
