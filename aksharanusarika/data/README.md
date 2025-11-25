# Data Directory

This directory contains all processed data files from the Aksharanusarika pipeline.

## Directory Structure

```
data/
├── final/                           # Final output files
│   ├── consolidated_testdata_with_analysis.csv    # 8.3 MB - Full dataset with Telugu text and analysis
│   └── final_data.csv                              # 5.8 MB - Transliterated to English with analysis
│
└── intermediate/                    # Intermediate processing files
    └── consolidated_testdata.csv                   # 7.3 MB - Combined poems before analysis
```

## File Descriptions

### Final Files (data/final/)

#### `consolidated_testdata_with_analysis.csv` (8.3 MB)
**Description**: Complete dataset with Telugu text and linguistic analysis.

**Columns** (41 total):
- **Metadata** (9 columns): source_file, file_type, author_telugu, shatakam_title_telugu, year, poem_id, makutam_telugu, poem_telugu, line_count
- **Analysis Metrics** (3 columns): totalAksharas, guruCount, laghuCount
- **Telugu Category Counts** (29 columns): అచ్చు, హల్లు, దీర్ఘ, సంయుక్తాక్షరం, etc.

**Rows**: 11,560 poems

**Use Case**: For analysis requiring original Telugu text

---

#### `final_data.csv` (5.8 MB)
**Description**: Transliterated dataset with romanized English text and English column names.

**Columns** (41 total):
- **Metadata** (9 columns): source_file, file_type, author_telugu, shatakam_title_telugu, year, poem_id, makutam_telugu, poem_telugu, line_count
  - Note: Text in these columns is romanized (e.g., "daurabhaā saubarahamaṇayaśarama")
- **Analysis Metrics** (3 columns): totalAksharas, guruCount, laghuCount
- **English Category Counts** (29 columns): vowel, consonant, dirgha, samyuktaksharam, antasthamu, etc.

**Rows**: 11,560 poems

**Use Case**: For analysis tools that don't support Telugu Unicode, or for easier data manipulation

**Transliteration Example**:
- Telugu: `తెలుగు భాష` → Roman: `telaugau bhaāṣa`
- Telugu: `సుమతీ!` → Roman: `saumatīi!`

---

### Intermediate Files (data/intermediate/)

#### `consolidated_testdata.csv` (7.3 MB)
**Description**: Combined poems from all JSON files in testdata/, before analysis.

**Columns** (9 total):
- source_file, file_type, author_telugu, shatakam_title_telugu, year, poem_id, makutam_telugu, poem_telugu, line_count

**Rows**: 11,560 poems

**Processing**:
- Created from 104 JSON files (5 files had errors)
- All poem lines combined into single `poem_telugu` column
- Added `line_count` to track number of lines

**Use Case**: Base dataset for reprocessing with different analysis parameters

---

## Processing Pipeline

```
testdata/ (109 JSON files)
    ↓
[json_to_csv_converter.py]
    ↓
data/intermediate/consolidated_testdata.csv (7.3 MB)
    ↓
[analyze_csv_pipeline.py]
    ↓
data/final/consolidated_testdata_with_analysis.csv (8.3 MB)
    ↓
[transliterate_csv_to_english.py]
    ↓
data/final/final_data.csv (5.8 MB)
```

## Column Mappings (Telugu → English)

| Telugu Column Name | English Column Name | Description |
|-------------------|---------------------|-------------|
| అచ్చు | vowel | Vowel count |
| హల్లు | consonant | Consonant count |
| దీర్ఘ | dirgha | Long vowel count |
| హ్రస్వాక్షరం | hrasvaksharam | Short syllable count |
| సంయుక్తాక్షరం | samyuktaksharam | Conjunct consonant count |
| ద్విత్వాక్షరం | dvitvaksharam | Double consonant count |
| విసర్గ అక్షరం | visarga_aksharam | Visarga count |
| అనుస్వారం | anusvaram | Anusvara count |
| ప్లుతములు | plutamulu | Plutamulu count |
| సరళములు | saralamulu | Saralamulu count |
| పరుషములు | parushamulu | Parushamulu count |
| స్థిరములు | sthiramulu | Sthiramulu count |
| క వర్గము | ka_vargamu | Ka vargamu count |
| చ వర్గము | cha_vargamu | Cha vargamu count |
| ట వర్గము | ta_vargamu | Ta vargamu count |
| త వర్గము | tha_vargamu | Tha vargamu count |
| ప వర్గము | pa_vargamu | Pa vargamu count |
| స్పర్శములు | sparshamu | Sparsha consonants |
| ఊష్మాలు | ooshmalu | Ushma consonants |
| అంతస్తములు | antasthamu | Antastha consonants |
| కంఠ్యములు | kanthyamu | Kanthya (guttural) |
| తాలవ్యములు | taalavyamu | Taalavya (palatal) |
| మూర్ధన్యములు | moordhanyamu | Moordhanya (retroflex) |
| దంత్యములు | dantyamu | Dantya (dental) |
| ఓష్ఠ్యములు | oshtyamu | Oshthya (labial) |
| అనునాసికములు | anunaasika | Anunaasika (nasal) |
| కంఠతాలవ్యములు | kanthataalavyamu | Kanthataalavya |
| కంఠోష్ఠ్యములు | kanthoshtyamu | Kanthoshthya |
| దంత్యోష్ఠ్యములు | dantoshtyamu | Dantoshtyamu |

## Statistics

- **Total Poems**: 11,560
- **Source JSON Files**: 109 (104 processed successfully, 5 errors)
- **Authors**: Multiple Telugu poets
- **Year Range**: Historical Telugu poetry collections
- **File Size Total**: ~21.4 MB (all files combined)

## Version

- **Generated**: 2025-10-31
- **Aksharanusarika Version**: v0.0.7a
- **Python Version**: 3.14

## See Also

- [Main README](../README.md) - Project overview
- [Python README](../python/README.md) - Python scripts documentation
- [JSON to CSV README](../python/JSON_TO_CSV_README.md) - CSV converter documentation
