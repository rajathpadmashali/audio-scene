import pytest
import numpy as np
from mixer.mix import apply_ducking

def test_ducking():
    sr = 44100
    ambient = np.ones(sr * 2)
    speech = np.zeros(sr * 2)
    # Speech active from 0.5 to 1.5s
    speech[int(0.5*sr):int(1.5*sr)] = 0.5
    
    ducked = apply_ducking(ambient, speech, sr, duck_db=-12)
    
    # Check if ducked amplitude is reduced during speech
    mid_speech_amp = ducked[int(1.0*sr)]
    no_speech_amp = ducked[int(0.1*sr)]
    
    assert mid_speech_amp < no_speech_amp

def test_ducking_starts_at_full_level_and_pads_short_speech():
    sr = 44100
    ambient = np.ones(sr)
    speech = np.zeros(sr // 2)

    ducked = apply_ducking(ambient, speech, sr)

    assert ducked[0] == pytest.approx(1.0)
    assert len(ducked) == len(ambient)
