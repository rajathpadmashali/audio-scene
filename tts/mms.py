import torch
import hashlib
import soundfile as sf
import librosa
from transformers import VitsModel, AutoTokenizer
from config import TTS_MODELS, DATA_DIR
from tts.emotion_dsp import apply_emotion_dsp
from schemas import TTSResult

_models = {}
_tokenizers = {}

def get_model_and_tokenizer(lang: str, gender: str):
    model_id = TTS_MODELS.get(lang, {}).get(gender, TTS_MODELS.get(lang, {}).get("male", "facebook/mms-tts-eng"))
    
    if model_id not in _models:
        _models[model_id] = VitsModel.from_pretrained(model_id)
        _tokenizers[model_id] = AutoTokenizer.from_pretrained(model_id)
        
    return _models[model_id], _tokenizers[model_id]

def generate_tts(
    text: str,
    lang: str,
    gender: str,
    emotion: str,
    idx: int,
    speaker: str = "",
) -> TTSResult:
    if not text.strip():
        raise ValueError("Cannot synthesize an empty dialogue line.")

    model_id = TTS_MODELS.get(lang, {}).get(gender)
    if model_id is None:
        raise ValueError(f"No TTS model configured for language '{lang}' and voice '{gender}'.")

    hash_str = hashlib.sha256(
        f"v5|{model_id}|{text}|{lang}|{gender}|{emotion}|{speaker}".encode("utf-8")
    ).hexdigest()
    wav_path = DATA_DIR / f"tts_cache_{hash_str}.wav"
    
    if wav_path.exists():
        dur = librosa.get_duration(path=str(wav_path))
        return TTSResult(idx=idx, wav_path=str(wav_path), sr=24000, duration_s=dur)
        
    model, tokenizer = get_model_and_tokenizer(lang, gender)

    inputs = tokenizer(text, return_tensors="pt")

    with torch.inference_mode():
        output = model(**inputs).waveform[0].cpu().numpy()
        
    sr = model.config.sampling_rate
    
    if sr != 24000:
        output = librosa.resample(output, orig_sr=sr, target_sr=24000)
        sr = 24000
        
    output, _ = librosa.effects.trim(output, top_db=35)
        
    gender_models = TTS_MODELS.get(lang, {})
    gender_shift = 0.0
    if gender_models.get("male") == gender_models.get("female"):
        # The base MMS model for English actually has a median pitch of ~86 Hz (Male).
        # We must pitch shift UP significantly (+4.0) to make it sound female, as per the spec.
        # Male uses the base voice (0.0).
        gender_shift = 4.0 if gender == "female" else 0.0
    
    speaker_shift = 0.0
    if speaker:
        speaker_value = hashlib.sha256(speaker.encode("utf-8")).digest()[0] / 255
        # Reduce unique speaker variance scale to avoid severe distortion
        speaker_shift = (speaker_value - 0.5) * 0.8
        
    output = apply_emotion_dsp(
        output,
        sr,
        emotion,
        gender_shift=gender_shift,
        speaker_shift=speaker_shift,
    )
    
    sf.write(str(wav_path), output, sr)
    dur = len(output) / sr
    return TTSResult(idx=idx, wav_path=str(wav_path), sr=sr, duration_s=dur)
