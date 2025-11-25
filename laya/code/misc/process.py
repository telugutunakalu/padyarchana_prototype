import pandas as pd
import os

# Define KANDAS mapping
KANDAS = {1: 77, 2: 119, 3: 75, 4: 67, 5: 68, 6: 128}

root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load the CSV file
input_file = os.path.join(root_dir, "SwaraSangraha/ramayana/ramayana_word_data.csv")
output_file = os.path.join(root_dir, "SwaraSangraha/ramayana/transcript.csv")


df = pd.read_csv(input_file, quoting=3, encoding="utf-8", on_bad_lines="skip")

# Ensure the dataframe is sorted correctly
df = df.sort_values(by=["Kanda", "Sarga"])

# Process data
transcript_data = []
for kanda in KANDAS:
    for sarga in range(1, KANDAS[kanda] + 1):
        words = df[(df["Kanda"] == kanda) & (df["Sarga"] == sarga)]["Word"].tolist()
        
        slokas = []
        current_sloka = ""
        
        for word in words:
            if word.endswith("॥"):
                current_sloka += word
                slokas.append(current_sloka.strip())
                current_sloka = ""
            else:
                current_sloka += " " + word if current_sloka else word
        
        if current_sloka:
            slokas.append(current_sloka.strip())
        
        for sloka in slokas:
            transcript_data.append([kanda, sarga, sloka])

# Convert to DataFrame and save
transcript_df = pd.DataFrame(transcript_data, columns=["Kanda", "Sarga", "Sloka"])
transcript_df.to_csv(output_file, index=False)

print(f"Transcript saved to {output_file}")