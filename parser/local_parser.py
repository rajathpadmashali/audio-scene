"""
Intelligent local parser for story scripts.

Handles:
  - Context / Characters header blocks for setting & character metadata
  - Name-based gender inference from a curated name database
  - Smart ambient auto-assignment via keyword scoring across all text
  - Auto-emotion detection from dialogue text (classifier + keyword fallback)
  - Punctuation-aware pause calculation
  - Explicit header overrides (Language:, Background:)
  - Bracketed tags: Speaker [emotion] [gender]: text

Backward compatible: explicitly tagged scripts produce the same output.
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from schemas import SceneSpec, Dialogue
from config import (
    ESC50_TAXONOMY, ESC50_SYNONYMS, SCENE_KEYWORDS,
    PAUSE_MAP, PAUSE_SPEAKER_CHANGE_EXTRA, PAUSE_DEFAULT,
    EMOTION_KEYWORDS, NAMES_DIR,
)

# ────────────────────────────────────────────────────────────────────
# Name database (loaded once)
# ────────────────────────────────────────────────────────────────────
_male_names: Set[str] = set()
_female_names: Set[str] = set()
_names_loaded = False


def _load_names() -> None:
    global _male_names, _female_names, _names_loaded
    if _names_loaded:
        return
    male_path = NAMES_DIR / "male_names.txt"
    female_path = NAMES_DIR / "female_names.txt"
    if male_path.exists():
        _male_names = {
            n.strip().lower()
            for n in male_path.read_text(encoding="utf-8").splitlines()
            if n.strip()
        }
    if female_path.exists():
        _female_names = {
            n.strip().lower()
            for n in female_path.read_text(encoding="utf-8").splitlines()
            if n.strip()
        }
    _names_loaded = True


# ────────────────────────────────────────────────────────────────────
# Language detection
# ────────────────────────────────────────────────────────────────────
def detect_lang(script: str) -> str:
    if any('\u0900' <= c <= '\u097F' for c in script):
        return "hi"
    if any('\u0C80' <= c <= '\u0CFF' for c in script):
        return "kn"
    return "en"


# ────────────────────────────────────────────────────────────────────
# Gender inference (layered: explicit → context → name DB → heuristic)
# ────────────────────────────────────────────────────────────────────
def _gender_from_name_db(name: str) -> Optional[str]:
    """Look up a name in the curated male/female name lists."""
    _load_names()
    low = name.lower().strip()
    # Try the full name first, then just the first token (for multi-word speakers)
    tokens = [low] + low.split()
    for tok in tokens:
        if tok in _female_names:
            return "female"
        if tok in _male_names:
            return "male"
    return None


def _gender_from_keywords(speaker: str) -> Optional[str]:
    """Infer gender from role-like keywords in the speaker label."""
    s = speaker.lower()
    female_kw = [
        "woman", "girl", "mother", "mom", "mum", "mrs", "ms", "miss",
        "queen", "lady", "sister", "daughter", "wife", "aunt", "grandma",
        "grandmother", "princess", "heroine", "goddess", "rani", "devi",
        "amma", "akka", "didi", "behen", "madam",
    ]
    male_kw = [
        "man", "boy", "father", "dad", "mr", "king", "lord", "sir",
        "brother", "son", "husband", "uncle", "grandpa", "grandfather",
        "prince", "hero", "god", "raja", "anna", "bhai", "sahab",
    ]
    if any(k in s for k in female_kw):
        return "female"
    if any(k in s for k in male_kw):
        return "male"
    return None


def _gender_from_suffix(speaker: str) -> str:
    """Last-resort heuristic: common feminine name endings."""
    s = speaker.lower().strip()
    if s.endswith(("a", "i", "ee", "ah", "ia", "ie", "ini", "ika",
                   "itha", "amma", "akka", "devi")):
        return "female"
    return "male"


def guess_gender(
    speaker: str,
    context_genders: Optional[Dict[str, str]] = None,
) -> str:
    """
    Multi-layer gender inference:
      1. Context header override (Characters: line)
      2. Role-keyword match (woman, boy, mother, …)
      3. Name database lookup
      4. Suffix heuristic fallback
    """
    # 1. Context override
    if context_genders:
        low = speaker.lower().strip()
        if low in context_genders:
            return context_genders[low]

    # 2. Keywords in speaker label
    kw = _gender_from_keywords(speaker)
    if kw:
        return kw

    # 3. Name database
    db = _gender_from_name_db(speaker)
    if db:
        return db

    # 4. Suffix heuristic
    return _gender_from_suffix(speaker)


# ────────────────────────────────────────────────────────────────────
# Smart ambient auto-assignment
# ────────────────────────────────────────────────────────────────────
def _score_ambient(all_text: str) -> str:
    """
    Score each ESC-50 ambient label by counting keyword hits in the
    combined text (context + all dialogue).  Return the best match
    or "none" if nothing scores.
    """
    text_lower = all_text.lower()
    best_label = "none"
    best_score = 0

    for label, keywords in SCENE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            # Count occurrences; use word-boundary-aware matching
            # to avoid partial matches like "train" inside "training"
            hits = len(re.findall(r"\b" + re.escape(kw) + r"\b", text_lower))
            score += hits
        if score > best_score:
            best_score = score
            best_label = label

    return best_label


# ────────────────────────────────────────────────────────────────────
# Auto-emotion from text
# ────────────────────────────────────────────────────────────────────
def _emotion_from_classifier(text: str) -> Optional[str]:
    """Try the trained emotion classifier; return None if unavailable."""
    try:
        from emotion.infer import get_emotion
        result = get_emotion(text)
        if result and result != "neutral":
            return result
        return None  # Return None if it's neutral or model missing, to allow keyword fallback
    except Exception:
        return None


def _emotion_from_keywords(text: str) -> str:
    """Rule-based emotion detection from dialogue content."""
    text_lower = text.lower()
    best_emotion = "neutral"
    best_score = 0

    for emotion, keywords in EMOTION_KEYWORDS.items():
        # Match standalone words
        score = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw) + r'\b', text_lower))
        if score > best_score:
            best_score = score
            best_emotion = emotion

    return best_emotion


def detect_emotion(text: str) -> str:
    """Auto-detect emotion: classifier first, keyword fallback."""
    # Try classifier
    result = _emotion_from_classifier(text)
    if result is not None:
        return result
    # Keyword fallback
    return _emotion_from_keywords(text)


# ────────────────────────────────────────────────────────────────────
# Punctuation-aware pause calculation
# ────────────────────────────────────────────────────────────────────
def _compute_pause(text: str, next_speaker: Optional[str],
                   current_speaker: str) -> int:
    """
    Compute pause_after_ms based on trailing punctuation and
    whether the next line has a different speaker.
    """
    text = text.rstrip()

    # Check for ellipsis first (before checking single period)
    if text.endswith("...") or text.endswith("…"):
        base = PAUSE_MAP.get("...", 900)
    elif text.endswith("!"):
        base = PAUSE_MAP.get("!", 550)
    elif text.endswith("?"):
        base = PAUSE_MAP.get("?", 450)
    elif text.endswith("."):
        base = PAUSE_MAP.get(".", 500)
    elif text.endswith("—"):
        base = PAUSE_MAP.get("—", 600)
    elif text.endswith(";"):
        base = PAUSE_MAP.get(";", 300)
    elif text.endswith(","):
        base = PAUSE_MAP.get(",", 200)
    else:
        base = PAUSE_DEFAULT

    # Extra gap on speaker change
    if next_speaker is not None and next_speaker != current_speaker:
        base += PAUSE_SPEAKER_CHANGE_EXTRA

    return base


# ────────────────────────────────────────────────────────────────────
# Context header parsing
# ────────────────────────────────────────────────────────────────────
_CONTEXT_RE = re.compile(
    r"^context\s*:\s*(.+)$", re.IGNORECASE
)
_CHARACTERS_RE = re.compile(
    r"^characters?\s*:\s*(.+)$", re.IGNORECASE
)


def _parse_characters_line(line: str) -> Dict[str, str]:
    """
    Parse a Characters line like:
      Characters: Maya (female doctor), Arjun (male guard), Narrator (female)
    Returns {name_lower: gender}
    """
    genders: Dict[str, str] = {}
    # Split by comma to get each character entry
    entries = line.split(",")
    for entry in entries:
        entry = entry.strip()
        if not entry:
            continue
        # Look for parenthesized description
        m = re.match(r"^(\w[\w\s]*?)\s*\(([^)]*)\)\s*$", entry)
        if m:
            name = m.group(1).strip().lower()
            desc = m.group(2).lower()
            if "female" in desc or "woman" in desc or "girl" in desc:
                genders[name] = "female"
            elif "male" in desc or "man" in desc or "boy" in desc:
                genders[name] = "male"
            else:
                # Try inferring from the name itself
                db_gender = _gender_from_name_db(name)
                if db_gender:
                    genders[name] = db_gender
        else:
            # No parenthesized description; just a name
            name = entry.strip().lower()
            db_gender = _gender_from_name_db(name)
            if db_gender:
                genders[name] = db_gender
    return genders


# ────────────────────────────────────────────────────────────────────
# Main parser
# ────────────────────────────────────────────────────────────────────
def parse_local(script: str) -> SceneSpec:
    lang = detect_lang(script)
    bg_scene = "none"
    explicit_bg = False
    context_text = ""
    context_genders: Dict[str, str] = {}

    dialogue_lines: List[str] = []

    for line in script.strip().splitlines():
        line = line.strip()
        if not line:
            continue

        # ── Language header ──
        language_match = re.match(
            r"^(?:language|lang)\s*:\s*(\w+)\s*$", line, re.IGNORECASE
        )
        if language_match:
            explicit_lang = language_match.group(1).lower()
            if explicit_lang not in {"en", "hi", "kn"}:
                raise ValueError(
                    f"Unsupported language '{explicit_lang}'. Use en, hi, or kn."
                )
            lang = explicit_lang
            continue

        # ── Background header ──
        background_match = re.match(
            r"^(?:background(?:\s+sound)?|background_scene)\s*:\s*(.+?)\s*$",
            line, re.IGNORECASE,
        )
        if background_match:
            requested = (
                background_match.group(1).strip().lower().replace(" ", "_")
            )
            requested = ESC50_SYNONYMS.get(requested, requested)
            if requested not in ESC50_TAXONOMY:
                raise ValueError(
                    f"Unsupported background sound "
                    f"'{background_match.group(1)}'. "
                    "Use an ESC-50 label or a supported synonym."
                )
            bg_scene = requested
            explicit_bg = True
            continue

        # ── Context header ──
        ctx_match = _CONTEXT_RE.match(line)
        if ctx_match:
            context_text = ctx_match.group(1).strip()
            continue

        # ── Characters header ──
        char_match = _CHARACTERS_RE.match(line)
        if char_match:
            context_genders = _parse_characters_line(char_match.group(1))
            continue

        # ── Everything else is a dialogue line ──
        dialogue_lines.append(line)

    # ── Collect all text for ambient scoring ──
    all_text_parts = [context_text]

    # ── Parse dialogue lines ──
    dialogues: List[Dialogue] = []
    idx = 0
    gender_map: Dict[str, str] = {}
    parsed_entries: List[Tuple[str, str, str, Optional[str]]] = []

    for line in dialogue_lines:
        speaker = f"speaker_{idx}"
        text = line
        emotion = None  # None means "auto-detect"
        explicit_gender = None
        explicit_emotion = False

        if ":" in line:
            parts = line.split(":", 1)
            speaker_part = parts[0].strip()
            text = parts[1].strip()

            # Check for tags in brackets: e.g. john [happy] [male]
            matches = re.findall(r'\[(.*?)\]', speaker_part)
            for m_val in matches:
                val = m_val.lower()
                if val in (
                    "neutral", "happy", "sad", "angry",
                    "fear", "surprise", "disgust",
                ):
                    emotion = val
                    explicit_emotion = True
                elif val in ("male", "female"):
                    explicit_gender = val

            # Clean speaker name by removing all bracketed tags
            speaker = re.sub(r'\[.*?\]', '', speaker_part).strip()
            if not speaker:
                speaker = f"speaker_{idx}"

        # ── Gender resolution ──
        if speaker not in gender_map:
            if explicit_gender:
                gender_map[speaker] = explicit_gender
            else:
                gender_map[speaker] = guess_gender(
                    speaker, context_genders
                )

        # ── Emotion resolution ──
        if emotion is None:
            emotion = detect_emotion(text)

        all_text_parts.append(text)
        parsed_entries.append((speaker, text, emotion, explicit_gender))
        idx += 1

    if not parsed_entries:
        raise ValueError(
            "No dialogue lines found. "
            "Add lines in 'Speaker [emotion] [gender]: text' format."
        )

    # ── Smart ambient auto-assignment ──
    if not explicit_bg:
        # First try synonym scan (original behaviour, for backward compat)
        script_lower = script.lower()
        for word, syn in ESC50_SYNONYMS.items():
            if word in script_lower:
                bg_scene = syn
                break

        # Then try keyword scoring on all collected text
        if bg_scene == "none":
            combined_text = " ".join(all_text_parts)
            bg_scene = _score_ambient(combined_text)

        # Final fallback: scan ESC50_TAXONOMY directly
        if bg_scene == "none":
            for tax in ESC50_TAXONOMY:
                if tax in script_lower and tax != "none":
                    bg_scene = tax
                    break

    # ── Build Dialogue objects with smart pauses ──
    for i, (speaker, text, emotion, _) in enumerate(parsed_entries):
        next_speaker = (
            parsed_entries[i + 1][0] if i + 1 < len(parsed_entries) else None
        )
        pause_ms = _compute_pause(text, next_speaker, speaker)

        dialogues.append(Dialogue(
            idx=i,
            speaker=speaker,
            gender=gender_map[speaker],
            text=text,
            emotion=emotion,
            pause_after_ms=pause_ms,
        ))

    return SceneSpec(
        language=lang, background_scene=bg_scene, dialogues=dialogues
    )


def parse_script(script: str, mode: str = "auto") -> SceneSpec:
    if mode in ("llm", "auto"):
        try:
            from parser.llm_parser import parse_with_llm
            res = parse_with_llm(script)
            if res.background_scene == "none":
                res.background_scene = _score_ambient(script)
            return res
        except Exception as e:
            print(
                f"[Warning] LLM Parser failed, falling back to local: "
                f"{str(e)}"
            )
            if mode == "llm":
                raise
            return parse_local(script)
    return parse_local(script)
