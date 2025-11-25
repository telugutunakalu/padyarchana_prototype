# Aksharanusarika Python Implementation

## 📖 Overview

This is the Python implementation of Aksharanusarika, a comprehensive Telugu linguistic and prosodic analysis toolkit. It provides a full-featured API for analyzing Telugu text programmatically.

## 🚀 Installation

### Requirements
- Python 3.7 or higher
- `pytz` library for timezone support

### Install Dependencies

```bash
# Using pip
pip install pytz

# Or using requirements.txt
pip install -r requirements.txt
```

## 📚 API Reference

### Core Functions

#### `generate_comprehensive_json(text, output_file=None)`

Generates comprehensive JSON analysis for Telugu text.

**Parameters:**
- `text` (str): Telugu text to analyze (letter, word, sentence, or paragraph)
- `output_file` (str, optional): Path to save JSON file. If None, returns dictionary.

**Returns:**
- `dict` or `str`: Complete analysis as dictionary if `output_file` is None, otherwise success message.

**Example:**
```python
from aksharanusarika import generate_comprehensive_json

# Return as dictionary
result = generate_comprehensive_json("తెలుగు")
print(result['linguistic']['statistics']['totalAksharas'])

# Save to file
generate_comprehensive_json("తెలుగు", "analysis.json")
```

#### `analyze_telugu_word(word)`

Performs core linguistic analysis on Telugu text.

**Parameters:**
- `word` (str): Telugu text to analyze

**Returns:**
- `dict`: Analysis containing `word`, `uniqueId`, `aksharalu`, `aksharaluList`, `categoryCounts`, `tags`

**Example:**
```python
from aksharanusarika import analyze_telugu_word

result = analyze_telugu_word("తెలుగు")
print(f"Aksharas: {result['aksharaluList']}")
print(f"Categories: {result['categoryCounts']}")
```

#### `compare_telugu_words(word1, word2)`

Compares two Telugu texts linguistically and prosodically.

**Parameters:**
- `word1` (str): First Telugu text
- `word2` (str): Second Telugu text

**Returns:**
- `dict`: Comparison results with `word1Analysis`, `word2Analysis`, and `comparison`

**Example:**
```python
from aksharanusarika import compare_telugu_words

result = compare_telugu_words("తెలుగు", "కన్నడ")
print(f"Common tags: {result['comparison']['commonTags']}")
print(f"Jaccard similarity: {result['comparison']['jaccardSimilarity']}")
```

#### `aksharaGanaVibhajana(aksharalu_list)`

Performs prosodic (Gana) analysis on a list of aksharas.

**Parameters:**
- `aksharalu_list` (list): List of aksharas

**Returns:**
- `list`: Gana markers ('U' for Guru, 'I' for Laghu, '' for ignorable)

#### `splitAksharalu(word)`

Splits Telugu text into individual aksharas (syllables).

**Parameters:**
- `word` (str): Telugu text

**Returns:**
- `list`: List of aksharas

**Example:**
```python
from aksharanusarika import split_aksharalu

aksharas = split_aksharalu("తెలుగు")
print(aksharas)  # ['తే', 'లు', 'గు']
```

### Helper Functions

#### `categorize_aksharam(aksharam)`

Categorizes a single aksharam into linguistic categories.

**Returns:** `list` of category names

#### `calculate_linguistic_statistics(analysis)`

Calculates statistical metrics from analysis result.

#### `calculate_vargam_distribution(analysis)`

Calculates consonant group distribution.

#### `calculate_articulation_distribution(analysis)`

Calculates place-of-articulation distribution.

#### `calculate_prosody_statistics(gana_markers, gana_combinations)`

Calculates prosodic statistics.

## 💡 Usage Examples

### Example 1: Basic Analysis

```python
from aksharanusarika import generate_comprehensive_json

# Analyze a single word
result = generate_comprehensive_json("తెలుగు")

# Access different parts of the analysis
print(f"Total Aksharas: {result['linguistic']['statistics']['totalAksharas']}")
print(f"Vowels: {result['linguistic']['statistics']['vowelCount']}")
print(f"Consonants: {result['linguistic']['statistics']['consonantCount']}")
print(f"Gana Sequence: {' '.join(result['prosody']['ganaSequence'])}")
```

### Example 2: Sentence Analysis

```python
from aksharanusarika import generate_comprehensive_json

sentence = "తెలుగు వికీపీడియా ఆవిర్భావానికి"
result = generate_comprehensive_json(sentence)

print(f"Word Count: {result['input']['wordCount']}")
print(f"Total Aksharas: {result['linguistic']['statistics']['totalAksharas']}")
print(f"Guru Count: {result['prosody']['statistics']['guruCount']}")
print(f"Laghu Count: {result['prosody']['statistics']['laghuCount']}")
print(f"Gana Combinations: {result['prosody']['ganaCombinations']['count']}")
```

### Example 3: Paragraph Analysis with File Output

```python
from aksharanusarika import generate_comprehensive_json

paragraph = """తెలుగు భాష దక్షిణ భారతదేశంలో తెలుగు ప్రజలు మాట్లాడే భాష.
ఆంధ్రప్రదేశ్, తెలంగాణ రాష్ట్రాల అధికార భాష."""

# Save to JSON file
message = generate_comprehensive_json(paragraph, "telugu_analysis.json")
print(message)  # "JSON analysis saved to telugu_analysis.json"
```

### Example 4: Comparative Analysis

```python
from aksharanusarika import compare_telugu_words

result = compare_telugu_words("సత్యము", "ధర్మము")

print(f"Common Tags: {result['comparison']['commonTags']}")
print(f"Unique to 'సత్యము': {result['comparison']['uniqueToWord1']}")
print(f"Unique to 'ధర్మము': {result['comparison']['uniqueToWord2']}")
print(f"Similarity: {result['comparison']['jaccardSimilarity']:.3f}")
print(f"Gana Similarity: {result['comparison']['ganaJaccard']['similarity']:.3f}")
```

### Example 5: Accessing Detailed Analysis

```python
from aksharanusarika import generate_comprehensive_json
import json

result = generate_comprehensive_json("అమ్మ")

# Pretty print entire JSON
print(json.dumps(result, ensure_ascii=False, indent=2))

# Access specific data
for akshara in result['linguistic']['aksharalu']:
    print(f"{akshara['aksharam']}: {akshara['count']} times")
    print(f"  Categories: {', '.join(akshara['categories'][:3])}...")

# Access Gana combinations
for combo in result['prosody']['ganaCombinations']['combinations'][:3]:
    parts = [f"{g['syllable_text']}-{g['name']}" for g in combo]
    print(f"Combination: {' + '.join(parts)}")
```

## 📊 JSON Output Structure

The `generate_comprehensive_json()` function returns/saves the following structure:

```json
{
  "metadata": {
    "schemaVersion": "1.0.0",
    "analysisTimestamp": "2025-10-30T13:45:30.123456+05:30",
    "analyzerVersion": "0.0.7a",
    "inputHash": "id-8a92e7c1",
    "processingTimeMs": 1.23
  },
  "input": {
    "rawText": "input text",
    "sanitizedText": "sanitized text",
    "characterCount": 10,
    "wordCount": 2,
    "sentenceCount": 1,
    "paragraphCount": 1,
    "language": "Telugu",
    "scriptValidation": {
      "isValid": true,
      "invalidCharacters": [],
      "warnings": []
    }
  },
  "linguistic": {
    "aksharalu": [
      {
        "aksharam": "తే",
        "categories": ["హల్లు", "హ్రస్వాక్షరం", ...],
        "count": 1,
        "positions": [0]
      }
    ],
    "aksharaluList": ["తే", "లు", "గు"],
    "categoryCounts": {
      "హల్లు": 3,
      "అచ్చు": 3,
      ...
    },
    "statistics": {
      "totalAksharas": 3,
      "uniqueAksharas": 3,
      "vowelCount": 3,
      "consonantCount": 3,
      "vowelToConsonantRatio": 1.0,
      "complexityScore": 0
    },
    "vargamDistribution": { ... },
    "articulationDistribution": { ... }
  },
  "prosody": {
    "ganaSequence": ["I", "I", "I"],
    "ganaMarkers": [
      {
        "aksharam": "తే",
        "marker": "I",
        "position": 0
      }
    ],
    "ganaCombinations": {
      "count": 4,
      "combinations": [ ... ],
      "limitedOutput": false,
      "maxCombinationsShown": 4
    },
    "statistics": {
      "totalSyllables": 3,
      "guruCount": 0,
      "laghuCount": 3,
      "guruPercentage": 0.0,
      "laghuPercentage": 100.0,
      "mostCommonGana": "Laghu"
    }
  },
  "summary": {
    "linguisticProfile": "Text with 3 aksharas, 3 vowels, 3 consonants",
    "prosodicProfile": "Prosodic pattern: 0.0% Guru, 100.0% Laghu",
    "dominantCategories": ["హల్లు", "అచ్చు", "హ్రస్వాక్షరం"]
  }
}
```

## 🧪 Testing

Run the test suite:

```bash
# Run comprehensive tests
python tests/test_json_feature.py

# Run demo
python examples/demo.py

# Run usage examples
python examples/example_json_usage.py
```

## 🔧 Advanced Usage

### Custom Analysis Pipeline

```python
from aksharanusarika import (
    split_aksharalu,
    categorize_aksharam,
    akshara_ganavibhajana,
    GanaAnalyzer,
    GANA_DEFINITIONS
)

# Step 1: Split text
text = "తెలుగు"
aksharas = split_aksharalu(text)
print(f"Aksharas: {aksharas}")

# Step 2: Categorize each akshara
for ak in aksharas:
    categories = categorize_aksharam(ak)
    print(f"{ak}: {categories}")

# Step 3: Gana analysis
gana_markers = akshara_ganavibhajana(aksharas)
print(f"Gana: {' '.join(m for m in gana_markers if m)}")

# Step 4: Find Gana combinations
analyzer = GanaAnalyzer(GANA_DEFINITIONS)
pure_ganas = [m for m in gana_markers if m]
combinations = analyzer.find_sequential_combinations(pure_ganas)
print(f"Found {len(combinations)} combinations")
```

### Batch Processing

```python
from aksharanusarika import generate_comprehensive_json
import json

words = ["తెలుగు", "కన్నడ", "తమిళం", "మలయాళం"]
results = []

for word in words:
    result = generate_comprehensive_json(word)
    results.append(result)

# Save all results
with open("batch_analysis.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
```

## 📝 Notes

- All text processing is done in Unicode
- Invalid characters are automatically removed and reported
- Gana combinations are limited to 50 to prevent excessive output
- Processing time is measured and included in metadata
- Supports Telugu Unicode range U+0C00 to U+0C7F

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError for pytz
```bash
pip install pytz
```

### Issue: UnicodeEncodeError on Windows
Use UTF-8 encoding when printing Telugu text:
```python
import sys
import codecs
sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
```

### Issue: Empty analysis results
Ensure input contains valid Telugu characters (U+0C00 to U+0C7F range)

## 📚 See Also

- [Main README](../README.md) - Project overview
- [HTML README](../html/README.md) - Web interface documentation
- [Release Notes](../RELEASE_NOTES.md) - Version history
- [JSON Feature Guide](../docs/JSON_FEATURE_README.md) - Detailed JSON documentation

## 📧 Support

For issues and questions:
- GitHub Issues: [aksharanusarika/issues](https://github.com/yourusername/aksharanusarika/issues)
- Documentation: [docs/](../docs/)

---

**Aksharanusarika Python v0.0.7a** - Telugu Linguistic Analysis Toolkit
