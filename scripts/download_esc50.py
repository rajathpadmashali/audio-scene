import urllib.request
import zipfile
import os
import sys
from pathlib import Path

# Add root project dir to python path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR
from pathlib import Path

def download_and_extract():
    esc50_dir = DATA_DIR / "esc50"
    esc50_dir.mkdir(parents=True, exist_ok=True)
    zip_path = esc50_dir / "master.zip"
    
    if not (esc50_dir / "ESC-50-master").exists():
        print("Downloading ESC-50...")
        url = "https://github.com/karoldvl/ESC-50/archive/master.zip"
        urllib.request.urlretrieve(url, zip_path)
        print("Extracting...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(esc50_dir)
        print("Done.")
    else:
        print("ESC-50 already exists.")

if __name__ == "__main__":
    download_and_extract()
