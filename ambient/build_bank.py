import os
import shutil
import csv
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR, ESC50_TAXONOMY

def build_bank():
    esc50_meta = DATA_DIR / "esc50" / "ESC-50-master" / "meta" / "esc50.csv"
    esc50_audio = DATA_DIR / "esc50" / "ESC-50-master" / "audio"
    bank_dir = DATA_DIR / "ambient_bank"
    
    if not esc50_meta.exists():
        print("Run download_esc50.py first!")
        return
        
    print("Building ambient bank...")
    with open(esc50_meta, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            category = row["category"]
            if category in ESC50_TAXONOMY:
                cat_dir = bank_dir / category
                cat_dir.mkdir(parents=True, exist_ok=True)
                
                src = esc50_audio / row["filename"]
                dst = cat_dir / row["filename"]
                if not dst.exists():
                    shutil.copy(src, dst)
                    
    print("Done building bank.")

if __name__ == "__main__":
    build_bank()
