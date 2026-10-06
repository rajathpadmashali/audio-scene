import librosa
import numpy as np
import scipy.signal

def get_emotion_rate(emotion: str) -> float:
    rates = {
        "neutral": 0.92,
        "happy": 1.02,
        "sad": 0.84,
        "angry": 1.04,
        "fear": 1.06,
        "surprise": 1.02,
        "disgust": 0.90
    }
    return rates.get(emotion, 0.92)

def apply_emotion_dsp(
    audio: np.ndarray,
    sr: int,
    emotion: str,
    gender_shift: float = 0.0,
    speaker_shift: float = 0.0,
) -> np.ndarray:
    presets = {
        "neutral":  {"pitch": 0, "gain": 0, "extra": None},
        "happy":    {"pitch": 1, "gain": 0, "extra": None},
        "sad":      {"pitch": -1, "gain": -2, "extra": "lp4k"},
        "angry":    {"pitch": 0.5, "gain": 1, "extra": "softclip"},
        "fear":     {"pitch": 1, "gain": -1, "extra": "tremolo"},
        "surprise": {"pitch": 1, "gain": 1, "extra": None},
        "disgust":  {"pitch": -0.5, "gain": 0, "extra": None}
    }

    params = presets.get(emotion, presets["neutral"])

    rate = get_emotion_rate(emotion)
    if len(audio) and rate != 1.0:
        audio = librosa.effects.time_stretch(audio, rate=rate)

    pitch = params["pitch"] + gender_shift + speaker_shift
    if len(audio) and pitch != 0:
        audio = librosa.effects.pitch_shift(audio, sr=sr, n_steps=pitch)

    extra = params["extra"]
    if extra == "lp4k":
        sos = scipy.signal.butter(4, 4000 / (sr / 2), "low", output="sos")
        padlen = min(3 * (2 * len(sos) + 1), max(0, len(audio) - 1))
        audio = scipy.signal.sosfiltfilt(sos, audio, padlen=padlen)
    elif extra == "softclip":
        drive = 1.15
        audio = np.tanh(audio * drive)
    elif extra == "tremolo":
        t = np.arange(len(audio)) / sr
        tremolo = 1.0 - 0.1 * (0.5 * (1.0 - np.cos(2 * np.pi * 6 * t)))
        audio = audio * tremolo
        
    gain_db = params["gain"]
    if gain_db != 0:
        gain_linear = 10 ** (gain_db / 20)
        audio = audio * gain_linear

    peak = np.max(np.abs(audio)) if len(audio) else 0.0
    if peak > 0.98:
        audio = audio * (0.98 / peak)

    return audio.astype(np.float32, copy=False)
