# Release Notes - Aksharanusarika

## Version 0.0.7a (2025-10-30)

### 🎉 Major Release - JSON Export & Enhanced Analysis

This release introduces comprehensive JSON export functionality, enhanced statistical analysis, and improved project organization.

### ✨ New Features

#### JSON Export System
- **Comprehensive JSON Generation**: Complete analysis output in structured JSON format
- **Python API**: `generate_comprehensive_json(text, output_file=None)` function
- **HTML Download Button**: One-click JSON download with timestamped filenames
- **Single Source of Truth**: UI now populated from generated JSON data
- **Schema Versioning**: JSON includes schema version for future compatibility

#### Enhanced Statistical Analysis
- **Linguistic Statistics**:
  - Vowel-to-consonant ratios
  - Long vs short vowel counts
  - Complexity scores (based on conjuncts and doublets)
  - Unique vs total akshara counts

- **Vargam Distribution**: Detailed consonant group frequency analysis
  - క, చ, ట, త, ప వర్గములు
  - స్పర్శములు, ఊష్మాలు, అంతస్తములు

- **Articulation Distribution**: Place-of-articulation statistics
  - కంఠ్యములు, తాలవ్యములు, మూర్ధన్యములు
  - దంత్యములు, ఓష్ఠ్యములు, అనునాసికములు
  - Combined articulation categories

- **Prosody Statistics**:
  - Guru/Laghu percentages and ratios
  - Most common Gana patterns
  - Gana variety (unique pattern count)
  - Total syllable counts

#### JSON Structure
```json
{
  "metadata": { /* Schema version, timestamp, hash, processing time */ },
  "input": { /* Raw text, sanitized text, counts, validation */ },
  "linguistic": { /* Aksharalu, statistics, distributions */ },
  "prosody": { /* Gana sequence, combinations, statistics */ },
  "summary": { /* Human-readable profiles, dominant categories */ }
}
```

### 🏗️ Project Organization

#### New Folder Structure
```
aksharanusarika/
├── python/          # Python implementation
│   ├── examples/    # Usage examples
│   └── tests/       # Test suite
├── html/            # HTML/JavaScript implementation
├── docs/            # Documentation
└── examples/        # Sample outputs
```

#### Documentation Improvements
- Comprehensive main README with quick start guides
- Separate READMEs for Python and HTML implementations
- Detailed JSON feature documentation
- Implementation summary and technical notes
- Test instructions and usage examples

### 🔧 Technical Improvements

#### Python Implementation
- **New Functions**:
  - `generate_comprehensive_json()`: Main JSON generation function
  - `calculate_linguistic_statistics()`: Linguistic metrics
  - `calculate_vargam_distribution()`: Vargam analysis
  - `calculate_articulation_distribution()`: Articulation analysis
  - `calculate_prosody_statistics()`: Prosodic metrics

- **Enhanced Output**:
  - Positional information for each aksharam
  - Detailed Gana marker mapping
  - Limited Gana combinations (max 50) to prevent huge outputs
  - Processing time measurement

#### HTML Implementation
- **New Functions**:
  - `generateComprehensiveJSON()`: JavaScript port of Python function
  - `createGanaTableFromJSON()`: Render from JSON data
  - `createGanaCombinationsFromJSON()`: Render combinations from JSON
  - `downloadJSON()`: File download functionality

- **UI Enhancements**:
  - Download JSON button (appears after analysis)
  - Styled with outline button design
  - Timestamp-based filenames
  - No visual changes to existing UI (preserves user experience)

### 📊 Analysis Enhancements

#### Input Processing
- Character, word, sentence, and paragraph counting
- Script validation with invalid character detection
- Sanitization warnings in JSON output

#### Metadata
- ISO-8601 timestamp with timezone
- Unique hash for each input
- Processing time in milliseconds
- Schema version for compatibility tracking

#### Summary Generation
- Linguistic profile: Human-readable text summary
- Prosodic profile: Gana pattern description
- Dominant categories: Top 3 linguistic categories

### 🐛 Bug Fixes
- Fixed Gana combination display for very long sequences
- Improved handling of ignorable characters (spaces, newlines, ZWSP)
- Better error handling for empty inputs

### 📝 Files Added
- `python/README.md`: Python-specific documentation
- `html/README.md`: HTML-specific documentation
- `python/requirements.txt`: Python dependencies
- `python/examples/example_json_usage.py`: Usage examples
- `python/examples/demo.py`: Quick demo script
- `python/tests/test_json_feature.py`: Test suite
- `docs/JSON_FEATURE_README.md`: JSON feature guide
- `docs/IMPLEMENTATION_SUMMARY.md`: Technical documentation
- `RELEASE_NOTES.md`: This file
- `LICENSE`: MIT License
- `.gitignore`: Git ignore rules

### 📝 Files Modified
- `python/aksharanusarika.py`: Added JSON export functions (~290 lines)
- `html/aksharanusarika.html`: Added JSON generation and download (~350 lines)
- `README.md`: Complete rewrite with comprehensive documentation

### 🔄 Migration from v0.0.6a

#### For Python Users
```python
# Old way (v0.0.6a)
from aksharanusarika import analyze_telugu_word
result = analyze_telugu_word("తెలుగు")

# New way (v0.0.7a) - Still works!
from aksharanusarika import analyze_telugu_word
result = analyze_telugu_word("తెలుగు")  # No breaking changes

# New JSON feature (v0.0.7a)
from aksharanusarika import generate_comprehensive_json
json_result = generate_comprehensive_json("తెలుగు")
# Or save to file:
generate_comprehensive_json("తెలుగు", "output.json")
```

#### For HTML Users
- Open `html/aksharanusarika.html` (same as before)
- Analysis works exactly as before
- **New**: Download JSON button appears after analysis
- Click to download complete analysis as JSON file

### ⚠️ Breaking Changes
**None!** This release is fully backward compatible with v0.0.6a.

### 📦 Dependencies
- Python: `pytz>=2025.2` (for timezone support)
- HTML: None (fully self-contained)

### 🔮 Future Plans
- REST API implementation
- Batch processing support
- Additional export formats (CSV, XML)
- Visualization enhancements
- Command-line interface (CLI)
- Package distribution (PyPI)

---

## Version 0.0.6a (Previous)

### Features
- Core Telugu linguistic analysis
- Akshara splitting and categorization
- Prosodic (Gana) analysis
- Comparative analysis with Jaccard similarity
- Gana combination recognition
- Interactive HTML interface with charts
- Python module for programmatic use

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
