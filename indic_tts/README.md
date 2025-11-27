# Indic TTS - Telugu Text-to-Speech

Offline Telugu text-to-speech using [Indic Parler-TTS](https://huggingface.co/ai4bharat/indic-parler-tts) from AI4Bharat.

## Setup

1. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install PyTorch with CUDA support:
```bash
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu130
```

3. Install other dependencies:
```bash
pip install -r requirements.txt
```

## Usage

```bash
python test_parler.py
```

This generates `telugu_parler.wav` with the sample Telugu text.

## Customization

Edit `test_parler.py` to change:
- `telugu_text`: The Telugu text to synthesize
- `voice_prompt`: Description of the desired voice characteristics
- `output_filename`: Output WAV file path

## Project Structure

```
indic_tts/
├── test_parler.py      # Main TTS script
├── requirements.txt    # Python dependencies
├── README.md
└── models/
    ├── indic-parler-tts/   # Main TTS model (~3.5GB)
    └── flan-t5-large/      # Description tokenizer
```

## Offline Operation

All models are stored locally in the `models/` directory. No internet connection required after initial setup.
