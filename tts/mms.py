import hashlib
import asyncio
import librosa
import soundfile as sf
from pathlib import Path
from config import DATA_DIR
from tts.emotion_dsp import apply_emotion_dsp
from schemas import TTSResult
import edge_tts

VOICE_POOLS = {
    "en": {
        "female": ["en-US-JennyNeural", "en-US-AriaNeural", "en-US-AnaNeural", "en-US-MichelleNeural", "en-US-AvaNeural"],
        "male": ["en-US-GuyNeural", "en-US-ChristopherNeural", "en-US-EricNeural", "en-US-BrianNeural", "en-US-AndrewNeural"]
    },
    "hi": {
        "female": ["hi-IN-SwaraNeural"],
        "male": ["hi-IN-MadhurNeural"]
    },
    "kn": {
        "female": ["kn-IN-SapnaNeural"],
        "male": ["kn-IN-GaganNeural"]
    }
}

def get_voice_for_speaker(lang: str, gender: str, speaker: str) -> str:
    pool = VOICE_POOLS.get(lang, {}).get(gender)
    if not pool:
        pool = VOICE_POOLS.get("en", {}).get(gender, ["en-US-JennyNeural"])
    
    # Hash speaker name to stably pick a voice from the pool
    if speaker:
        speaker_hash = int(hashlib.md5(speaker.lower().strip().encode("utf-8")).hexdigest(), 16)
        return pool[speaker_hash % len(pool)]
    return pool[0]

def get_edge_tts_params(emotion: str):
    # Milder pitch changes to preserve character identity, utilizing rate and volume for emotion
    if emotion == "happy":
        return "+10%", "+5Hz", "+10%"
    elif emotion == "sad":
        return "-15%", "-10Hz", "-15%"
    elif emotion == "angry":
        return "+15%", "+10Hz", "+20%"
    elif emotion == "fear":
        return "+20%", "+15Hz", "+0%"
    elif emotion == "surprise":
        return "+5%", "+15Hz", "+10%"
    elif emotion == "disgust":
        return "-5%", "-5Hz", "-5%"
    return "+0%", "+0Hz", "+0%"

async def generate_edge_tts(text: str, voice: str, rate: str, pitch: str, volume: str, output_path: str):
    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume=volume)
    await communicate.save(output_path)

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

    # Add punctuation to prevent flat reading
    text = text.strip()
    if not text.endswith(('.', '!', '?', ',')):
        text += '.'

    voice = get_voice_for_speaker(lang, gender, speaker)
    rate, pitch, volume = get_edge_tts_params(emotion)

    hash_str = hashlib.sha256(
        f"v9|edge|{voice}|{text}|{emotion}|{speaker}|{rate}|{pitch}|{volume}".encode("utf-8")
    ).hexdigest()
    
    mp3_path = DATA_DIR / f"tts_cache_{hash_str}.mp3"
    wav_path = DATA_DIR / f"tts_cache_{hash_str}.wav"
    
    if not wav_path.exists():
        # Generate using Edge TTS natively
        asyncio.run(generate_edge_tts(text, voice, rate, pitch, volume, str(mp3_path)))
        
        # Load and apply light DSP
        output, sr = librosa.load(str(mp3_path), sr=24000)
        output, _ = librosa.effects.trim(output, top_db=35)
        
        # We only use apply_emotion_dsp for lowpass filters (like in sad) and limiting
        # No pitch shifting or time stretching via librosa anymore!
        output = apply_emotion_dsp(
            output,
            sr,
            emotion,
            gender_shift=0.0,
            speaker_shift=0.0,
        )
        
        sf.write(str(wav_path), output, sr)
        if mp3_path.exists():
            try:
                mp3_path.unlink()
            except:
                pass
            
    dur = librosa.get_duration(path=str(wav_path))
    return TTSResult(idx=idx, wav_path=str(wav_path), sr=24000, duration_s=dur)
