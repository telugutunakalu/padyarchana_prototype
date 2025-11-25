from pydub import AudioSegment
from pydub.silence import detect_nonsilent
import os
from tqdm import tqdm

def segment_audio_precise(input_path, output_dir,
                          min_silence_len=700, silence_thresh_dB=-40, keep_silence=200):
    # Extract base filename
    base_filename = os.path.splitext(os.path.basename(input_path))[0]

    print(f"\n📥 Loading audio from: {input_path}")
    audio = AudioSegment.from_file(input_path)

    print(f"🔍 Detecting non-silent segments...")
    nonsilent_ranges = detect_nonsilent(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh_dB
    )

    if not nonsilent_ranges:
        print("⚠️ No speech segments detected. Try adjusting silence parameters.")
        return

    os.makedirs(output_dir, exist_ok=True)
    print(f"💾 Exporting {len(nonsilent_ranges)} segments to: {output_dir}")

    for i, (start_ms, end_ms) in tqdm(enumerate(nonsilent_ranges, start=1), total=len(nonsilent_ranges), desc="Exporting"):
        # Apply optional context padding
        start_ms = max(0, start_ms - keep_silence)
        end_ms = min(len(audio), end_ms + keep_silence)

        # Extract segment
        segment = audio[start_ms:end_ms]


        out_filename = f"{base_filename}-{start_ms}-{end_ms}.wav"
        out_path = os.path.join(output_dir, out_filename)

        segment.export(out_path, format="wav")

    print("✅ Segmentation complete.\n")

# Example usage
if __name__ == "__main__":
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    input_audio_file = os.path.join(root_dir, "SwaraSangraha/ramayana/audio/1/1.mp3")
    output_folder = os.path.join(root_dir, "segmented")

    segment_audio_precise(
        input_audio_file,
        output_folder,
        min_silence_len=35,
        silence_thresh_dB=-30,
        keep_silence=20
    )
