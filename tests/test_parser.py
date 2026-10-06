import pytest
from pathlib import Path
from parser.local_parser import parse_local

def test_local_parser_en():
    script = "Language: en\nBackground: thunderstorm\nnarrator: The storm was brewing.\nmale_1: I am scared!"
    scene = parse_local(script)
    
    assert scene.language == "en"
    assert scene.background_scene == "thunderstorm"
    assert len(scene.dialogues) == 2
    assert scene.dialogues[1].speaker == "male_1"

def test_local_parser_hi():
    script = "Language: hi\nnarrator: नमस्ते दुनिया"
    scene = parse_local(script)
    assert scene.language == "hi"

@pytest.mark.parametrize(
    ("filename", "language", "background"),
    [
        ("en.txt", "en", "rain"),
        ("hi.txt", "hi", "thunderstorm"),
        ("kn.txt", "kn", "rain"),
    ],
)
def test_example_scripts_include_language_background_and_emotions(
    filename, language, background
):
    script_path = Path(__file__).parents[1] / "examples" / filename
    scene = parse_local(script_path.read_text(encoding="utf-8"))

    assert scene.language == language
    assert scene.background_scene == background
    assert [dialogue.emotion for dialogue in scene.dialogues] == [
        "neutral",
        "fear",
        "happy",
    ]
    assert [dialogue.gender for dialogue in scene.dialogues] == [
        "female",
        "female",
        "male",
    ]

def test_local_parser_rejects_unknown_explicit_background():
    with pytest.raises(ValueError, match="Unsupported background sound"):
        parse_local("Language: en\nBackground: spaceship\nMaya [neutral] [female]: Hello.")

def test_smart_ambient_inference():
    script = "John: I can't believe it's pouring outside. Let's find an umbrella."
    scene = parse_local(script)
    assert scene.background_scene == "rain"

def test_name_based_gender_inference():
    script = "Emma: Let's go!\nJames: Okay."
    scene = parse_local(script)
    assert scene.dialogues[0].gender == "female"
    assert scene.dialogues[1].gender == "male"

def test_punctuation_pauses():
    script = "John: Hello. How are you?\nMaya: I'm good..."
    scene = parse_local(script)
    # Line 1 ends in ?, plus speaker changes -> 450 + 200 = 650
    assert scene.dialogues[0].pause_after_ms == 650
    # Line 2 ends in ..., no speaker change (end of script) -> 900
    assert scene.dialogues[1].pause_after_ms == 900

def test_context_header():
    script = "Context: A creepy haunted house.\nCharacters: Alex (female teenager), Sam (male).\nAlex: Did you hear that?"
    scene = parse_local(script)
    assert scene.background_scene == "crow" # haunted -> crow
    assert scene.dialogues[0].gender == "female"

def test_emotion_keyword_fallback():
    script = "Sam: I am absolutely terrified of ghosts!"
    scene = parse_local(script)
    assert scene.dialogues[0].emotion == "fear"
