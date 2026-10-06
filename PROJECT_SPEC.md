# Multilingual Audio Scene Generator — Software Spec (v2, simplified)

Source of truth for any dev agent. Implement against §4 contracts; update this file if a contract changes.

## 1. Goal
Input: scene/script text in ONE language per run (EN, HI or KN).
Output: one `.wav` = emotional multi-speaker dialogue + background ambient sound (+ optional music bed), speech always clearly audible (ducking). Delivered as a Gradio app; demo is recorded.

## 2. Decisions (locked)
| Topic | Decision |
|---|---|
| Parser | Groq API (OpenAI-compatible), model via `GROQ_MODEL` env (check Groq docs for a current model with JSON-schema support; else JSON mode + pydantic validation). Local rule-based fallback |
| TTS | **Meta MMS-TTS (VITS, ~83M params), FINE-TUNED** with `ylacombe/finetune-hf-vits` (mentor requirement): Kannada male+female on OpenSLR SLR79 (required), English male+female (LJSpeech/VCTK), Hindi only if a clean dataset is obtained (§8.3). Base `facebook/mms-tts-{eng,hin,kan}` is the fallback. CPU inference |
| Emotion in speech | MMS has no emotion control → **DSP emotion presets** (§5.2) on top of MMS output. Approximate; state in report |
| Gender | Real male/female voices from per-gender fine-tuned checkpoints; pitch-shift only where no fine-tuned voice exists (§5.2) |
| Ambient | ESC-50 clips, label→folder lookup. No CLAP, no vector search |
| Music | Optional bed from small royalty-free bank, chosen by dominant emotion (§5.3) |
| Language mixing | None. One language per script |
| Compute | Local only (4 GB GPU for training, CPU for inference). No Colab dependency (Kaggle free GPU = fallback if local training fails) |
| UI | Gradio |
| Dropped | Parler-TTS, CLAP, Freesound extras, code-switching, IndicTrans2, MOS listening test |

## 3. Architecture
```
Script ─▶ [1 Parser] ─▶ SceneSpec
             ├─▶ [2 MMS TTS + emotion DSP] ─▶ speech timeline ─┐
             └─▶ [3 Ambient(+music) lookup] ───────────────────┤
                                                               ▼
                                         [4 Mixer: loudnorm + ducking] ─▶ final.wav
                                                               ▼
                                                      [5 Gradio UI]
```
Stack: Python 3.11, torch, transformers, librosa, soundfile, pyloudnorm, pydub+ffmpeg, pydantic, groq (or openai SDK w/ base_url `https://api.groq.com/openai/v1`), gradio, scikit-learn, matplotlib, pytest.

## 4. Contracts (pydantic)
```json
SceneSpec = {
  "language": "en|hi|kn",
  "background_scene": "<ESC-50 label or 'none'>",
  "dialogues": [
    {"idx":0,"speaker":"male_1","gender":"male|female",
     "text":"<native script>",
     "emotion":"neutral|happy|sad|angry|fear|surprise|disgust",
     "pause_after_ms":400}
  ]
}
TTSResult={idx,wav_path,sr,duration_s}   MixResult={wav_path,duration_s,lufs}
```
Text must be native script (Devanagari/Kannada), not romanized. Reject unknown enums. Scene label must be in the taxonomy (§6); the LLM prompt includes the exact list plus the synonym map.

## 5. Modules
### 5.1 parser/
- `llm_parser.py`: Groq, temperature 0, retry ×2 on schema failure → SceneSpec.
- `local_parser.py` (fallback on error/429/no key): language by Unicode script; split lines on quotes/newlines/`Name:`; gender default alternate by speaker; scene by keyword→label map (config); emotion via trained classifier (§8.1).
- `parse(script, mode="llm|local|auto")`; auto = Groq then local.

### 5.2 tts/ (MMS + emotion DSP)
- Load `VitsModel` + tokenizer per language lazily; if `tokenizer.is_uroman` is true, run `uroman` first (check for kan/hin on first run).
- Checkpoint registry `config.TTS_MODELS[lang][gender]` → path of fine-tuned model (e.g. `models/mms-kan-female`), else base model. Missing gender → use available voice and pitch-shift ±4 semitones (librosa `pitch_shift`); record base-voice gender by listening once.
- Emotion presets (speaking_rate via model config before generate; pitch semitones; gain dB). Starting values, tune by ear:

| emotion | rate | pitch | gain | extra |
|---|---|---|---|---|
| neutral | 1.00 | 0 | 0 | – |
| happy | 1.10 | +2 | +1 | – |
| sad | 0.85 | −2 | −3 | low-pass 4 kHz |
| angry | 1.12 | +1 | +4 | soft clip (tanh drive 1.5) |
| fear | 1.18 | +3 | −1 | 6 Hz tremolo depth 0.1 |
| surprise | 1.05 | +4 | +2 | – |
| disgust | 0.92 | −1 | 0 | – |
- Resample to 24 kHz mono. Cache by hash(text,lang,gender,emotion).
- Honest limitation for report: emotion is prosodic/DSP approximation, validated by listening + (optional) classifier-free A/B in demo.

### 5.3 ambient/
- `scripts/download_esc50.py`: download `https://github.com/karoldvl/ESC-50/archive/master.zip` (or git clone), extract to `data/esc50/`.
- `build_bank.py`: from `meta/esc50.csv`, copy selected classes to `data/ambient_bank/<label>/`. Pick random clip; loop with 1 s crossfade to length (clips are 5 s, so loop is mandatory).
- Music (optional): `data/music/{calm,happy,sad,tense}.mp3`, 4 royalty-free tracks the user downloads manually (CC0/CC-BY, e.g. Pixabay/FMA/Incompetech; record license in `data/music/LICENSES.md`). Pick by dominant emotion: happy/surprise→happy, sad→sad, angry/fear/disgust→tense, else calm. UI toggle; missing files → skip silently.
- ESC-50 contains sound effects, not music.

## 6. Taxonomy (ESC-50 only)
rain, thunderstorm, wind, sea_waves, crackling_fire, crickets, chirping_birds, rooster, dog, cat, crow, car_horn, engine, train, siren, church_bells, clock_tick, keyboard_typing, door_knock, footsteps, clapping, laughing, crying_baby, vacuum_cleaner, helicopter, airplane, `none`.
Synonym map in config (e.g. storm→thunderstorm, traffic→car_horn, ocean/beach→sea_waves, village→rooster, office→keyboard_typing, temple→church_bells). No match → `none`.
ESC-50 license CC BY-NC: academic use only; state in README.

## 7. Mixer
1. Timeline: concat speech in idx order + `pause_after_ms`; record spans.
2. Loudness (pyloudnorm): speech −20 LUFS, ambient −32, music −34.
3. Ambient/music looped to length + 1 s tail.
4. Ducking: envelope gain 0 dB outside speech, `DUCK_DB=-12` inside; 150 ms attack, 400 ms release on 10 ms frames; applied to ambient and music.
5. Sum, limit to −1 dBFS, normalize −16 LUFS, export 44.1 kHz 16-bit WAV + `timeline.json`.
Tests: ambient RMS ≥10 dB below speech RMS during speech; no clipping; duration ≈ timeline + tail.

## 8. Datasets, training, evaluation (COMPULSORY)
### 8.1 Emotion classifier — dataset: GoEmotions
- Model: `distilbert-base-multilingual-cased`, fp16, batch 16, max_len 64 (fits 4 GB).
- Labels: 28 → 7 (Ekman + neutral) via fixed mapping file `emotion/label_map.json`.
- Train on English GoEmotions train; validate on val; test on test split.
- Cross-lingual test: 150 sentences/language (HI, KN) sampled from GoEmotions test, translated with the Groq LLM, then hand-checked by you; report zero-shot transfer honestly.
- Report: train/val loss curves, accuracy, macro-F1 (EN, HI, KN), per-class precision/recall, confusion matrix → `reports/emotion/`.
- Role at runtime: fallback parser emotion + agreement % vs LLM labels on demo scripts.
### 8.2 Ambient classifier — dataset: ESC-50
- ResNet-18 (ImageNet init, 1-channel adapt) on log-mel (128 mel, 5 s @ 22.05 kHz), official 5 folds, light SpecAugment, ~30 epochs/fold (reduce if slow).
- Report: per-fold + mean accuracy, loss/acc curves, confusion matrix (for the taxonomy classes) → `reports/ambient/`.
- Role at runtime: verify the chosen ambient clip classifies to the requested label (shown in UI as confidence).
### 8.3 TTS fine-tuning (COMPULSORY) — datasets: OpenSLR SLR79 (Kannada), LJSpeech + VCTK (English), Hindi optional
- Tool: `github.com/ylacombe/finetune-hf-vits`. Fine-tuning needs a checkpoint that includes the VITS discriminator: `ylacombe/mms-tts-eng-train` exists; for `kan`/`hin` build one with the repo's checkpoint-conversion script (check its README for exact steps).
- **Kannada (required):** OpenSLR SLR79 (`kn_in_female.zip`, `kn_in_male.zip`, `line_index_*.tsv`; Google, CC BY-SA 4.0, 16 kHz, ~2000 lines per gender). Train one model per gender on 500–1000 clips each (2–10 s, mono 16 kHz, loudness-normalized, transcript sanity-checked). Split 90/5/5 by sentence.
- **English:** LJSpeech (female, public domain) and one male VCTK speaker (CC BY 4.0) → `mms-tts-eng-train`.
- **Hindi:** no clean open single-speaker TTS set verified. Try IndicTTS (IITM) or SPICOR/SYSPIN (IISc) via their request forms; if not obtained, Hindi uses base MMS (+pitch shift) and the report says so. Do not use Common Voice (noisy).
- Compute: model is small; try local 4 GB GPU (fp16, batch 4, gradient accumulation, clips ≤10 s). If OOM, use Kaggle free GPU (needs account). Public MMS fine-tunes reached usable voices in ~20 min on 80–150 clips; use more data for quality.
- Logs per run: total/mel/KL/duration/generator/discriminator/feature-matching losses, validation mel loss curve → `reports/tts_finetune/`.
- Evaluation, base vs fine-tuned, 50 held-out sentences per voice: (a) Whisper CER/WER; (b) median F0 via `librosa.pyin` (male low, female high → evidence of real gender control); (c) mel-spectrogram comparison vs ground truth; (d) optional DTW-MCD. Report honestly: fine-tuning mainly adapts voice/prosody to the target speaker; CER may not improve.
- Emotion is still DSP (§5.2) applied on the fine-tuned outputs. Fine-tuned models inherit MMS CC-BY-NC.

### 8.4 TTS intelligibility — dataset: FLEURS (en_us, hi_in, kn_in test)
- Synthesize 50 sentences/language with base and fine-tuned MMS (neutral); transcribe with Whisper (`small`); report WER (EN) and CER+WER (HI, KN) → `reports/tts/`. Also compare neutral vs each emotion preset on 10 sentences (WER delta) to show DSP doesn't destroy intelligibility.
### 8.5 Pipeline demo metrics
Ducking check (dB margin), end-to-end latency per scene length, 3 reference scripts (one per language) with audio + spectrogram figures.

## 9. Repo layout
```
audio-scene/
  app.py  config.py  schemas.py  cli.py
  parser/{llm_parser,local_parser}.py
  emotion/{data_prep,train,infer,label_map.json}
  tts/{mms,emotion_dsp,cache}.py  tts/finetune/{prep_slr79,prep_ljspeech,train_config.json,run.md}
  ambient/{bank,classifier,train_resnet}.py
  mixer/{timeline,ducking,mix}.py
  scripts/{download_esc50,eval_tts_fleurs}.py
  data/ reports/ tests/ README.md PROJECT_SPEC.md requirements.txt
```
Env: `GROQ_API_KEY`, `GROQ_MODEL`, `DEVICE=auto|cuda|cpu`, `HF_HOME`.

## 10. Build order
1. schemas/config + mixer + tests (dummy wavs).
2. Base MMS TTS + emotion DSP + local parser → offline CLI end-to-end (fine-tuned voices plug in later via `TTS_MODELS`).
3. ESC-50 download, bank, ambient lookup + loop.
4. Groq parser + auto fallback.
5. Gradio UI (script box, parser mode, music toggle, duck slider; outputs audio, SceneSpec JSON, per-line clips).
6. Emotion classifier train/eval.
7. ResNet ESC-50 train/eval; hook verification into UI.
8. TTS fine-tuning (Kannada m/f first, then English, Hindi if data) + §8.3 eval; swap checkpoints into `TTS_MODELS`.
9. FLEURS TTS eval; reports; record demo.

## 11. Acceptance
- CLI and Gradio produce a mixed WAV for EN, HI, KN reference scripts: distinct audible emotions per line, matching ambient, speech ≥10 dB over background.
- Works offline (local parser) and online (Groq).
- Reports in `reports/` contain all metrics in §8 with plots.
- Tests pass: schemas, fallback parser, emotion DSP (length/finite output), ducking, loop crossfade.

## 12. Risks
- Fine-tuning may not fit 4 GB or may overfit → Kaggle fallback, early stopping on val mel loss, keep base model as fallback.
- MMS emotion is DSP approximation → tune presets by ear, document limitation.
- MMS Kannada/Hindi voice may sound robotic → expected; report WER/CER.
- Cross-lingual emotion transfer weaker than EN → report per-language honestly.
- ESC-50 lacks cafe/market → synonym map or `none`.
- Groq limits/data policy → fallback; no private data.
- MMS CC-BY-NC, ESC-50 CC BY-NC → non-commercial only.

## 13. Agent rules
Stick to §4 types, no hardcoded keys/model ids, each module ships a test, keep scope to this sheet (no added backends).
