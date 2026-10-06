import re
from schemas import SceneSpec, Dialogue
from config import ESC50_TAXONOMY, ESC50_SYNONYMS

def detect_lang(script: str) -> str:
    if any('\u0900' <= c <= '\u097F' for c in script): return "hi"
    if any('\u0C80' <= c <= '\u0CFF' for c in script): return "kn"
    return "en"

def guess_gender(speaker: str) -> str:
    s = speaker.lower()
    if any(k in s for k in ['woman', 'girl', 'mother', 'mom', 'mrs', 'ms', 'miss', 'queen', 'lady']):
        return "female"
    if any(k in s for k in ['man', 'boy', 'father', 'dad', 'mr', 'king', 'lord', 'sir']):
        return "male"
    if s.endswith(('a', 'i', 'y', 'ah', 'ee', 'ia')):
        return "female"
    return "male"

def parse_local(script: str) -> SceneSpec:
    lang = detect_lang(script)
    bg_scene = "none"
    script_lower = script.lower()

    dialogue_lines = []
    for line in script.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        language_match = re.match(r"^(?:language|lang)\s*:\s*(\w+)\s*$", line, re.IGNORECASE)
        if language_match:
            explicit_lang = language_match.group(1).lower()
            if explicit_lang not in {"en", "hi", "kn"}:
                raise ValueError(
                    f"Unsupported language '{explicit_lang}'. Use en, hi, or kn."
                )
            lang = explicit_lang
            continue

        background_match = re.match(
            r"^(?:background(?:\s+sound)?|background_scene)\s*:\s*(.+?)\s*$",
            line,
            re.IGNORECASE,
        )
        if background_match:
            requested_scene = background_match.group(1).strip().lower().replace(" ", "_")
            requested_scene = ESC50_SYNONYMS.get(requested_scene, requested_scene)
            if requested_scene not in ESC50_TAXONOMY:
                raise ValueError(
                    f"Unsupported background sound '{background_match.group(1)}'. "
                    "Use an ESC-50 label or a supported synonym."
                )
            bg_scene = requested_scene
            continue

        dialogue_lines.append(line)

    for word, syn in ESC50_SYNONYMS.items():
        if word in script_lower:
            if bg_scene == "none":
                bg_scene = syn
            break
    if bg_scene == "none":
        for tax in ESC50_TAXONOMY:
            if tax in script_lower and tax != "none":
                bg_scene = tax
                break
                
    dialogues = []
    idx = 0
    gender_map = {}

    for line in dialogue_lines:
        
        speaker = f"speaker_{idx}"
        text = line
        emotion = "neutral"
        explicit_gender = None
        
        if ":" in line:
            parts = line.split(":", 1)
            speaker_part = parts[0].strip()
            text = parts[1].strip()
            
            # Check for tags in brackets: e.g. john [happy] [male]
            matches = re.findall(r'\[(.*?)\]', speaker_part)
            for m in matches:
                val = m.lower()
                if val in ["neutral", "happy", "sad", "angry", "fear", "surprise", "disgust"]:
                    emotion = val
                elif val in ["male", "female"]:
                    explicit_gender = val
            
            # Clean speaker name by removing all bracketed tags
            speaker = re.sub(r'\[.*?\]', '', speaker_part).strip()
            if not speaker: speaker = f"speaker_{idx}"
                
        if speaker not in gender_map:
            gender_map[speaker] = explicit_gender if explicit_gender else guess_gender(speaker)
            
        dialogues.append(Dialogue(
            idx=idx,
            speaker=speaker,
            gender=gender_map[speaker],
            text=text,
            emotion=emotion,
            pause_after_ms=300
        ))
        idx += 1

    if not dialogues:
        raise ValueError("No dialogue lines found. Add lines in 'Speaker [emotion] [gender]: text' format.")

    return SceneSpec(language=lang, background_scene=bg_scene, dialogues=dialogues)

def parse_script(script: str, mode: str = "auto") -> SceneSpec:
    if mode in ("llm", "auto"):
        try:
            from parser.llm_parser import parse_with_llm
            return parse_with_llm(script)
        except Exception as e:
            print(f"[Warning] LLM Parser failed, falling back to local: {str(e)}")
            if mode == "llm": raise
            return parse_local(script)
    return parse_local(script)
