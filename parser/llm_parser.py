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
    The script may start with 'Language: <en|hi|kn>' and 'Background: <ESC-50 label>'.
    Dialogue lines may mark a speaker with [emotion] and [male|female] tags.
    Preserve the requested background and explicit speaker emotions/genders.
    
    Format example:
    {{
      "language": "en",
      "background_scene": "rain",
      "dialogues": [
        {{"idx": 0, "speaker": "male_1", "gender": "male", "text": "Hello", "emotion": "neutral", "pause_after_ms": 300}}
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
