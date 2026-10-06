from pydantic import BaseModel
from typing import List, Literal

class Dialogue(BaseModel):
    idx: int
    speaker: str
    gender: Literal["male", "female"]
    text: str
    emotion: Literal["neutral", "happy", "sad", "angry", "fear", "surprise", "disgust"]
    pause_after_ms: int = 300

class SceneSpec(BaseModel):
    language: Literal["en", "hi", "kn"]
    background_scene: str
    dialogues: List[Dialogue]

class TTSResult(BaseModel):
    idx: int
    wav_path: str
    sr: int
    duration_s: float

class MixResult(BaseModel):
    wav_path: str
    duration_s: float
    lufs: float
