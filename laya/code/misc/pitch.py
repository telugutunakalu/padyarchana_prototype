import parselmouth
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys

def extract_pitch(audio_file, min_pitch=50, max_pitch=400):
    """
    Extracts the pitch contour from an audio file and returns a DataFrame with time and F0 (Hz).
    """
    # Load the audio file
    snd = parselmouth.Sound(audio_file)

    # Extract pitch using Praat's algorithm
    pitch = snd.to_pitch(time_step=0.01, min_pitch=min_pitch, max_pitch=max_pitch)

    # Get time and pitch values
    times = pitch.xs()
    f0_values = pitch.selected_array['frequency']

    # Replace unvoiced frames (0 Hz) with NaN for better visualization
    f0_values[f0_values == 0] = np.nan

    # Save to DataFrame
    pitch_data = pd.DataFrame({'Time (s)': times, 'Pitch (Hz)': f0_values})
    
    return pitch_data

def plot_pitch_contour(pitch_data, audio_file):
    """
    Plots the extracted pitch contour.
    """
    plt.figure(figsize=(10, 4))
    plt.plot(pitch_data['Time (s)'], pitch_data['Pitch (Hz)'], marker='o', linestyle='-', color='b')
    plt.xlabel("Time (seconds)")
    plt.ylabel("Pitch (Hz)")
    plt.title(f"Pitch Contour: {audio_file}")
    plt.grid()
    plt.show()

def save_pitch_data(pitch_data, output_file):
    """
    Saves the pitch contour data to a CSV file.
    """
    pitch_data.to_csv(output_file, index=False)
    print(f"Pitch data saved to: {output_file}")

if __name__ == "__main__":
    # Example usage
    audio_file = "amarakosha_audio/1/2.mp3"  # Replace with your file
    output_csv = f"test/pitch_contour{audio_file}.csv"

    # Extract pitch
    pitch_data = extract_pitch(audio_file)

    # Plot the contour
    plot_pitch_contour(pitch_data, audio_file)

    # Save pitch data
    save_pitch_data(pitch_data, output_csv)
