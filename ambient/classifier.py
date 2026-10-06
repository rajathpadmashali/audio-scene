import torch
import torch.nn as nn
import torchvision.models as models
import librosa
import numpy as np
from config import DATA_DIR, ESC50_TAXONOMY

def verify_ambient(audio_path: str) -> str:
    model_path = DATA_DIR / "resnet18_esc50.pt"
    if not model_path.exists():
        return "unknown"
        
    model = models.resnet18(pretrained=False)
    model.conv1 = nn.Conv2d(1, 64, kernel_size=(7, 7), stride=(2, 2), padding=(3, 3), bias=False)
    model.fc = nn.Linear(model.fc.in_features, len(ESC50_TAXONOMY))
    model.load_state_dict(torch.load(model_path))
    model.eval()
    
    y, sr = librosa.load(audio_path, sr=22050, duration=5.0)
    if len(y) < 5 * 22050:
        y = np.pad(y, (0, 5 * 22050 - len(y)))
        
    mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    mel_db = librosa.power_to_db(mel, ref=np.max)
    
    mel_t = torch.tensor(mel_db).unsqueeze(0).unsqueeze(0).float()
    
    with torch.no_grad():
        out = model(mel_t)
        pred = out.argmax(-1).item()
        
    return ESC50_TAXONOMY[pred]
