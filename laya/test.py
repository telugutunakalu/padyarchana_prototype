import torch
import torchaudio
from pathlib import Path

# Load official silero VAD model from torch.hub
model = torch.hub.load(repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=True)

# Load audio (mono, 16kHz)
wav, sr = torchaudio.load("SwaraSangraha/ramayana/audio/1/1.mp3")
if sr != 16000:
    wav = torchaudio.functional.resample(wav, sr, 16000)
    sr = 16000

# Apply VAD
from silero.utils import get_speech_timestamps, save_audio
speech_timestamps = get_speech_timestamps(wav[0], model, sampling_rate=sr)

# Print VAD segments
for i, ts in enumerate(speech_timestamps):
    start_sec = ts['start'] / sr
    end_sec = ts['end'] / sr
    print(f"Segment {i+1}: {start_sec:.2f}s - {end_sec:.2f}s")

# Optional: Save segments
for i, ts in enumerate(speech_timestamps):
    segment = wav[:, ts['start']:ts['end']]
    save_audio(f"segment_{i+1}.wav", segment, sampling_rate=sr)
