import os
import requests
import csv
from bs4 import BeautifulSoup
import time
import random
import traceback
from tqdm import tqdm

BASE_URL = "https://hrishikeshrt.github.io/audio_alignment/corpus/ashtadhyayi/"
ADHYAYAS = {i: 4 for i in range(1, 9)}


base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sentence_csv_file = os.path.join(base_dir, "SwaraSangraha/ashtadhyayi/sentence_data.csv")
word_csv_file = os.path.join(base_dir, "SwaraSangraha/ashtadhyayi/word_data.csv")
audio_directory = os.path.join(base_dir, "SwaraSangraha/ashtadhyayi/audio")
log_file = os.path.join(base_dir, "error_log.txt")

# Ensure directories exist
os.makedirs(os.path.dirname(sentence_csv_file), exist_ok=True)
os.makedirs(os.path.dirname(word_csv_file), exist_ok=True)
os.makedirs(audio_directory, exist_ok=True)

def ensure_csv(file_path, headers):
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

ensure_csv(sentence_csv_file, ["Adhyaya", "Pada", "Sentence", "Sentence Start", "Sentence End"])
ensure_csv(word_csv_file, ["Adhyaya", "Pada", "Word", "Word Start", "Word End"])

def log_error(message):
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(message + "\n")
        log.write(traceback.format_exc() + "\n")

MAX_RETRIES = 3

def fetch_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
    }
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                wait_time = 2 ** attempt + random.uniform(1, 3)
                log_error(f"Rate limit exceeded for {url}, retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
        except requests.RequestException as e:
            log_error(f"Request error for {url}: {e}")
        time.sleep(3)
    return None

def append_to_csv(file_path, data):
    with open(file_path, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(data)

def scrape_data():
    for adhyaya, num_padas in tqdm(ADHYAYAS.items(), desc="Processing Adhyayas"):
        for pada in tqdm(range(1, num_padas + 1), desc=f"Processing Padas for Adhyaya {adhyaya}", leave=False):
            url = f"{BASE_URL}{adhyaya}.{pada}/"
            print(f"Scraping: {url}")

            response = fetch_url(url)
            if not response:
                log_error(f"Failed to fetch {url} after retries, skipping...")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')   

            text_container = soup.find(id="text-container")
            if not text_container:
                log_error(f"No text-container found in {url}. Page content:\n{soup.prettify()[:500]}")
                continue

            for sentence in tqdm(text_container.find_all(class_="sentence-unit"), desc=f"Processing Sentences for {adhyaya}.{pada}", leave=False):
                try:
                    sentence_text = sentence.get_text(strip=True)
                    sentence_begin = sentence.get("data-begin", "")
                    sentence_end = sentence.get("data-end", "")

                    append_to_csv(sentence_csv_file, [adhyaya, pada, sentence_text, sentence_begin, sentence_end])
                    
                    for word in sentence.find_all(class_="word-unit"):
                        try:
                            word_text = word.get_text(strip=True)
                            word_begin = word.get("data-begin", "")
                            word_end = word.get("data-end", "")

                            append_to_csv(word_csv_file, [adhyaya, pada, word_text, word_begin, word_end])
                        except Exception as e:
                            log_error(f"Error processing word in {url}: {e}")
                except Exception as e:
                    log_error(f"Error processing sentence in {url}: {e}")

            # Uncomment the below code to download audio files
            audio_file = soup.find("audio")
            if audio_file and audio_file.get("src"):
                audio_url = audio_file["src"]
                audio_subdir = os.path.join(audio_directory, str(adhyaya))
                os.makedirs(audio_subdir, exist_ok=True)
                audio_filename = os.path.join(audio_subdir, f"{pada}.mp3")

                response = fetch_url(audio_url)
                if response:
                    with open(audio_filename, "wb") as f:
                        f.write(response.content)
                else:
                    log_error(f"Failed to fetch audio file {audio_url} for {adhyaya}.{pada}")
            
            time.sleep(random.uniform(2, 5))

    print("Data scraping completed.")

scrape_data()
