import argparse
from parser import parse_script
from tts import generate_tts
from ambient import get_ambient_clip, get_music_clip
from mixer.mix import mix_scene

def run_pipeline(script_text: str, mode: str = "auto", out_file: str = "final.wav"):
    print("Parsing script...")
    scene = parse_script(script_text, mode)
    print(f"Scene detected: {scene.language}, Background: {scene.background_scene}")
    
    tts_results = []
    emotions = []
    for d in scene.dialogues:
        print(f"Generating TTS for [{d.speaker}]: {d.text[:20]}... (emotion: {d.emotion})")
        res = generate_tts(
            d.text, scene.language, d.gender, d.emotion, d.idx, d.speaker
        )
        tts_results.append(res)
        emotions.append(d.emotion)
        
    dominant_emotion = max(set(emotions), key=emotions.count) if emotions else "neutral"
    
    ambient_path = get_ambient_clip(scene.background_scene)
    music_path = get_music_clip(dominant_emotion)
    
    print("Mixing...")
    mix_res = mix_scene(scene, tts_results, ambient_path, music_path, out_file)
    print(f"Done! Output: {mix_res.wav_path}")
    return mix_res

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("script", help="Path to script file")
    parser.add_argument("--mode", default="auto", choices=["auto", "llm", "local"])
    parser.add_argument("--out", default="final.wav")
    args = parser.parse_args()
    
    with open(args.script, "r", encoding="utf-8") as f:
         text = f.read()
         
    run_pipeline(text, args.mode, args.out)
