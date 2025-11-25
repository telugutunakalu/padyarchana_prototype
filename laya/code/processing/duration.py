import os
from mutagen import File
from tqdm import tqdm
from collections import defaultdict

# List of base directories containing subdirectories with audio files
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sub_dirs = [
    "amarakosha/",
    "ashtadhyayi/",
    "ramayana/",
    "meghaduta/",
    "tarkasangraha/",
    "yogasutra/",
]

base_dirs = [os.path.join(root_dir, "SwaraSangraha/", sub_dir, "audio/") for sub_dir in sub_dirs]

def get_audio_files(directories):
    """Recursively fetch all audio files from the given directories."""
    audio_files = defaultdict(list)  # Store files per base directory
    for base_dir in directories:
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith((".mp3", ".wav", ".ogg", ".flac", ".m4a")):  # Supported formats
                    audio_files[base_dir].append(os.path.join(root, file))
    return audio_files

def get_audio_durations(audio_files):
    """Calculate total duration and duration per base directory."""
    total_duration = 0  # Total duration in seconds
    base_dir_durations = defaultdict(float)  # Store duration per base directory

    for base_dir, files in audio_files.items():
        for file_path in tqdm(files, desc=f"Processing {base_dir}", unit="file"):
            try:
                audio = File(file_path)  # Detect format & read metadata
                if audio and audio.info:
                    duration = audio.info.length  # Get duration in seconds
                    total_duration += duration
                    base_dir_durations[base_dir] += duration  # Add duration to respective base directory
            except Exception as e:
                print(f"❌ Error processing {file_path}: {e}")

    return total_duration, base_dir_durations

# Fetch all audio files from the given directories
audio_files = get_audio_files(base_dirs)

# Calculate total duration & per-base directory durations
total_seconds, base_dir_durations = get_audio_durations(audio_files)

# Convert total duration to HH:MM:SS format
def format_duration(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    sec = int(seconds % 60)
    return f"{hours}h {minutes}m {sec}s ({seconds:.2f} seconds)"

# Print total duration
print(f"\n🎵 Total Audio Duration: {format_duration(total_seconds)}")

# Print duration per base directory
print("\n📂 Duration per Base Directory:")
for base_dir, duration in base_dir_durations.items():
    print(f"  📁 {base_dir}: {format_duration(duration)}")
