import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
REPORTS_DIR = BASE_DIR / "reports"
NAMES_DIR = DATA_DIR / "names"

for d in [DATA_DIR, MODELS_DIR, REPORTS_DIR, DATA_DIR / "ambient_bank", DATA_DIR / "music", NAMES_DIR]:
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
    "temple": "church_bells", "birds": "chirping_birds",
    "sea": "sea_waves", "waves": "sea_waves", "shore": "sea_waves",
    "coast": "sea_waves", "harbour": "sea_waves", "harbor": "sea_waves",
    "fire": "crackling_fire", "campfire": "crackling_fire", "bonfire": "crackling_fire",
    "fireplace": "crackling_fire", "hearth": "crackling_fire",
    "thunder": "thunderstorm", "lightning": "thunderstorm",
    "night": "crickets", "midnight": "crickets", "dusk": "crickets",
    "morning": "chirping_birds", "dawn": "chirping_birds", "sunrise": "chirping_birds",
    "garden": "chirping_birds", "park": "chirping_birds", "forest": "chirping_birds",
    "jungle": "chirping_birds", "woods": "chirping_birds",
    "road": "car_horn", "highway": "car_horn", "street": "car_horn",
    "railway": "train", "station": "train", "platform": "train",
    "church": "church_bells", "mosque": "church_bells", "prayer": "church_bells",
    "police": "siren", "ambulance": "siren", "emergency": "siren",
    "hospital": "siren",
    "farm": "rooster", "rural": "rooster", "countryside": "rooster",
    "party": "laughing", "celebration": "laughing",
    "audience": "clapping", "applause": "clapping", "stage": "clapping",
    "concert": "clapping", "performance": "clapping",
    "airport": "airplane", "flight": "airplane", "runway": "airplane",
    "baby": "crying_baby", "nursery": "crying_baby",
    "corridor": "footsteps", "hallway": "footsteps", "alley": "footsteps",
    "typing": "keyboard_typing", "computer": "keyboard_typing", "desk": "keyboard_typing",
    "clock": "clock_tick", "waiting": "clock_tick",
}

# ── Keyword scoring for smart ambient auto-assignment ──────────────
# Each key is an ESC-50 label; the value is a list of keywords that
# suggest that ambient.  The parser scores each ambient by counting
# keyword hits across all dialogue text + context.
SCENE_KEYWORDS = {
    "rain":           ["rain", "rainy", "drizzle", "downpour", "monsoon",
                       "umbrella", "puddle", "wet", "pour", "shower"],
    "thunderstorm":   ["thunder", "lightning", "storm", "tempest", "gale",
                       "rumble", "bolt"],
    "sea_waves":      ["ocean", "sea", "beach", "shore", "waves", "coast",
                       "boat", "ship", "harbour", "harbor", "sail", "island",
                       "tide", "surf", "pier", "dock", "lighthouse"],
    "wind":           ["wind", "windy", "breeze", "gust", "blowing", "breezy",
                       "gusty", "howling wind"],
    "crackling_fire": ["fire", "fireplace", "campfire", "bonfire", "hearth",
                       "flame", "burning", "embers", "warm glow", "chimney"],
    "crickets":       ["night", "evening", "dark", "midnight", "dusk",
                       "nightfall", "moonlight", "stars", "nocturnal",
                       "after dark", "twilight", "moon"],
    "chirping_birds": ["morning", "dawn", "sunrise", "garden", "park",
                       "tree", "forest", "jungle", "woods", "meadow",
                       "flowers", "spring", "sunny", "daybreak", "grove"],
    "dog":            ["dog", "puppy", "bark", "kennel", "hound", "paw",
                       "fetch", "leash"],
    "cat":            ["cat", "kitten", "meow", "purr", "feline", "whiskers"],
    "car_horn":       ["traffic", "road", "highway", "drive", "car", "taxi",
                       "bus", "street", "honk", "vehicle", "intersection",
                       "commute", "rush hour"],
    "engine":         ["engine", "motor", "truck", "motorcycle", "garage",
                       "rev", "diesel"],
    "train":          ["train", "railway", "station", "platform", "tracks",
                       "locomotive", "compartment", "rail", "carriage"],
    "church_bells":   ["church", "temple", "mosque", "bell", "prayer",
                       "worship", "chapel", "cathedral", "shrine"],
    "clock_tick":     ["clock", "tick", "waiting", "silence", "quiet room",
                       "study", "library", "ticking", "grandfather clock",
                       "pendulum"],
    "keyboard_typing":["office", "computer", "typing", "desk", "work",
                       "cubicle", "laptop", "keyboard", "email", "meeting room"],
    "footsteps":      ["walking", "footsteps", "corridor", "hallway", "alley",
                       "passage", "tunnel", "staircase", "steps", "path"],
    "door_knock":     ["knock", "door", "entrance", "doorbell", "gate"],
    "siren":          ["police", "ambulance", "emergency", "hospital",
                       "patrol", "alarm", "rescue"],
    "crying_baby":    ["baby", "infant", "nursery", "cradle", "newborn",
                       "diaper", "crib"],
    "rooster":        ["village", "farm", "rural", "countryside", "rooster",
                       "barn", "harvest", "field", "crop", "tractor"],
    "laughing":       ["party", "celebration", "laughing", "comedy", "joke",
                       "funny", "humor", "giggle", "chuckle", "festival"],
    "clapping":       ["audience", "applause", "stage", "performance",
                       "concert", "theatre", "theater", "show", "recital"],
    "helicopter":     ["helicopter", "chopper", "rescue", "airlift", "hover"],
    "airplane":       ["airport", "airplane", "flight", "runway", "jet",
                       "pilot", "cabin", "turbulence", "takeoff", "landing"],
    "crow":           ["crow", "raven", "scarecrow", "graveyard", "cemetery",
                       "haunted", "abandoned"],
    "vacuum_cleaner": ["vacuum", "cleaning", "housework", "maid"],
}

# ── Punctuation → pause mapping (ms) ──────────────────────────────
PAUSE_MAP = {
    ".":   500,
    "!":   550,
    "?":   450,
    "...": 900,
    "…":   900,
    ",":   200,
    ";":   300,
    ":":   300,
    "—":   600,
    "-":   200,
}
PAUSE_SPEAKER_CHANGE_EXTRA = 200   # extra ms when speaker changes
PAUSE_DEFAULT = 350                # default when no punctuation detected

# ── Emotion keyword fallback (when no classifier model is available) ──
EMOTION_KEYWORDS = {
    "happy":    ["happy", "joy", "wonderful", "excited", "delighted", "glad",
                 "cheerful", "thrilled", "overjoyed", "elated", "smile",
                 "laugh", "celebrate", "love", "amazing", "fantastic",
                 "great", "beautiful", "blessed", "grateful"],
    "sad":      ["sad", "cry", "tears", "sorrow", "grief", "heartbreak",
                 "depressed", "miserable", "lonely", "regret", "mourn",
                 "lost", "miss", "pain", "hurt", "broken", "tragic",
                 "disappointed", "hopeless", "despair"],
    "angry":    ["angry", "furious", "rage", "mad", "hate", "annoyed",
                 "irritated", "outraged", "livid", "enraged", "hostile",
                 "bitter", "resentful", "frustrated", "fed up", "disgusted"],
    "fear":     ["scared", "afraid", "terrified", "horror", "fear", "panic",
                 "nervous", "anxious", "dread", "creepy", "frightened",
                 "trembling", "shaking", "alarmed", "worried", "uneasy",
                 "ghost", "scream", "danger", "threat"],
    "surprise": ["surprised", "shocked", "astonished", "amazed", "stunned",
                 "unexpected", "unbelievable", "incredible", "wow",
                 "startled", "bewildered", "disbelief", "gasp", "oh my",
                 "what", "no way", "really"],
    "disgust":  ["disgusting", "gross", "revolting", "repulsive", "nasty",
                 "vile", "sickening", "awful", "horrible", "yuck",
                 "eww", "filthy", "rotten", "putrid", "foul"],
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
