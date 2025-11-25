import os
import shutil
import subprocess
from tqdm import tqdm
from pydub import AudioSegment

# Define input items (directories containing audio files)


root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
input_items = [
    "tarkasangraha/",
]

base_dirs = [os.path.join(root_dir, "SwaraSangraha/", input_item, "audio/") for input_item in input_items]


output_root = "demucs"  # Root output directory
temp_dir = "demucs_temp"  # Temporary directory for processing
chunk_length = 120  # Chunk length in seconds (2 minutes)


def get_audio_files():
    """Retrieve all audio files from input directories."""
    audio_files = []
    
    for item in base_dirs:
        if os.path.isdir(item):  
            for dirpath, _, filenames in os.walk(item):
                for file in filenames:
                    if file.endswith((".mp3", ".wav", ".flac", ".m4a", ".ogg")):
                        audio_files.append(os.path.join(dirpath, file))
        elif os.path.isfile(item):  
            if item.endswith((".mp3", ".wav", ".flac", ".m4a", ".ogg")):
                audio_files.append(item)

    return audio_files


def split_audio(input_audio, chunk_length=120):
    """Split audio into chunks of specified length and return chunk file paths."""
    os.makedirs(temp_dir, exist_ok=True)
    track_name = os.path.splitext(os.path.basename(input_audio))[0]
    chunk_folder = os.path.join(temp_dir, track_name)
    os.makedirs(chunk_folder, exist_ok=True)

    # Load audio
    audio = AudioSegment.from_file(input_audio)
    duration = len(audio) / 1000  # Convert to seconds
    chunks = []

    for i in range(0, int(duration), chunk_length):
        chunk_path = os.path.join(chunk_folder, f"{track_name}_part{i//chunk_length}.wav")
        start_time = i * 1000  # Convert to milliseconds
        end_time = min((i + chunk_length) * 1000, len(audio))
        chunk = audio[start_time:end_time]
        chunk.export(chunk_path, format="wav")
        chunks.append(chunk_path)

    return chunks


def merge_audio(chunks, output_path):
    """Merge processed chunks back into a single audio file."""
    combined = AudioSegment.silent(duration=0)
    
    # **Fix sorting logic: Extract number from "_partX_vocals.wav"**
    def extract_chunk_number(filename):
        """Extracts numeric part from filenames like 'track_part0_vocals.wav'."""
        base_name = os.path.basename(filename)
        parts = base_name.split("_part")[-1].split("_vocals.wav")[0]
        return int(parts) if parts.isdigit() else float('inf')  # Put non-numeric at the end

    sorted_chunks = sorted(chunks, key=extract_chunk_number)

    for chunk in sorted_chunks:
        combined += AudioSegment.from_file(chunk)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    combined.export(output_path, format="wav")



def remove_old_chunks(output_dir, track_name):
    """Remove old chunk files if found."""
    chunk_files = [f for f in os.listdir(output_dir) if f.startswith(track_name + "_part") and f.endswith("_vocals.wav")]
    if chunk_files:
        tqdm.write(f"🗑️ Removing old chunks for: {track_name}")
        for chunk_file in chunk_files:
            os.remove(os.path.join(output_dir, chunk_file))


def process_single_audio(input_audio):
    """Process audio by splitting, running Demucs on chunks, and merging."""
    root_dir = next((d for d in base_dirs if input_audio.startswith(d)), None) or os.path.dirname(input_audio)
    relative_path = os.path.relpath(input_audio, root_dir)
    track_name = os.path.splitext(os.path.basename(input_audio))[0]

    output_dir = os.path.join(output_root, os.path.dirname(relative_path))
    final_output = os.path.join(output_dir, f"{track_name}.wav")

    # **Check if the final processed audio already exists**
    if os.path.exists(final_output):
        return f"✅ Skipped (Already Processed): {final_output}"

    # **Check for old chunk files and remove if necessary**
    if os.path.exists(output_dir):
        remove_old_chunks(output_dir, track_name)

    os.makedirs(output_dir, exist_ok=True)

    tqdm.write(f"🎵 Processing: {input_audio}")

    # Split audio into chunks
    chunks = split_audio(input_audio, chunk_length)

    processed_chunks = []
    
    for chunk in tqdm(chunks, desc=f"Processing {track_name}", unit="chunk"):
        chunk_name = os.path.basename(chunk).replace(".wav", "")
        temp_chunk_dir = os.path.join(temp_dir, "htdemucs", chunk_name)

        # Run Demucs on the chunk
        subprocess.run(["demucs", "--two-stems=vocals", "-o", temp_dir, chunk], check=True)

        vocals_path = os.path.join(temp_chunk_dir, "vocals.wav")

        if os.path.exists(vocals_path):
            processed_chunk_path = os.path.join(output_dir, f"{chunk_name}_vocals.wav")
            shutil.move(vocals_path, processed_chunk_path)
            processed_chunks.append(processed_chunk_path)
        else:
            tqdm.write(f"❌ Error processing: {chunk}")

    # Merge processed chunks
    if processed_chunks:
        merge_audio(processed_chunks, final_output)
        result = f"✅ Merged vocals: {final_output}"
    else:
        result = f"❌ No chunks processed for {input_audio}"

    shutil.rmtree(temp_dir, ignore_errors=True)  # Cleanup temporary files



    return result


def process_audio_files():
    """Process all audio files with batch processing on chunks."""
    audio_files = get_audio_files()
    
    if not audio_files:
        print("❌ No audio files found in the given directories!")
        return

    print(f"🔍 Found {len(audio_files)} audio files. Processing...\n")

    for audio in tqdm(audio_files, desc="Overall Progress", unit="file"):
        result = process_single_audio(audio)
        tqdm.write(result)  


process_audio_files()
