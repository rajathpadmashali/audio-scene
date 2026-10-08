import os
from groq import Groq
from parser.local_parser import detect_lang

def translate_text(text: str, target_lang: str) -> str:
    """
    Translates text to the target language using Groq if needed.
    Supports targeting 'kn' (Kannada) or 'hi' (Hindi).
    If the text is already in the target language (detected by unicode), it skips translation.
    """
    current_lang = detect_lang(text)
    if current_lang == target_lang:
        return text
        
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        print(f"[Warning] GROQ_API_KEY not set. Skipping translation to {target_lang}.")
        return text
        
    try:
        client = Groq(api_key=api_key)
        model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
        
        lang_map = {
            "kn": "Kannada",
            "hi": "Hindi",
            "en": "English"
        }
        
        target_name = lang_map.get(target_lang, target_lang)
        
        sys_prompt = f"You are a professional translator. Translate the given text to {target_name}. Output ONLY the translated text in the native script without any quotes, explanations, or transliteration."
        
        res = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": text}
            ],
            temperature=0,
        )
        translated = res.choices[0].message.content.strip()
        return translated
    except Exception as e:
        print(f"[Error] Translation to {target_lang} failed: {str(e)}")
        return text

def apply_translation(scene) -> None:
    """Translates dialogue text in the scene to the target language if required."""
    for d in scene.dialogues:
        if scene.language in ['kn', 'hi']:
            if detect_lang(d.text) == 'en':
                d.text = translate_text(d.text, scene.language)
