from groq import Groq
import os
import json
from schemas import SceneSpec
from config import ESC50_TAXONOMY

def parse_with_llm(script: str) -> SceneSpec:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set")
    client = Groq(api_key=api_key)
    model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    
    taxonomy_str = ", ".join(ESC50_TAXONOMY)
    prompt = f"""
    Convert this script to a JSON strictly following SceneSpec schema.
    Language must be 'en', 'hi', or 'kn'.
    Background_scene must be one of: {taxonomy_str}.
    
    INSTRUCTIONS:
    1. Infer the best background_scene from the script content (context headers or dialogue text). If no scene fits well, use 'none'.
    2. Infer gender from character names if not explicitly stated.
    3. Infer emotion from the dialogue text if not explicitly stated. **Crucial: Emotion must STRICTLY be one of: 'neutral', 'happy', 'sad', 'angry', 'fear', 'surprise', or 'disgust'. Do NOT use any other words like 'urgent' or 'concerned'.**
    4. Set 'pause_after_ms' intelligently based on punctuation.
    5. The 'speaker' field MUST be the actual character's name as written in the script (e.g. 'John', 'Sarah'). Do not use generic labels like 'male_1'.
    
    Format example:
    {{
      "language": "en",
      "background_scene": "rain",
      "dialogues": [
        {{"idx": 0, "speaker": "John", "gender": "male", "text": "Hello", "emotion": "neutral", "pause_after_ms": 500}}
      ]
    }}
    
    Script:
    {script}
    """
    
    last_err = None
    for _ in range(2):
        try:
            res = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"}
            )
            data = json.loads(res.choices[0].message.content)
            return SceneSpec(**data)
        except Exception as e:
            last_err = e
    raise ValueError(f"LLM Parsing failed: {last_err}")

def generate_script_from_prompt(prompt: str) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in .env")
    client = Groq(api_key=api_key)
    model = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")
    
    sys_prompt = """
    You are an expert audio drama scriptwriter. The user will give you a prompt.
    Write a short script (4 to 8 lines of dialogue) matching the prompt.
    If the prompt is generic, create a popular or meaningful related story.
    Use simple English whenever possible and don't make it too wordy.
    
    You MUST format it strictly as follows:
    Context: A brief description of the setting and ambient sounds.
    Characters: Name1 (gender), Name2 (gender)
    
    Name1 [emotion]: Dialogue text here.
    Name2 [emotion]: Dialogue text here.
    
    Emotions must be one of: neutral, happy, sad, angry, fear, surprise, disgust.
    Do not output any extra text, only the script.
    """
    
    res = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
    )
    return res.choices[0].message.content.strip()
