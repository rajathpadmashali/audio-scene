import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import load_dataset
import json
import sys
import os
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import BASE_DIR, REPORTS_DIR

def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average='macro')
    return {"accuracy": acc, "f1": f1}

def train():
    dataset = load_dataset("go_emotions")
    
    with open(BASE_DIR / "emotion" / "label_map.json", "r") as f:
        mapping = json.load(f)
        
    ekman_labels = ["neutral", "happy", "sad", "angry", "fear", "surprise", "disgust"]
    go_emotions_classes = dataset["train"].features["labels"].feature.names
    
    def map_labels(example):
        labels = example["labels"]
        if not labels:
            return {"label": 0}
        orig = go_emotions_classes[labels[0]]
        ekman = mapping.get(orig, "neutral")
        return {"label": ekman_labels.index(ekman)}
        
    dataset = dataset.map(map_labels, remove_columns=["labels", "id"])
    
    tokenizer = AutoTokenizer.from_pretrained("distilbert-base-multilingual-cased")
    
    def tokenize(batch):
        return tokenizer(batch["text"], padding="max_length", truncation=True, max_length=64)
        
    dataset = dataset.map(tokenize, batched=True)
    
    model = AutoModelForSequenceClassification.from_pretrained(
        "distilbert-base-multilingual-cased", 
        num_labels=7
    )
    
    args = TrainingArguments(
        output_dir=str(BASE_DIR / "models" / "emotion_model"),
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=3,
        weight_decay=0.01,
        fp16=torch.cuda.is_available(),
    )
    
    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=dataset["train"].select(range(5000)), # Subset for testing
        eval_dataset=dataset["validation"].select(range(500)),
        compute_metrics=compute_metrics,
    )
    
    trainer.train()
    trainer.save_model(str(BASE_DIR / "models" / "emotion_model"))
    tokenizer.save_pretrained(str(BASE_DIR / "models" / "emotion_model"))

if __name__ == "__main__":
    train()
