# TTS Fine-Tuning Instructions

According to the project spec, fine-tuning MMS TTS on Kannada (OpenSLR SLR79) and English (LJSpeech/VCTK) is required.

## Steps

1. Clone the fine-tuning repository:
   ```bash
   git clone https://github.com/ylacombe/finetune-hf-vits.git
   cd finetune-hf-vits
   pip install -r requirements.txt
   ```

2. **Kannada (SLR79)**:
   - Download the dataset from OpenSLR (SLR79) `kn_in_male.zip` and `kn_in_female.zip`.
   - Prepare the dataset into a Hugging Face `datasets` format.
   - You need a checkpoint that includes the VITS discriminator. Run the checkpoint-conversion script provided in the repo.
   - Run fine-tuning:
     ```bash
     accelerate launch run_vits_finetuning.py \
       --model_name_or_path "facebook/mms-tts-kan" \
       --dataset_name "your_prepared_slr79" \
       --output_dir "../models/mms-kan-female"
     ```

3. **English (LJSpeech)**:
   - `ylacombe/mms-tts-eng-train` already exists as a checkpoint.
   - Use LJSpeech to fine-tune female voice.
   
4. Update `config.py` TTS_MODELS environment variables (`TTS_KN_MALE`, `TTS_KN_FEMALE`) to point to your fine-tuned local models.
