import os
import random
from pathlib import Path
from config import DATA_DIR, ESC50_TAXONOMY

def get_ambient_clip(label: str) -> str:
    if label == "none" or label not in ESC50_TAXONOMY:
        return None
        
    bank_dir = DATA_DIR / "ambient_bank" / label
    if not bank_dir.exists():
        return None
        
    clips = list(bank_dir.glob("*.wav"))
    if not clips:
        return None
        
    return str(random.choice(clips))

def get_music_clip(dominant_emotion: str) -> str:
    if dominant_emotion in ["happy", "surprise"]:
        m_type = "happy"
    elif dominant_emotion == "sad":
        m_type = "sad"
    elif dominant_emotion in ["angry", "fear", "disgust"]:
        m_type = "tense"
    else:
        m_type = "calm"
        
    music_path = DATA_DIR / "music" / f"{m_type}.mp3"
    if music_path.exists():
        return str(music_path)
    return None
