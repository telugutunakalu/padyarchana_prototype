#!/usr/bin/env python
import os
import json
import librosa

def segment_sloka_to_json(input_audio_path, output_json_path, top_db=35, frame_length=1024, hop_length=256, min_duration=0.2):
    """
    Processes a sloka chanting audio file and outputs a JSON with each sloka's timestamp.
    
    It first detects non-silent intervals using librosa.effects.split. The first interval
    remains as is, and then every two consecutive intervals (starting from the second) are merged.
    
    Parameters:
        input_audio_path (str): Path to the input audio file.
        output_json_path (str): Path where the JSON with timestamps will be saved.
        top_db (int): The decibel threshold for silence detection.
        frame_length (int): Frame length for analysis.
        hop_length (int): Hop length for analysis.
        min_duration (float): Minimum duration (in seconds) for a segment to be considered valid.
    """
    # Load the audio file preserving its native sample rate.
    y, sr = librosa.load(input_audio_path, sr=None)
    total_duration = len(y) / sr
    print(f"Loaded '{input_audio_path}' at {sr} Hz. Duration: {total_duration:.2f} seconds.")

    # Detect non-silent intervals using librosa's effects.split.
    intervals = librosa.effects.split(y, top_db=top_db, frame_length=frame_length, hop_length=hop_length)
    print(f"Detected {len(intervals)} segments based on silence detection.")

    # Filter out segments that are too short.
    valid_intervals = []
    for i, (start, end) in enumerate(intervals, start=1):
        duration = (end - start) / sr
        if duration < min_duration:
            print(f"Skipping segment {i} (duration {duration:.2f}s is below threshold)")
            continue
        valid_intervals.append((start, end))
    
    # Merge segments: keep the first as is, and merge every two consecutive segments starting from the second.
    merged_slokas = []
    if valid_intervals:
        # First sloka remains unchanged.
        merged_slokas.append(valid_intervals[0])
        
        # Merge every two consecutive segments starting from the second.
        i = 1
        while i < len(valid_intervals):
            if i + 1 < len(valid_intervals):
                # Merge the i-th and (i+1)-th segments.
                start_merged = valid_intervals[i][0]
                end_merged = valid_intervals[i + 1][1]
                merged_slokas.append((start_merged, end_merged))
                i += 2  # Skip the next one as it has been merged.
            else:
                # If there's an odd segment left, add it as is.
                merged_slokas.append(valid_intervals[i])
                i += 1

    # Build JSON structure with each sloka's timestamp (in seconds).
    slokas_list = []
    for idx, (start, end) in enumerate(merged_slokas, start=1):
        sloka_info = {
            "sloka_index": idx,
            "start_time": round(start / sr, 2),
            "end_time": round(end / sr, 2),
            "duration": round((end - start) / sr, 2)
        }
        slokas_list.append(sloka_info)
    
    output_data = {"slokas": slokas_list}

    # Save JSON output.
    with open(output_json_path, "w") as f:
        json.dump(output_data, f, indent=4)
    
    print(f"JSON with sloka timestamps saved to: {output_json_path}")

# --- Configuration Variables ---
input_audio = "audio/balakanda/Kanda_1_BK-001-Samksheparamayanam.mp3"  
output_json = "slokas_timestamps.json"   # Path for the JSON output

if __name__ == "__main__":
    segment_sloka_to_json(input_audio, output_json, top_db=35, frame_length=1024, hop_length=256, min_duration=0.2)
