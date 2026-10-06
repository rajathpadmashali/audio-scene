import numpy as np

from tts.emotion_dsp import apply_emotion_dsp, get_emotion_rate


def test_emotion_processing_preserves_finite_audio_and_humanizes_pacing():
    sr = 24000
    audio = 0.2 * np.sin(2 * np.pi * 220 * np.arange(sr) / sr)

    neutral = apply_emotion_dsp(audio, sr, "neutral")
    sad = apply_emotion_dsp(audio, sr, "sad")

    assert np.isfinite(neutral).all()
    assert np.isfinite(sad).all()
    assert len(sad) > len(neutral)
    assert get_emotion_rate("neutral") < 1.0


def test_gender_variants_use_a_distinct_pitch_without_clipping():
    sr = 24000
    audio = 0.2 * np.sin(2 * np.pi * 220 * np.arange(sr) / sr)

    female = apply_emotion_dsp(audio, sr, "neutral", gender_shift=2.0)
    male = apply_emotion_dsp(audio, sr, "neutral", gender_shift=-2.0)

    assert not np.allclose(female, male)
    assert np.max(np.abs(female)) <= 0.98
    assert np.max(np.abs(male)) <= 0.98
