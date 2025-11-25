# ARFF File Documentation

## Overview

The `final_data.arff` file is an ARFF (Attribute-Relation File Format) version of the Telugu poems dataset, suitable for use with Weka and other machine learning tools.

## File Information

- **File**: `data/final/final_data.arff`
- **Size**: 6.0 MB
- **Rows**: 11,560 poems
- **Attributes**: 41
- **Relation Name**: `telugu_poems`

## ARFF Format

ARFF is a text-based format used by Weka for machine learning. It consists of two sections:

1. **Header Section**: Defines attributes (columns) and their types
2. **Data Section**: Contains the actual data rows

### Structure

```
@RELATION telugu_poems

@ATTRIBUTE attribute_name type
...

@DATA
value1,value2,value3,...
...
```

## Attribute Types

### STRING Attributes (5)
Text-based attributes with variable-length strings:
- `source_file` - Original JSON filename
- `file_type` - Type of file (poem_collection)
- `author_telugu` - Romanized author name
- `shatakam_title_telugu` - Romanized collection title
- `makutam_telugu` - Romanized makutam/refrain
- `poem_telugu` - Romanized poem text

### NOMINAL Attributes (1)
Categorical attribute with discrete values:
- `year` - {1850, 1931, null} - Publication year

### NUMERIC Attributes (35)
Continuous numerical values:

**Metadata**:
- `poem_id` - Poem number within collection
- `line_count` - Number of lines in poem

**Analysis Metrics**:
- `totalAksharas` - Total syllables
- `guruCount` - Heavy syllables count
- `laghuCount` - Light syllables count

**Category Counts** (29 linguistic categories):
- `antasthamu` - Antastha consonants
- `vowel` - Vowels
- `anunaasika` - Nasal consonants
- `anusvaram` - Anusvara marks
- `ooshmalu` - Sibilants
- `oshtyamu` - Labial sounds
- `ka_vargamu` - Ka-group consonants
- `kanthataalavyamu` - Guttural-palatal
- `kanthoshtyamu` - Guttural-labial
- `kanthyamu` - Guttural sounds
- `cha_vargamu` - Cha-group consonants
- `ta_vargamu` - Ta-group consonants (retroflex)
- `tha_vargamu` - Tha-group consonants (dental)
- `taalavyamu` - Palatal sounds
- `dantyamu` - Dental sounds
- `dantoshtyamu` - Dental-labial
- `dirgha` - Long vowels
- `dvitvaksharam` - Double consonants
- `pa_vargamu` - Pa-group consonants
- `parushamulu` - Hard consonants
- `plutamulu` - Pluta vowels
- `moordhanyamu` - Retroflex sounds
- `visarga_aksharam` - Visarga marks
- `samyuktaksharam` - Conjunct consonants
- `saralamulu` - Soft consonants
- `sthiramulu` - Stable consonants
- `sparshamu` - Stop consonants
- `consonant` - Total consonants
- `hrasvaksharam` - Short syllables

## Missing Values

Missing values are represented by `?` in the ARFF format.

## Usage with Weka

### Loading the File

1. **Weka Explorer**:
   ```
   File → Open file → Select final_data.arff
   ```

2. **Weka Command Line**:
   ```bash
   java weka.gui.GUIChooser
   # Then: Explorer → Open file → final_data.arff
   ```

### Sample Analyses

#### Classification
Use any of the numeric attributes to predict categories:
```
Classify → Choose Classifier → Select class attribute
```

#### Clustering
Group similar poems based on linguistic features:
```
Cluster → Choose Clusterer (e.g., SimpleKMeans)
Select attributes to use for clustering
```

#### Association Rules
Find patterns in linguistic categories:
```
Associate → Choose Associator (e.g., Apriori)
```

### Attribute Selection

For better results, you may want to:
- **Remove text attributes** before numeric analysis (source_file, author_telugu, poem_telugu, etc.)
- **Normalize numeric values** for clustering/classification
- **Use filters** to preprocess data

### Example Filters

```
Filter → Choose →
  - RemoveByName (remove STRING attributes)
  - Normalize (normalize numeric attributes)
  - Remove (remove specific attributes by index)
```

## Conversion Script

The ARFF file was generated using:

```bash
python python/convert_csv_to_arff.py
```

**Script**: `python/convert_csv_to_arff.py`

### Custom Conversion

```bash
# Default (uses final_data.csv)
python python/convert_csv_to_arff.py

# Custom input/output
python python/convert_csv_to_arff.py input.csv output.arff relation_name
```

## Data Quality

- **Total Poems**: 11,560
- **Complete Records**: All rows have data
- **Missing Values**: Minimal (mostly in optional fields like makutam)
- **Encoding**: UTF-8
- **Source**: Romanized from Telugu Unicode text

## Use Cases

### Machine Learning
- **Classification**: Predict author, era, or style based on linguistic features
- **Clustering**: Group poems by linguistic similarity
- **Regression**: Predict complexity metrics from other features

### Data Mining
- **Association Rules**: Discover relationships between linguistic categories
- **Pattern Recognition**: Identify common prosodic patterns
- **Outlier Detection**: Find unusual poems based on linguistic features

### Statistical Analysis
- **Correlation Analysis**: Relationships between different linguistic metrics
- **Distribution Analysis**: Study feature distributions across collections
- **Comparative Studies**: Compare different authors or time periods

## Related Files

- **CSV Version**: `data/final/final_data.csv` (5.8 MB)
- **Telugu Version**: `data/final/consolidated_testdata_with_analysis.csv` (8.3 MB)
- **Data Documentation**: `data/README.md`

## Schema Version

- **Generated**: 2025-10-31
- **Aksharanusarika Version**: v0.0.7a
- **ARFF Format Version**: Standard Weka format

## References

- **ARFF Format Specification**: https://waikato.github.io/weka-wiki/formats_and_processing/arff/
- **Weka Documentation**: https://www.cs.waikato.ac.nz/ml/weka/
- **Aksharanusarika**: https://github.com/your-repo/aksharanusarika

---

**Note**: This dataset contains romanized Telugu poetry with comprehensive linguistic analysis. The ARFF format makes it readily usable with Weka and other machine learning tools without requiring any preprocessing.
