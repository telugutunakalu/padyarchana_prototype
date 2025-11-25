import os
import requests
from bs4 import BeautifulSoup
import time
import random
import traceback
from tqdm import tqdm

# Define the base URL
BASE_URL = "https://avinashvarna.github.io/audio_alignment/corpus/meghaduta/"

# Define the subpaths to iterate through
SUBPATHS = [
    "pm01-10",
    "pm11-20",
    "pm21-30",
    "pm31-40",
    "pm41-50",
    "pm51-63"
]

# Define file paths
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sentence_csv_file = os.path.join(base_dir, "SwaraSangraha/meghaduta/sentence_data.csv")
word_csv_file = os.path.join(base_dir, "SwaraSangraha/meghaduta/word_data.csv")
audio_directory = os.path.join(base_dir, "SwaraSangraha/meghaduta/audio")
log_file = os.path.join(base_dir, "error_log.txt")

# Ensure directories exist
os.makedirs(os.path.dirname(sentence_csv_file), exist_ok=True)
os.makedirs(os.path.dirname(word_csv_file), exist_ok=True)
os.makedirs(audio_directory, exist_ok=True)

# Ensure CSV files exist and have headers
if not os.path.exists(sentence_csv_file):
    with open(sentence_csv_file, "w", encoding="utf-8") as f:
        f.write("Part,Sentence,Sentence Start,Sentence End\n")

if not os.path.exists(word_csv_file):
    with open(word_csv_file, "w", encoding="utf-8") as f:
        f.write("Part,Sarga,Word,Word Start,Word End\n")

# Logging function
def log_error(message):
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(message + "\n")
        log.write(traceback.format_exc() + "\n")

# Function to fetch URL with retries and rate limiting
MAX_RETRIES = 3

def fetch_url(url):
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response
            elif response.status_code == 429:
                wait_time = 2 ** attempt + random.uniform(0, 1)
                log_error(f"Rate limit exceeded for {url}, retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
        except requests.RequestException as e:
            log_error(f"Request error for {url}: {e}")
        time.sleep(2)
    return None  # Return None if all retries fail


# Main scraping function
def scrape_data():
    for index, SUBPATH in tqdm(enumerate(SUBPATHS), desc="Processing Parts"):
            url = f"{BASE_URL}{SUBPATH}/"
            print(f"Scraping: {url}")

            response = fetch_url(url)
            if not response:
                log_error(f"Failed to fetch {url} after retries, skipping...")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')

            # Locate text container
            text_container = soup.find(id="text-container")
            if not text_container:
                log_error(f"No text-container found in {url}. Page content:\n{soup.prettify()[:500]}")
                continue
            
            # Extract sentences and words
            for sentence in tqdm(text_container.find_all(class_="sentence-unit"), desc=f"Processing Sentences for {SUBPATH}", leave=False):
                try:
                    sentence_text = sentence.get_text(strip=True)
                    sentence_begin = sentence.get("data-begin", "")
                    sentence_end = sentence.get("data-end", "")

                    with open(sentence_csv_file, "a", encoding="utf-8") as f:
                        f.write(f"{SUBPATH},{sentence_text},{sentence_begin},{sentence_end}\n")
                
                    # Extract word units inside sentence
                    for word in sentence.find_all(class_="word-unit"):
                        try:
                            word_text = word.get_text(strip=True)
                            word_begin = word.get("data-begin", "")
                            word_end = word.get("data-end", "")

                            with open(word_csv_file, "a", encoding="utf-8") as f:
                                f.write(f"{SUBPATH},{word_text},{word_begin},{word_end}\n")
                        except Exception as e:
                            log_error(f"Error processing word in {url}: {e}")
                except Exception as e:
                    log_error(f"Error processing sentence in {url}: {e}")
            
                        # Uncomment the below code to download audio files
            audio_file = soup.find("audio")
            if audio_file and audio_file.get("src"):
                audio_url = audio_file["src"]
                audio_filename = os.path.join(audio_directory, f"{SUBPATH}.mp3")

                response = fetch_url(audio_url)
                if response:
                    with open(audio_filename, "wb") as f:
                        f.write(response.content)
                else:
                    log_error(f"Failed to fetch audio file {audio_url} for {SUBPATH}")
            

            # Sleep to avoid excessive requests
            time.sleep(random.uniform(1, 3))

    print("Data scraping completed.")

# Run the scraper
scrape_data()
