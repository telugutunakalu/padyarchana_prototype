import torch
from pathlib import Path
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer
import soundfile as sf

# Local model paths (relative to script location)
SCRIPT_DIR = Path(__file__).parent
MODEL_DIR = SCRIPT_DIR / "models" / "indic-parler-tts"
DESCRIPTION_TOKENIZER_DIR = SCRIPT_DIR / "models" / "flan-t5-large"

def generate_telugu_speech(text, description, output_filename="output.wav"):
    """
    Generates Telugu speech using Indic Parler-TTS (offline mode).

    Args:
        text (str): The Telugu text to synthesize.
        description (str): The semantic prompt describing the voice.
        output_filename (str): The path to save the wav file.
    """

    # Check for GPU
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    print(f"Loading model on {device}...")

    # Load Model and Tokenizers from local paths
    model = ParlerTTSForConditionalGeneration.from_pretrained(MODEL_DIR).to(device)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    description_tokenizer = AutoTokenizer.from_pretrained(DESCRIPTION_TOKENIZER_DIR)

    # Tokenize the Description (Prompt)
    description_input_ids = description_tokenizer(description, return_tensors="pt").to(device)

    # Tokenize the Content (Telugu Text)
    prompt_input_ids = tokenizer(text, return_tensors="pt").to(device)

    print("Generating audio...")
    
    # Generate
    generation = model.generate(
        input_ids=description_input_ids.input_ids,
        attention_mask=description_input_ids.attention_mask,
        prompt_input_ids=prompt_input_ids.input_ids,
        prompt_attention_mask=prompt_input_ids.attention_mask,
        do_sample=True,   # Enable sampling for variety
        temperature=1.0   # Control creativity/variance
    )

    # Convert to Numpy and Save
    audio_arr = generation.cpu().numpy().squeeze()
    sf.write(output_filename, audio_arr, model.config.sampling_rate)
    print(f"Success! Audio saved to {output_filename}")

# --- Usage Example ---
if __name__ == "__main__":
    # Telugu text (Vemana Padyam - a famous Telugu poem)
    telugu_text = "అల్పుడెపుడుబల్కు నాడంబరముగాను, సజ్జనుండు పలుకు చల్లగాను, కంచుమ్రోగినట్లు కనకంబుమ్రోగునా, విశ్వదాభిరామ వినురవేమ."

    # Voice description for Telugu
    # Recommended Telugu speakers: Prakash (male), Lalitha (female), Kiran
    voice_prompt = "Lalitha speaks with a clear, expressive voice at a moderate pace. The recording is of very high quality with no background noise."

    generate_telugu_speech(telugu_text, voice_prompt, "telugu_parler.wav")