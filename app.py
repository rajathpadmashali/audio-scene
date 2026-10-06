import gradio as gr
import os
from parser import parse_script
from tts import generate_tts
from ambient import get_ambient_clip, get_music_clip
from mixer.mix import mix_scene

def process_ui(script_text: str, mode: str, add_music: bool):
    try:
        scene = parse_script(script_text, mode)
        tts_results = []
        emotions = []
        
        for d in scene.dialogues:
            res = generate_tts(
                d.text, scene.language, d.gender, d.emotion, d.idx, d.speaker
            )
            tts_results.append(res)
            emotions.append(d.emotion)
            
        dominant = max(set(emotions), key=emotions.count) if emotions else "neutral"
        ambient_path = get_ambient_clip(scene.background_scene)
        music_path = get_music_clip(dominant) if add_music else None
        
        mix_res = mix_scene(scene, tts_results, ambient_path, music_path, "output.wav")
        return mix_res.wav_path, f"Success! Audio generated: {mix_res.duration_s:.2f}s"
    except Exception as e:
        return None, f"Error: {str(e)}"

with gr.Blocks() as demo:
    gr.Markdown("# Multilingual Audio Scene Generator")
    with gr.Row():
        with gr.Column():
            script_in = gr.Textbox(lines=10, label="Script (EN, HI, KN)", placeholder="Write your script here...")
            mode_in = gr.Radio(["auto", "llm", "local"], value="local", label="Parser Mode")
            music_in = gr.Checkbox(value=True, label="Add Music Bed")
            submit = gr.Button("Generate")
        with gr.Column():
            audio_out = gr.Audio(label="Output Audio", type="filepath")
            status_out = gr.Textbox(label="Status")
            
    submit.click(
        fn=process_ui,
        inputs=[script_in, mode_in, music_in],
        outputs=[audio_out, status_out]
    )

if __name__ == "__main__":
    demo.launch()
