import pytest
from pathlib import Path
from parser.local_parser import parse_local

def test_local_parser_en():
    script = "narrator: The storm was brewing.\nmale_1: I am scared!"
    scene = parse_local(script)
    
    assert scene.language == "en"
    assert scene.background_scene == "thunderstorm"
    assert len(scene.dialogues) == 2
    assert scene.dialogues[1].speaker == "male_1"

def test_local_parser_hi():
    script = "narrator: नमस्ते दुनिया"
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
        parse_local("Language: en\nBackground: forest\nMaya [neutral] [female]: Hello.")
