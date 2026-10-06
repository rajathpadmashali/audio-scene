import torch
import torch.nn as nn
import torchvision.models as models
import librosa
import numpy as np
import pandas as pd
import sys
import os
from pathlib import Path
from torch.utils.data import Dataset, DataLoader

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR, REPORTS_DIR, ESC50_TAXONOMY

class ESC50Dataset(Dataset):
    def __init__(self, csv_path, audio_dir, fold, train=True):
        df = pd.read_csv(csv_path)
        if train:
            self.df = df[df.fold != fold]
        else:
            self.df = df[df.fold == fold]
            
        self.audio_dir = Path(audio_dir)
        self.classes = {c: i for i, c in enumerate(ESC50_TAXONOMY)}
        
    def __len__(self):
        return len(self.df)
        
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        cat = row['category']
        if cat not in self.classes:
            cat = "none"
            
        label = self.classes[cat]
        path = self.audio_dir / row['filename']
        
        y, sr = librosa.load(path, sr=22050, duration=5.0)
        if len(y) < 5 * 22050:
            y = np.pad(y, (0, 5 * 22050 - len(y)))
            
        mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
        mel_db = librosa.power_to_db(mel, ref=np.max)
        
        mel_t = torch.tensor(mel_db).unsqueeze(0).float()
        return mel_t, label

def train():
    print("Training ResNet for ESC-50...")
    model = models.resnet18(pretrained=True)
    model.conv1 = nn.Conv2d(1, 64, kernel_size=(7, 7), stride=(2, 2), padding=(3, 3), bias=False)
    model.fc = nn.Linear(model.fc.in_features, len(ESC50_TAXONOMY))
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    
    csv_path = DATA_DIR / "esc50" / "ESC-50-master" / "meta" / "esc50.csv"
    audio_dir = DATA_DIR / "esc50" / "ESC-50-master" / "audio"
    
    if not csv_path.exists():
        print("ESC-50 dataset not found.")
        return
        
    train_ds = ESC50Dataset(csv_path, audio_dir, fold=5, train=True)
    train_dl = DataLoader(train_ds, batch_size=32, shuffle=True)
    
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    
    for epoch in range(1): # Just 1 epoch for demonstration
        model.train()
        for x, y in train_dl:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            
    torch.save(model.state_dict(), DATA_DIR / "resnet18_esc50.pt")
    print("Done training.")

if __name__ == "__main__":
    train()
