import json
import csv

# Input and output file paths
input_file = 'ramayana_slokas.json'
output_file = 'ramayana_slokas.csv'

# Load JSON data
with open(input_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Extract slokas list
slokas = data.get("slokas", [])

# Write to CSV
with open(output_file, 'w', encoding='utf-8', newline='') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=["kanda", "sarga", "sloka", "text"])
    writer.writeheader()
    for sloka in slokas:
        writer.writerow(sloka)

print(f"CSV written to {output_file}")
