import gradio as gr
import os
from parser import parse_script, generate_script_from_prompt
from tts import generate_tts
from ambient import get_ambient_clip, get_music_clip
from mixer.mix import mix_scene
from config import ESC50_TAXONOMY

def scene_to_script(scene) -> str:
    lines = []
    lines.append(f"Language: {scene.language}")
    lines.append(f"Background: {scene.background_scene}")
    lines.append("")
    for d in scene.dialogues:
        lines.append(f"{d.speaker} [{d.emotion}] [{d.gender}]: {d.text}")
    return "\n".join(lines)

def process_ui(script_text: str, mode: str, add_music: bool, lang_override: str, bg_override: str):
    try:
        scene = parse_script(script_text, mode)
        
        # Override language if selected
        if lang_override and lang_override != "auto":
            scene.language = lang_override
            
        # Override background ambient if selected
        if bg_override and bg_override != "auto":
            scene.background_scene = bg_override
            
        # Apply translation if needed (e.g. English -> Kannada)
        from translator import apply_translation
        apply_translation(scene)
            
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
        updated_script = scene_to_script(scene)
        return updated_script, scene.language, scene.background_scene, mix_res.wav_path, f"Success! Audio generated: {mix_res.duration_s:.2f}s"
    except Exception as e:
        return script_text, lang_override, bg_override, None, f"Error: {str(e)}"

def process_auto(prompt: str, mode: str, add_music: bool, lang_override: str, bg_override: str):
    try:
        # Generate script from prompt
        script = generate_script_from_prompt(prompt)
        # Generate audio from script
        updated_script, out_lang, out_bg, audio_path, status = process_ui(script, mode, add_music, lang_override, bg_override)
        return updated_script, out_lang, out_bg, audio_path, status
    except Exception as e:
        return "", lang_override, bg_override, None, f"Error: {str(e)}"

# Minimal UI Theme
theme = gr.themes.Monochrome(
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
)

# Custom CSS for rainbow prompt box
css = """
.rainbow-box textarea {
    border: 3px solid transparent !important;
    background-image: linear-gradient(var(--input-background-fill, var(--background-fill-primary)), var(--input-background-fill, var(--background-fill-primary))), linear-gradient(to right, red, orange, yellow, green, blue, indigo, violet) !important;
    background-origin: border-box !important;
    background-clip: padding-box, border-box !important;
    animation: rainbow 5s linear infinite !important;
    color: var(--body-text-color) !important;
}
@keyframes rainbow {
    0% { filter: hue-rotate(0deg); }
    100% { filter: hue-rotate(360deg); }
}
"""

with gr.Blocks(title="Audio Scene Generator", css=css) as demo:
    gr.Markdown(
        """
        # Multilingual Audio Scene Generator
        Bring your scripts to life with TTS, ambient backgrounds, and music beds.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### ✨ LLM Story Generator")
            prompt_in = gr.Textbox(
                lines=2,
                label="Story Prompt",
                placeholder="Type a story prompt here... (e.g., A tense moment in an abandoned space station)",
                elem_classes=["rainbow-box"]
            )
            generate_auto_btn = gr.Button("Generate Story & Audio", variant="primary")
            
            gr.Markdown("### ✍️ Manual Script")
            script_in = gr.Textbox(
                lines=12, 
                label="Your Script (EN, HI, KN)",
                placeholder="" # Removed placeholder
            )
            
            with gr.Row():
                lang_in = gr.Dropdown(
                    choices=["auto", "en", "hi", "kn"], 
                    value="auto", 
                    label="Language Override", 
                    allow_custom_value=True
                )
                
                bg_in = gr.Dropdown(
                    choices=["auto"] + sorted([x for x in ESC50_TAXONOMY]), 
                    value="auto", 
                    label="Background Sound (Ambient)", 
                    allow_custom_value=True
                )
            
            with gr.Row():
                mode_in = gr.Radio(
                    ["auto", "llm", "local"], 
                    value="auto", 
                    label="Parser Mode"
                )
                music_in = gr.Checkbox(value=True, label="Add Music Bed")
                
            submit = gr.Button("Generate Audio from Script", variant="secondary")
            
        with gr.Column(scale=1):
            audio_out = gr.Audio(label="Output Audio", type="filepath", interactive=False)
            status_out = gr.Textbox(label="Status", interactive=False)
            # Removed Tips section

    generate_auto_btn.click(
        fn=process_auto,
        inputs=[prompt_in, mode_in, music_in, lang_in, bg_in],
        outputs=[script_in, lang_in, bg_in, audio_out, status_out]
    )
            
    submit.click(
        fn=process_ui,
        inputs=[script_in, mode_in, music_in, lang_in, bg_in],
        outputs=[script_in, lang_in, bg_in, audio_out, status_out]
    )

if __name__ == "__main__":
    demo.launch(theme=theme)
