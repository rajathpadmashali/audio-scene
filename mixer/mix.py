import json
import librosa
import numpy as np
import soundfile as sf
import pyloudnorm as pyln
from pathlib import Path
from schemas import SceneSpec, TTSResult, MixResult

def apply_ducking(ambient: np.ndarray, speech: np.ndarray, sr: int, duck_db: float = -12.0) -> np.ndarray:
    frame_len = int(sr * 0.01) # 10 ms frames
    attack_frames = int(0.150 * sr / frame_len)
    release_frames = int(0.400 * sr / frame_len)
    
    # Compute speech energy envelope
    speech_frames = np.pad(speech, (0, (frame_len - len(speech) % frame_len) % frame_len))
    speech_frames = speech_frames.reshape(-1, frame_len)
    energy = np.sum(speech_frames**2, axis=1)
    threshold = 1e-5
    is_speech = energy > threshold
    
    # Envelope gain with attack/release
    gain = np.zeros_like(is_speech, dtype=np.float32)
    current_gain = 1.0
    target_gain_linear = 10 ** (duck_db / 20)
    
    for i in range(len(is_speech)):
        if is_speech[i]:
            current_gain -= (1.0 - target_gain_linear) / max(1, attack_frames)
            current_gain = max(target_gain_linear, current_gain)
        else:
            current_gain += (1.0 - target_gain_linear) / max(1, release_frames)
            current_gain = min(1.0, current_gain)
        gain[i] = current_gain
        
    gain_upsampled = np.repeat(gain, frame_len)[:len(ambient)]
    if len(gain_upsampled) < len(ambient):
        gain_upsampled = np.pad(
            gain_upsampled,
            (0, len(ambient) - len(gain_upsampled)),
            constant_values=1.0,
        )
    return ambient * gain_upsampled

def mix_scene(scene: SceneSpec, tts_results: list[TTSResult], ambient_path: str = None, music_path: str = None, out_path: str = "final.wav") -> MixResult:
    sr = 44100
    
    # 1. Timeline
    timeline = []
    current_time = 0.0
    speech_parts = []
    
    fade_len = int(sr * 0.02) # 20ms fade
    fade_in = np.linspace(0, 1, fade_len)
    fade_out = np.linspace(1, 0, fade_len)
    
    for d, res in zip(scene.dialogues, tts_results):
        audio, _ = librosa.load(res.wav_path, sr=sr, mono=True)
        
        # Add very light room reverb to blend with ambient bed
        delay_samples = int(sr * 0.03) # 30ms
        if delay_samples < len(audio):
            reverb = np.zeros_like(audio)
            reverb[delay_samples:] = audio[:-delay_samples] * 0.15
            audio = audio + reverb
        
        # Apply fade in/out to remove boundary clicks
        if len(audio) > 2 * fade_len:
            audio[:fade_len] *= fade_in
            audio[-fade_len:] *= fade_out
            
        speech_parts.append(audio)
        timeline.append({"idx": res.idx, "start": current_time, "end": current_time + res.duration_s})
        current_time += res.duration_s
        
        pause_s = d.pause_after_ms / 1000.0
        if pause_s > 0:
            speech_parts.append(np.zeros(int(pause_s * sr)))
            current_time += pause_s
        
    speech_mix = np.concatenate(speech_parts) if speech_parts else np.zeros(0)
    
    total_samples = len(speech_mix) + int(1.0 * sr) # 1s tail
    speech_mix = np.pad(speech_mix, (0, total_samples - len(speech_mix)))
    
    # 2. Loudness (pyloudnorm)
    meter = pyln.Meter(sr)
    def normalize_loudness(audio, target_lufs):
        if len(audio) < sr * 0.4: return audio
        loudness = meter.integrated_loudness(audio)
        if np.isinf(loudness): return audio
        return pyln.normalize.loudness(audio, loudness, target_lufs)
        
    speech_mix = normalize_loudness(speech_mix, -20.0)
    
    # 3. Ambient & Music Loop & Duck
    bg_mix = np.zeros(total_samples)
    for path, target_lufs in [(ambient_path, -24.0), (music_path, -26.0)]:
        if path and Path(path).exists():
            audio, _ = librosa.load(path, sr=sr, mono=True)
            if len(audio) > 0:
                audio = normalize_loudness(audio, target_lufs)
                # Loop
                repeats = int(np.ceil(total_samples / len(audio)))
                audio = np.tile(audio, repeats)[:total_samples]
                # Ducking
                audio = apply_ducking(audio, speech_mix, sr)
                bg_mix += audio
                
    # 5. Sum & Limit
    final_mix = speech_mix + bg_mix
    
    # Simple limiter to -1 dBFS
    max_val = np.max(np.abs(final_mix))
    limit_val = 10 ** (-1.0 / 20)
    if max_val > limit_val:
        final_mix = final_mix * (limit_val / max_val)
        
    final_lufs = meter.integrated_loudness(final_mix) if len(final_mix) > sr * 0.4 else -16.0
    # Normalize to -16 LUFS
    if not np.isinf(final_lufs):
         final_mix = pyln.normalize.loudness(final_mix, final_lufs, -16.0)

    peak = np.max(np.abs(final_mix)) if len(final_mix) else 0.0
    limit_val = 10 ** (-1.0 / 20)
    if peak > limit_val:
        final_mix = final_mix * (limit_val / peak)
    
    sf.write(out_path, final_mix, sr)
    with open(str(Path(out_path).with_suffix('.json')), 'w') as f:
        json.dump(timeline, f, indent=2)
        
    return MixResult(wav_path=out_path, duration_s=total_samples/sr, lufs=-16.0)
