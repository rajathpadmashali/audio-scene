# Project Architecture

Here is a very simple diagram showing the journey your text script takes to become a final audio file.

```mermaid
flowchart TD
    UserScript[1. You type a Text Script] --> Parser{2. The Brain (Parser)}
    
    Parser -->|Reads the words| TTS[3. Voice Generator]
    Parser -->|Reads the feeling| DSP[4. Emotion Effects]
    Parser -->|Reads the setting| Ambient[5. Sound Effects Library]
    
    TTS -->|Raw Voice Audio| DSP
    DSP -->|Emotional Voice Audio| Mixer[6. The Audio Mixer]
    Ambient -->|Background Noises| Mixer
    
    Mixer -->|Lowers background noise\nwhen people speak| FinalAudio[7. Final .wav File]
```

### What happens in plain English?
1. **The Brain (Parser)** reads your script and figures out who is talking, how they feel, and where they are.
2. **The Voice Generator** creates raw audio of the words.
3. **The Emotion Effects** mathematically tweak the voice to make it sound happy, sad, or angry.
4. **The Sound Effects Library** (using the ESC-50 Dataset) grabs a background sound (like rain or traffic).
5. **The Audio Mixer** stacks the voices on top of the background sound and saves the final audio file!
