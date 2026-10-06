import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from config import BASE_DIR
import json

def get_emotion(text: str) -> str:
    model_path = BASE_DIR / "models" / "emotion_model"
    if not model_path.exists():
        return "neutral"
        
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=64)
    with torch.no_grad():
        outputs = model(**inputs)
        
    ekman_labels = ["neutral", "happy", "sad", "angry", "fear", "surprise", "disgust"]
    pred = outputs.logits.argmax(-1).item()
    return ekman_labels[pred]
