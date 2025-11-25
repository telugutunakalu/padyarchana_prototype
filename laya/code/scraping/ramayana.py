import os
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import traceback
from tqdm import tqdm
import json

# Define the base URL
BASE_URL = "https://hrishikeshrt.github.io/audio_alignment/corpus/ramayana/"

# Define the number of sargas for each kanda
KANDAS = {
    1: 77,
    2: 119,
    3: 75,
    4: 67,
    5: 68,
    6: 128
}

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sentence_csv_file = os.path.join(base_dir, "SwaraSangraha/ramayana2/sentence_data.csv")
word_csv_file = os.path.join(base_dir, "SwaraSangraha/ramayana2/word_data.csv")
audio_directory = os.path.join(base_dir, "SwaraSangraha/ramayana2/audio")
log_file = os.path.join(base_dir, "error_log.txt")

# Ensure directories exist
os.makedirs(os.path.dirname(sentence_csv_file), exist_ok=True)
os.makedirs(os.path.dirname(word_csv_file), exist_ok=True)
os.makedirs(audio_directory, exist_ok=True)

sentence_data = []
word_data = []

def log_error(message):
    with open(log_file, "a", encoding="utf-8") as log:
        log.write(message + "\n")


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


# Function to fetch and parse data
def scrape_data():
    for kanda, num_sargas in tqdm(KANDAS.items(), desc="Processing Kandas"):
        for sarga in tqdm(range(1, num_sargas + 1), desc=f"Processing Sargas for Kanda {kanda}", leave=False):
            sarga_str = f"{sarga:03d}"  # Format sarga as three-digit
            url = f"{BASE_URL}{kanda}.{sarga_str}/"
            print(f"Scraping: {url}")
            
            try:
                response = requests.get(url)
                if response.status_code != 200:
                    log_error(f"Failed to fetch {url}, skipping...")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                text_container = soup.find(id="text-container")
                if not text_container:
                    log_error(f"No text-container found in {url}")
                    continue
                
                # Extract sentence and word data
                for sentence in tqdm(text_container.find_all(class_="sentence-unit"), desc=f"Processing Sentences for {kanda}.{sarga_str}", leave=False):
                    try:
                        sentence_text = sentence.get_text(strip=True)
                        sentence_begin = sentence.get("data-begin", "")
                        sentence_end = sentence.get("data-end", "")
                        
                        sentence_data.append({
                            "Kanda": kanda,
                            "Sarga": sarga,
                            "Sentence": sentence_text,
                            "Sentence Start": sentence_begin,
                            "Sentence End": sentence_end
                        })
                    
                        # Extract word units inside sentence
                        for word in sentence.find_all(class_="word-unit"):
                            try:
                                word_text = word.get_text(strip=True)
                                word_begin = word.get("data-begin", "")
                                word_end = word.get("data-end", "")
                                
                                word_data.append({
                                    "Kanda": kanda,
                                    "Sarga": sarga,
                                    "Word": word_text,
                                    "Word Start": word_begin,
                                    "Word End": word_end
                                })
                            except Exception as e:
                                log_error(f"Error processing word in {url}: {e}")
                    except Exception as e:
                        log_error(f"Error processing sentence in {url}: {e}")
            
            except Exception as e:
                log_error(f"Error processing {url}: {e}")
            
            # Uncomment the below code to download audio files
            # audio_file = soup.find("audio")
            # if audio_file and audio_file.get("src"):
            #     audio_url = audio_file["src"]
            #     audio_filename = os.path.join(audio_directory, f"{kanda}/{sarga}.mp3")
            #     os.makedirs(os.path.dirname(audio_filename), exist_ok=True)

            #     response = fetch_url(audio_url)
            #     if response:
            #         with open(audio_filename, "wb") as f:
            #             f.write(response.content)
            #     else:
            #         log_error(f"Failed to fetch audio file {audio_url} for {kanda}/{sarga}")

            # Sleep to avoid excessive requests
            time.sleep(1)

    with open(sentence_csv_file.replace(".csv", ".json"), "w", encoding="utf-8") as f:
        json.dump(sentence_data, f, ensure_ascii=False, indent=2)

    with open(word_csv_file.replace(".csv", ".json"), "w", encoding="utf-8") as f:
        json.dump(word_data, f, ensure_ascii=False, indent=2)

    print("Data scraping completed.")

# Run the scraper
scrape_data()