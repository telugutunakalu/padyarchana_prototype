# Comprehensive JSON Output Feature

## Overview

The `generate_comprehensive_json()` function provides a complete analysis of Telugu text (letters, words, sentences, or paragraphs) and outputs it as a structured JSON file or dictionary.

## Features

This function performs comprehensive analysis including:

### 1. Metadata
- Schema version tracking
- Timestamp of analysis (IST timezone)
- Analyzer version
- Unique input hash
- Processing time in milliseconds

### 2. Input Analysis
- Raw and sanitized text
- Character, word, sentence, and paragraph counts
- Script validation (detects non-Telugu characters)

### 3. Linguistic Analysis
- **Aksharalu (Syllables)**
  - Individual aksharas with positions
  - Linguistic categories for each akshara
  - Frequency counts

- **Category Counts**
  - Complete count of all linguistic categories

- **Statistics**
  - Total and unique aksharas
  - Vowel and consonant counts
  - Vowel-to-consonant ratio
  - Long vs short vowel counts
  - Conjunct and doublet counts
  - Anusvaram and visarga counts
  - Complexity score

- **Vargam Distribution**
  - Distribution across consonant groups (క, చ, ట, త, ప వర్గములు)
  - Sparsha, Ooshma, Antasta classifications

- **Articulation Distribution**
  - Place of articulation categories
  - Kanthya, Taalavya, Moordhanya, Dantya, Ooshthya, etc.

### 4. Prosody Analysis (Gana)
- **Gana Sequence**
  - Guru (U) and Laghu (I) markers for each syllable

- **Gana Markers**
  - Detailed mapping of aksharas to their prosodic markers

- **Gana Combinations**
  - All possible ways to partition the sequence into named Gana patterns
  - Includes 1, 2, and 3-syllable patterns (Ya, Ma, Ta, Ra, Ja, Bha, Na, Sa, etc.)
  - Limited to 50 combinations to prevent huge outputs

- **Statistics**
  - Total syllables
  - Guru and Laghu counts and percentages
  - Guru-to-Laghu ratio
  - Most common Gana pattern
  - Gana variety (number of unique patterns)

### 5. Summary
- Human-readable linguistic profile
- Prosodic profile description
- Dominant linguistic categories

## Usage

### Basic Usage - Return Dictionary

```python
from aksharanusarika import generate_comprehensive_json

# Analyze a Telugu word
result = generate_comprehensive_json("తెలుగు")

# Access the results
print(result['linguistic']['statistics']['totalAksharas'])
print(result['prosody']['ganaSequence'])
print(result['summary']['linguisticProfile'])
```

### Save to JSON File

```python
# Save analysis to a JSON file
generate_comprehensive_json("తెలుగు వికీపీడియా", "output.json")
# Returns: "JSON analysis saved to output.json"
```

### Analyzing Different Input Types

```python
# Single letter
result = generate_comprehensive_json("తే")

# Word
result = generate_comprehensive_json("తెలుగు")

# Sentence
result = generate_comprehensive_json("తెలుగు వికీపీడియా ఆవిర్భావానికి")

# Paragraph
paragraph = """తెలుగు భాష దక్షిణ భారతదేశంలో తెలుగు ప్రజలు మాట్లాడే భాష.
ఆంధ్రప్రదేశ్, తెలంగాణ రాష్ట్రాల అధికార భాష."""
result = generate_comprehensive_json(paragraph)
```

## Function Signature

```python
def generate_comprehensive_json(text, output_file=None):
    """
    Generates comprehensive JSON analysis for Telugu text input.

    Args:
        text (str): Telugu text (letter, word, sentence, or paragraph)
        output_file (str, optional): Path to save JSON file. If None, returns JSON as dict.

    Returns:
        dict or str: Complete analysis as dictionary, or success message if file saved
    """
```

## JSON Structure

```json
{
  "metadata": {
    "schemaVersion": "1.0.0",
    "analysisTimestamp": "ISO-8601 timestamp",
    "analyzerVersion": "0.0.6a+",
    "inputHash": "unique hash",
    "processingTimeMs": 0.13
  },
  "input": {
    "rawText": "...",
    "sanitizedText": "...",
    "characterCount": 0,
    "wordCount": 0,
    "sentenceCount": 0,
    "paragraphCount": 0,
    "language": "Telugu",
    "scriptValidation": {
      "isValid": true,
      "invalidCharacters": [],
      "warnings": []
    }
  },
  "linguistic": {
    "aksharalu": [...],
    "aksharaluList": [...],
    "categoryCounts": {...},
    "statistics": {...},
    "vargamDistribution": {...},
    "articulationDistribution": {...}
  },
  "prosody": {
    "ganaSequence": [...],
    "ganaMarkers": [...],
    "ganaCombinations": {
      "count": 0,
      "combinations": [...],
      "limitedOutput": false,
      "maxCombinationsShown": 0
    },
    "statistics": {...}
  },
  "summary": {
    "linguisticProfile": "...",
    "prosodicProfile": "...",
    "dominantCategories": [...]
  }
}
```

## Examples

See `example_json_usage.py` for detailed examples including:
- Single letter analysis
- Word analysis
- Sentence analysis
- Paragraph analysis
- Saving to file
- Accessing specific features
- Pretty printing JSON

## Performance

- Typical processing time: < 1ms for single words
- Longer texts: 10-50ms depending on complexity
- Gana combinations are limited to 50 to prevent excessive computation

## Notes

- Input text is automatically sanitized to remove non-Telugu characters
- Invalid characters are reported in the `scriptValidation` section
- The function handles whitespace, newlines, and special Telugu characters
- Sentence counting recognizes Telugu (।॥) and English (. ? !) punctuation

## Version History

- **v0.0.6a+** - Added comprehensive JSON output feature with full linguistic and prosodic analysis
