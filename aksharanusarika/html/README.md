# Aksharanusarika HTML Implementation

## 📖 Overview

This is the HTML/JavaScript implementation of Aksharanusarika - a self-contained, interactive web application for Telugu linguistic and prosodic analysis. No server or installation required!

## 🚀 Quick Start

### Usage

1. **Open the file**: Double-click `aksharanusarika.html` or open it in any modern web browser
2. **Enter text**: Type or paste Telugu text in the input box
3. **Analyze**: Click the **విశ్లేషించు (Analyze)** button
4. **View results**: Explore the comprehensive analysis with interactive charts
5. **Download**: Click **📥 Download JSON** to save the complete analysis

**That's it!** No installation, no dependencies, no server needed.

## ✨ Features

### Two Analysis Modes

#### 1. Single Analysis (అక్షర విశ్లేషణ)
- Analyze any Telugu text (letter, word, sentence, or paragraph)
- Interactive pie chart showing category distribution
- Detailed aksharaTable with frequencies
- Guru-Laghu prosody table
- Gana pattern visualization (line chart)
- Comprehensive Gana combinations
- **NEW**: Download complete analysis as JSON

#### 2. Comparative Analysis (తులనాత్మక విశ్లేషణ)
- Side-by-side comparison of two texts
- Common and unique linguistic features
- Jaccard similarity metrics
- Gana sequence comparison (overlay chart)
- Longest Common Substring (LCS) of Gana patterns
- Visual feature comparison (stacked bar chart)

### Interactive Visualizations

- **Pie Chart**: Category frequency distribution
- **Line Chart**: Guru-Laghu sequence visualization
- **Bar Chart**: Feature comparison (comparative mode)
- **Overlay Chart**: Dual Gana sequence comparison

### JSON Export (New in v0.0.7a)

The download feature provides a comprehensive JSON file containing:
- Metadata (timestamp, version, processing time)
- Input analysis (character/word/sentence counts)
- Linguistic analysis (aksharas, statistics, distributions)
- Prosody analysis (Gana sequence, combinations, statistics)
- Summary (profiles, dominant categories)

## 📱 Responsive Design

The interface automatically adapts to different screen sizes:
- **Mobile**: Single-column layout, touch-friendly buttons
- **Tablet**: Two-column layout where appropriate
- **Desktop**: Full multi-column layout with larger charts

## 🎨 User Interface

### Single Analysis Tab

```
┌─────────────────────────────────────┐
│ [Text Input Box]                    │
│                                     │
└─────────────────────────────────────┘
        [Analyze Button]
     [📥 Download JSON]  ← appears after analysis

┌─────────────────────────────────────┐
│ Info Box      │ Category Pie Chart  │
├─────────────────────────────────────┤
│ Category Counts Table               │
├─────────────────────────────────────┤
│ Aksharalu Analysis Table            │
├─────────────────────────────────────┤
│ Guru-Laghu Table                    │
├─────────────────────────────────────┤
│ Gana Combinations                   │
├─────────────────────────────────────┤
│ Gana Sequence Line Chart            │
└─────────────────────────────────────┘
```

### Comparative Analysis Tab

```
┌──────────────┬──────────────┐
│ Text Input 1 │ Text Input 2 │
└──────────────┴──────────────┘
      [Compare Button]

┌──────────────┬──────────────┐
│ Analysis 1   │ Analysis 2   │
├──────────────┼──────────────┤
│ Gana Combos  │ Gana Combos  │
├──────────────┴──────────────┤
│ Comparison Metrics (4 cards)│
├─────────────────────────────┤
│ Gana Sequence Overlay Chart │
├─────────────────────────────┤
│ LCS Panel                   │
├─────────────────────────────┤
│ Feature Comparison Chart    │
├──────────────┬──────────────┤
│ Common Tags  │ Unique Tags  │
└──────────────┴──────────────┘
```

## 🔧 Technical Details

### Technologies Used
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with flexbox and grid
- **JavaScript (ES6)**: Core analysis logic
- **Chart.js**: Interactive visualizations
- **CDN**: Chart.js loaded from jsDelivr CDN

### Browser Compatibility
- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Opera 76+

### Performance
- Analysis typically completes in < 10ms for single words
- Longer texts: 10-50ms depending on complexity
- Gana combinations limited to 50 for performance
- All processing done client-side (no server calls)

## 📊 Analysis Capabilities

### Linguistic Categories Detected
- అచ్చు (Vowels)
- హల్లు (Consonants)
- దీర్ఘ (Long vowels)
- హ్రస్వాక్షరం (Short syllables)
- సంయుక్తాక్షరం (Conjuncts)
- ద్విత్వాక్షరం (Doubled consonants)
- అనుస్వారం (Anusvaram)
- విసర్గ అక్షరం (Visarga)
- Vargams (క, చ, ట, త, ప వర్గములు)
- Place of articulation categories
- And many more...

### Gana Patterns Recognized
- **1-syllable**: Guru (U), Laghu (I)
- **2-syllable**: Lalamu (II), Lagamu/Va (IU), Galamu/Ha (UI), Gagamu (UU)
- **3-syllable**: Ya (IUU), Ma (UUU), Ta (UUI), Ra (UIU), Ja (IUI), Bha (UII), Na (III), Sa (IIU)
- **Special**: Surya, Indra, and Chandra Ganas

## 💡 Usage Examples

### Example 1: Analyze a Word
1. Open `aksharanusarika.html`
2. Enter: **తెలుగు**
3. Click **విశ్లేషించు**
4. View:
   - 3 aksharas detected
   - Category breakdown
   - Gana sequence: I I I
   - All 3 aksharas are Laghu

### Example 2: Analyze a Sentence
1. Enter: **తెలుగు వికీపీడియా ఆవిర్భావానికి**
2. Click **విశ్లేషించు**
3. View:
   - Multiple word analysis
   - Rich Gana patterns
   - Various categories detected
4. Click **📥 Download JSON**
5. Get: `telugu_analysis_2025-10-30_13-45-30.json`

### Example 3: Compare Two Words
1. Switch to **తులనాత్మక విశ్లేషణ** tab
2. Enter **తెలుగు** and **కన్నడ**
3. Click **పోల్చు**
4. View:
   - Common linguistic features
   - Unique features in each
   - Similarity scores
   - Gana sequence comparison

## 🎯 JSON Download Feature

### Filename Format
```
telugu_analysis_YYYY-MM-DD_HH-MM-SS.json
```

Example: `telugu_analysis_2025-10-30_13-45-30.json`

### JSON Structure
The downloaded JSON contains:

```json
{
  "metadata": {
    "schemaVersion": "1.0.0",
    "analysisTimestamp": "ISO-8601 timestamp",
    "analyzerVersion": "0.0.7a",
    "inputHash": "unique-id",
    "processingTimeMs": 1.23
  },
  "input": { /* text, counts, validation */ },
  "linguistic": { /* aksharas, statistics, distributions */ },
  "prosody": { /* gana sequence, combinations, statistics */ },
  "summary": { /* human-readable profiles */ }
}
```

### Use Cases for JSON
- Save analysis results for later review
- Import into other tools or scripts
- Build analysis pipelines
- Share analysis with others
- Archive linguistic research data

## 🔍 Keyboard Shortcuts

- **Enter**: Submit analysis (when focused on input)
- **Tab**: Navigate between tabs and buttons
- **Ctrl/Cmd + A**: Select all text in input box

## 📝 Tips & Best Practices

### For Best Results
- ✅ Use valid Telugu Unicode text (U+0C00 to U+0C7F)
- ✅ Paste text from Telugu keyboards or Unicode sources
- ✅ Remove non-Telugu characters for accurate analysis
- ❌ Avoid ASCII transliteration (e.g., "telugu" instead of "తెలుగు")

### Performance Tips
- Long texts (>500 aksharas) may take a few seconds to analyze
- Gana combinations are limited to 50 for very long texts
- Download JSON for detailed analysis of long texts

### Visual Tips
- Use zoom (Ctrl/Cmd + +/-) to enlarge charts
- Scroll horizontally on mobile for wide tables
- Download JSON to view complete data

## 🐛 Troubleshooting

### Issue: Charts not displaying
**Solution**: Ensure you're connected to the internet (Chart.js loads from CDN)

### Issue: Download button doesn't appear
**Solution**: Click the Analyze button first

### Issue: Telugu text not rendering properly
**Solution**: Ensure you're using a font that supports Telugu Unicode

### Issue: JSON file won't open
**Solution**: Use a text editor or JSON viewer to open .json files

## 🔄 Workflow Integration

### Export to Python
1. Download JSON from HTML interface
2. Load in Python:
```python
import json
with open('telugu_analysis_2025-10-30_13-45-30.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(data['linguistic']['statistics'])
```

### Batch Analysis
1. Open HTML file multiple times (or use tabs)
2. Analyze different texts
3. Download each JSON
4. Process batch of JSON files with your scripts

## 📚 See Also

- [Main README](../README.md) - Project overview
- [Python README](../python/README.md) - Python API documentation
- [Release Notes](../RELEASE_NOTES.md) - Version history
- [JSON Feature Guide](../docs/JSON_FEATURE_README.md) - Detailed JSON documentation

## 🆕 What's New in v0.0.7a

- ✨ JSON download functionality
- 📊 Enhanced statistics in output
- 🎨 Improved button styling
- ⚡ Single source of truth architecture (JSON → UI)
- 📦 No breaking changes to existing features

## 📧 Support

For issues and questions:
- GitHub Issues: [aksharanusarika/issues](https://github.com/yourusername/aksharanusarika/issues)
- Documentation: [docs/](../docs/)

## 📄 License

MIT License - See [LICENSE](../LICENSE) for details

---

**Aksharanusarika HTML v0.0.7a** - Interactive Telugu Linguistic Analysis Tool

**No installation required • Works offline (after initial load) • Self-contained**
