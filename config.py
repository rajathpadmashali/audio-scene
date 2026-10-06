import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"

for d in [DATA_DIR, MODELS_DIR, REPORTS_DIR, DATA_DIR / "ambient_bank", DATA_DIR / "music"]:
    d.mkdir(parents=True, exist_ok=True)

ESC50_TAXONOMY = [
    "rain", "thunderstorm", "wind", "sea_waves", "crackling_fire", "crickets", 
    "chirping_birds", "rooster", "dog", "cat", "crow", "car_horn", "engine", 
    "train", "siren", "church_bells", "clock_tick", "keyboard_typing", 
    "door_knock", "footsteps", "clapping", "laughing", "crying_baby", 
    "vacuum_cleaner", "helicopter", "airplane", "none"
]

ESC50_SYNONYMS = {
    "storm": "thunderstorm", "traffic": "car_horn", "ocean": "sea_waves", 
    "beach": "sea_waves", "village": "rooster", "office": "keyboard_typing", 
    "temple": "church_bells", "birds": "chirping_birds"
}

TTS_MODELS = {
    "en": {
        "male": os.environ.get("TTS_EN_MALE", "facebook/mms-tts-eng"),
        "female": os.environ.get("TTS_EN_FEMALE", "facebook/mms-tts-eng"),
    },
    "hi": {
        "male": os.environ.get("TTS_HI_MALE", "facebook/mms-tts-hin"),
        "female": os.environ.get("TTS_HI_FEMALE", "facebook/mms-tts-hin"),
    },
    "kn": {
        "male": os.environ.get("TTS_KN_MALE", "facebook/mms-tts-kan"),
        "female": os.environ.get("TTS_KN_FEMALE", "facebook/mms-tts-kan"),
    }
}
