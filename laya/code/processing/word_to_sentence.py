import csv
import io
from tqdm import tqdm

input_path = "SwaraSangraha/ramayana2/word_data.csv"
output_path = "SwaraSangraha/ramayana2/sentence_data.csv"

def convert_word_to_sentences(input_file, output_file):
    import sys
    csv.field_size_limit(sys.maxsize)
    with open(input_file, "r", encoding="utf-8") as infile:
        reader = csv.DictReader(io.StringIO(infile.read()))
        data = list(reader)
    print(f"Total rows read: {len(data)}")

    sentences = []
    current_sentence = []
    kanda, sarga = None, None
    start_time = None
    skipped_rows = 0

    for row in tqdm(data, desc="Processing Sentences"):
        if not row["Word Start"] or not row["Word End"] or row["Word Start"].strip() == "" or row["Word End"].strip() == "":
            skipped_rows += 1
            continue
        word_start = float(row["Word Start"])
        word_end = float(row["Word End"])
        kanda = row["Kanda"]
        sarga = row["Sarga"]

        if not current_sentence:
            start_time = word_start

        word = row["Word"]
        current_sentence.append(word)

        if word.endswith("।") or word.endswith("॥"):
            sentence_text = " ".join(current_sentence)
            sentences.append({
                "Kanda": kanda,
                "Sarga": sarga,
                "Sentence": sentence_text.strip(),
                "Sentence Start": start_time,
                "Sentence End": word_end
            })
            current_sentence = []

    print(f"Rows skipped due to missing times: {skipped_rows}")
    print(f"Sentences formed: {len(sentences)}")

    with open(output_file, "w", encoding="utf-8", newline="") as outfile:
        fieldnames = ["Kanda", "Sarga", "Sentence", "Sentence Start", "Sentence End"]
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        for sent in sentences:
            writer.writerow(sent)

convert_word_to_sentences(input_path, output_path)