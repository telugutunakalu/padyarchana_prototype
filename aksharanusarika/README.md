# అక్షరానుసారిక (Aksharanusarika) v0.0.7a

## 📖 Overview

**Aksharanusarika** is a comprehensive Telugu language analysis toolkit that provides advanced linguistic and prosodic (Gana/Chandas) analysis. The name "అక్షరానుసారిక" (Aksharanusarika) means "syllable analyzer" in Telugu.

This toolkit is available in two implementations:
- **Python**: Full-featured analysis with JSON export capabilities
- **HTML/JavaScript**: Interactive web-based analyzer with visual charts and downloadable JSON reports

## ✨ Key Features

### Linguistic Analysis
- **Akshara Segmentation**: Intelligent splitting of Telugu text into syllables (aksharas)
- **Character Classification**: Categorization into vowels (అచ్చులు), consonants (హల్లులు), long/short vowels
- **Phonetic Analysis**: Classification by place of articulation (కంఠ్యము, తాలవ్యము, మూర్ధన్యము, దంత్యము, ఓష్ఠ్యము)
- **Consonant Groups**: Vargam analysis (క, చ, ట, త, ప వర్గములు)
- **Special Characters**: Detection of anusvaram (ం), visarga (ః), and conjuncts (సంయుక్తాక్షరములు)
- **Statistical Analysis**: Vowel-to-consonant ratios, complexity scores, frequency distributions

### Prosodic Analysis (Gana/Chandas)
- **Guru-Laghu Classification**: Syllable weight analysis based on classical prosody rules
- **Gana Pattern Recognition**: Identification of traditional prosodic patterns:
  - 1-syllable: Guru (U), Laghu (I)
  - 2-syllable: Lalamu (II), Lagamu/Va (IU), Galamu/Ha (UI), Gagamu (UU)
  - 3-syllable: Ya (IUU), Ma (UUU), Ta (UUI), Ra (UIU), Ja (IUI), Bha (UII), Na (III), Sa (IIU)
  - Special categories: Surya, Indra, and Chandra Ganas
- **Combination Analysis**: All possible ways to partition a sequence into named patterns
- **Prosodic Statistics**: Guru/Laghu ratios, pattern frequencies, rhythm analysis

### Comparative Analysis
- **Feature Comparison**: Jaccard similarity/distance for linguistic features
- **Gana Comparison**: Prosodic similarity using bigram-based Jaccard coefficient
- **Longest Common Substring**: Identification of shared Gana patterns
- **Visual Comparison**: Side-by-side charts and tables

### JSON Export (New in v0.0.7a)
- **Comprehensive Data Export**: Complete analysis in structured JSON format
- **Single Source of Truth**: UI populated from generated JSON
- **Downloadable Reports**: One-click download with timestamp
- **Machine-Readable**: Perfect for integration with other tools and pipelines

## 🚀 Quick Start

### Python Implementation

#### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/aksharanusarika.git
cd aksharanusarika

# Install dependencies
pip install pytz

# Or using requirements.txt
pip install -r python/requirements.txt
```

#### Basic Usage

```python
from python.aksharanusarika import generate_comprehensive_json

# Analyze Telugu text
result = generate_comprehensive_json("తెలుగు")

# Access analysis data
print(f"Total Aksharas: {result['linguistic']['statistics']['totalAksharas']}")
print(f"Gana Sequence: {' '.join(result['prosody']['ganaSequence'])}")

# Save to JSON file
generate_comprehensive_json("తెలుగు వికీపీడియా", "analysis.json")
```

See [python/README.md](python/README.md) for detailed Python documentation.

### HTML Implementation

#### Usage

1. Open `html/aksharanusarika.html` in a modern web browser
2. Enter Telugu text in the input box
3. Click **విశ్లేషించు (Analyze)**
4. View comprehensive analysis with interactive charts
5. Click **📥 Download JSON** to save analysis results

**No installation required!** Just open the HTML file in any modern browser.

See [html/README.md](html/README.md) for detailed HTML documentation.

## 📊 Example Analysis

### Input
```
తెలుగు భాష
```

### Output Structure
```json
{
  "metadata": {
    "schemaVersion": "1.0.0",
    "analysisTimestamp": "2025-10-31T11:54:45.002430+05:30",
    "analyzerVersion": "0.0.7a+",
    "inputHash": "id-eb2fc841",
    "processingTimeMs": 21.25
  },
  "linguistic": {
    "statistics": {
      "totalAksharas": 5,
      "uniqueAksharas": 5,
      "vowelCount": 0,
      "consonantCount": 5,
      "vowelToConsonantRatio": 0.0,
      "longVowelCount": 1,
      "shortVowelCount": 4,
      "conjunctCount": 0,
      "doubletCount": 0,
      "anusvaaramCount": 0,
      "visargaCount": 0,
      "complexityScore": 0.0
    },
    "vargamDistribution": {
      "క వర్గము": 0,
      "చ వర్గము": 0,
      "ట వర్గము": 0,
      "త వర్గము": 2,
      "ప వర్గము": 1,
      "స్పర్శములు": 3,
      "ఊష్మాలు": 1,
      "అంతస్తములు": 1
    },
    "articulationDistribution": {
      "కంఠ్యములు": 1,
      "తాలవ్యములు": 1,
      "మూర్ధన్యములు": 0,
      "దంత్యములు": 2,
      "ఓష్ఠ్యములు": 1,
      "అనునాసికములు": 0,
      "కంఠతాలవ్యములు": 0,
      "కంఠోష్ఠ్యములు": 0,
      "దంత్యోష్ఠ్యములు": 0
    }
  },
  "prosody": {
    "ganaSequence": ["I", "I", "I", "U", "I"],
    "statistics": {
      "totalSyllables": 5,
      "guruCount": 1,
      "laghuCount": 4,
      "guruToLaghuRatio": 0.25,
      "guruPercentage": 20.0,
      "laghuPercentage": 80.0,
      "mostCommonGana": "Laghu",
      "ganaVariety": 11
    },
    "ganaCombinations": {
      "count": 30,
      "limitedOutput": false
    }
  }
}
```

## 📁 Repository Structure

```
aksharanusarika/
├── README.md                 # This file - main documentation
├── LICENSE                   # MIT License
├── .gitignore               # Git ignore rules
├── RELEASE_NOTES.md         # Version history and changes
│
├── python/                  # Python implementation
│   ├── README.md                       # Python-specific documentation
│   ├── requirements.txt                # Python dependencies
│   ├── aksharanusarika.py              # Main Telugu analysis module
│   ├── json_to_csv_converter.py        # Convert JSON test data to CSV
│   ├── analyze_csv_pipeline.py         # Batch analysis pipeline
│   ├── transliterate_csv_to_english.py # Telugu to Roman transliteration
│   ├── JSON_TO_CSV_README.md           # CSV converter documentation
│   ├── examples/                       # Usage examples
│   │   ├── example_json_usage.py
│   │   └── demo.py
│   └── tests/                          # Test suite
│       └── test_json_feature.py
│
├── html/                    # HTML/JavaScript implementation
│   ├── README.md           # HTML-specific documentation
│   └── aksharanusarika.html # Self-contained web application
│
├── docs/                    # Additional documentation
│   ├── JSON_FEATURE_README.md
│   └── IMPLEMENTATION_SUMMARY.md
│
├── data/                    # Processed data files
│   ├── README.md           # Data documentation
│   ├── final/              # Final output files
│   │   ├── consolidated_testdata_with_analysis.csv  # 8.3 MB - Telugu + analysis
│   │   └── final_data.csv                            # 5.8 MB - Romanized + analysis
│   └── intermediate/       # Intermediate processing files
│       └── consolidated_testdata.csv                 # 7.3 MB - Combined poems
│
├── testdata/               # Original test data (109 JSON files)
│   ├── vemana_*.json      # Vemana poetry collections
│   ├── *_satakam.json     # Various satakam collections
│   └── ...                # Other Telugu poetry files
│
└── examples/               # Sample outputs and usage examples
    └── sample_outputs/
```

## 🔧 Technical Details

### Telugu Unicode Support
- Full support for Telugu Unicode range (U+0C00 to U+0C7F)
- Handles dependent and independent vowel forms
- Proper handling of halant (్), anusvaram (ం), and visarga (ః)
- Support for conjunct consonants and doubled consonants

### Prosody Rules
Based on classical Telugu prosody (ఛందస్సు):
- **Guru (heavy) syllable** if:
  - Contains long vowel (దీర్ఘ స్వరము)
  - Contains plutas (ఐ, ఔ)
  - Contains anusvaram or visarga
  - Ends with halant (pollu)
  - Followed by conjunct or doubled consonant
- **Laghu (light) syllable** otherwise

### Algorithm Highlights
- **Two-pass splitting**: Coarse split followed by pollu-hallu merging
- **Memoized Gana analysis**: Efficient dynamic programming for combination finding
- **Bigram-based Jaccard**: Advanced similarity metric for prosodic comparison
- **LCS algorithm**: O(mn) dynamic programming for longest common substring

## 📚 Documentation

- **[Python README](python/README.md)** - Python API reference and examples
- **[HTML README](html/README.md)** - Web interface guide
- **[Release Notes](RELEASE_NOTES.md)** - Version history and changelog
- **[JSON Feature Guide](docs/JSON_FEATURE_README.md)** - Comprehensive JSON export documentation
- **[Implementation Details](docs/IMPLEMENTATION_SUMMARY.md)** - Technical implementation notes

## 🆕 What's New in v0.0.7a

### Major Features
✨ **JSON Export Functionality**
- Comprehensive JSON generation for all analysis types
- One-click download in HTML interface
- Structured data export in Python
- Single source of truth architecture

✨ **Enhanced Statistics**
- Vowel-to-consonant ratios
- Complexity scores
- Vargam and articulation distributions
- Prosodic pattern frequencies

✨ **Improved Organization**
- Separated Python and HTML implementations
- Comprehensive documentation
- Example scripts and test suite
- Professional repository structure

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for complete details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes:
1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Based on traditional Telugu prosody (ఛందస్సు శాస్త్రము)
- Inspired by classical Telugu linguistics
- Unicode Consortium for Telugu character specifications

## 📧 Contact

- **Project Repository**: [github.com/yourusername/aksharanusarika](https://github.com/yourusername/aksharanusarika)
- **Issues**: [github.com/yourusername/aksharanusarika/issues](https://github.com/yourusername/aksharanusarika/issues)

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

---

**అక్షరానుసారిక v0.0.7a** - Advanced Telugu Linguistic and Prosodic Analysis Toolkit
