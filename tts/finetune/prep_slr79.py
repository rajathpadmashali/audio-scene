import os
import shutil
import urllib.request
import zipfile
from pathlib import Path

def prepare_slr79():
    base_dir = Path("data/slr79")
    base_dir.mkdir(parents=True, exist_ok=True)
    
    print("SLR79 preparation script.")
    print("Please download kn_in_female.zip and kn_in_male.zip from OpenSLR SLR79.")
    print("Extract them to data/slr79/female and data/slr79/male")
    print("Then use https://github.com/ylacombe/finetune-hf-vits to fine-tune.")

if __name__ == "__main__":
    prepare_slr79()
