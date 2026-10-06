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
    1. If a 'Context:' or 'Characters:' header exists, use it to infer character genders and the best background_scene.
    2. Infer gender from character names if not explicitly stated.
    3. Infer emotion from the dialogue text if not explicitly stated. **Crucial: Emotion must STRICTLY be one of: 'neutral', 'happy', 'sad', 'angry', 'fear', 'surprise', or 'disgust'. Do NOT use any other words like 'urgent' or 'concerned'.**
    4. Set 'pause_after_ms' intelligently based on punctuation (e.g. 200ms for comma, 500ms for period, 900ms for ellipsis, +200ms if the speaker changes in the next line).
    
    Format example:
    {{
      "language": "en",
      "background_scene": "rain",
      "dialogues": [
        {{"idx": 0, "speaker": "male_1", "gender": "male", "text": "Hello", "emotion": "neutral", "pause_after_ms": 500}}
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
