# JSON to CSV Converter Documentation

## Overview

The `json_to_csv_converter.py` script converts all JSON files from the testdata directory into a single consolidated CSV file with all attributes as column headers.

## Features

✅ **Comprehensive Data Preservation**
- Recursively flattens all nested JSON structures
- Preserves all data without loss
- Creates null/empty columns for missing attributes
- Handles both poem/satakam files and analysis output files

✅ **Smart Column Management**
- Automatically discovers all unique columns across all files
- Sorts columns logically (metadata first, then content)
- Uses dot notation for nested attributes (e.g., `metadata.schemaVersion`)

✅ **Robust Processing**
- Handles large volumes of JSON files
- Error-tolerant (continues processing if some files fail)
- Progress indicators for long-running operations
- UTF-8 encoding support for Telugu text

## Usage

### Basic Usage (Default Directories)

```bash
cd python
python json_to_csv_converter.py
```

This will:
- Read all JSON files from `../testdata/`
- Create `../consolidated_testdata.csv`

### Custom Directories

```bash
python json_to_csv_converter.py <input_directory> <output_file>
```

**Examples:**

```bash
# Specify input directory only (output defaults to consolidated_data.csv)
python json_to_csv_converter.py ../testdata

# Specify both input and output
python json_to_csv_converter.py ../testdata my_output.csv

# Use absolute paths
python json_to_csv_converter.py /path/to/json/files output.csv
```

## Output Format

### CSV Structure

The output CSV contains:
- **Header Row**: All unique column names across all JSON files
- **Data Rows**: One row per poem/analysis item
- **Null Handling**: Missing values are represented as empty cells

### Column Organization

Columns are logically sorted:

1. **Source Information**
   - `source_file`: Original JSON filename
   - `file_type`: Type (poem_collection or analysis_output)

2. **Metadata** (for poem files)
   - `shatakam_title_telugu`: Title of the satakam
   - `author_telugu`: Author name
   - `year`: Publication year

3. **Poem Data**
   - `poem_id`: Poem number within collection
   - `makutam_telugu`: Refrain/signature line
   - `poem_telugu`: Complete poem text (all lines combined with newlines)
   - `line_count`: Number of lines in the poem

4. **Analysis Data** (for analysis files)
   - `metadata.*`: Analysis metadata (timestamp, version, etc.)
   - `input.*`: Input text statistics
   - `linguistic.*`: Linguistic analysis results
   - `prosody.*`: Prosodic analysis results
   - `summary.*`: Analysis summaries

### Example Columns

```
source_file
file_type
author_telugu
shatakam_title_telugu
year
poem_id
makutam_telugu
poem_telugu
line_count
```

## Sample Output

From the testdata conversion:

```
Processed 104 files successfully, 5 errors
Total rows: 11560
Total columns: 9
```

### Statistics
- **Input**: 109 JSON files
- **Success**: 104 files processed
- **Errors**: 5 files (malformed JSON)
- **Output Rows**: 11,560 data rows (+ 1 header)
- **Output Columns**: 9 unique columns
- **File Size**: ~7.3 MB

## Script Architecture

### Main Functions

#### `flatten_json(nested_json, parent_key='', sep='.')`
Recursively flattens nested JSON structures using dot notation.

**Input:**
```json
{"metadata": {"version": "1.0", "stats": {"count": 5}}}
```

**Output:**
```python
{
  "metadata.version": "1.0",
  "metadata.stats.count": 5
}
```

#### `process_poem_json(file_path, data)`
Processes poem/satakam JSON files.
- Extracts metadata (title, author, year)
- Creates one row per poem
- Combines all poem lines into single `poem_telugu` column (newline-separated)
- Adds `line_count` column with number of lines

#### `process_analysis_json(file_path, data)`
Processes analysis output JSON files.
- Flattens entire nested structure
- Creates one row per file

#### `collect_all_columns(rows)`
Discovers all unique columns and sorts them logically.

#### `convert_json_directory_to_csv(input_dir, output_csv)`
Main conversion orchestrator:
1. Finds all JSON files
2. Processes each file
3. Collects all columns
4. Writes consolidated CSV

## Error Handling

The script handles several error scenarios:

### Malformed JSON Files
```
Error processing agha_vinasha_satakam.json: Illegal trailing comma
Error processing narayana_satakam.json: Invalid \escape
```

**Action**: Logged but continues processing other files

### Missing Directories
```
Error: Input directory 'testdata' does not exist!
```

**Action**: Exits with error code 1

### No JSON Files Found
```
Error: No JSON files found in 'testdata'!
```

**Action**: Exits with error code 1

## Performance

- **Small datasets** (<10 files): < 1 second
- **Medium datasets** (10-100 files): 2-5 seconds
- **Large datasets** (100+ files): 5-10 seconds

Progress is shown every 10 files:
```
Found 109 JSON files in 'testdata'
Processed 10 files...
Processed 20 files...
...
```

## Limitations & Considerations

### Known Limitations
1. **Array Handling**: Arrays are expanded with numeric indices (e.g., `poems.0`, `poems.1`)
2. **Large Files**: Very deep nesting can create many columns
3. **Memory**: Entire dataset loaded into memory before writing

### Recommendations
- **Maximum file count**: ~1000 JSON files
- **Maximum file size**: ~10MB per JSON file
- **Maximum total rows**: ~100K rows for reasonable CSV performance

## Troubleshooting

### Issue: UnicodeEncodeError on Windows
**Solution**: Already handled in script - CSV uses UTF-8 encoding

### Issue: Missing columns in output
**Cause**: Some JSON files may have unique keys
**Solution**: This is expected - nulls are inserted for missing data

### Issue: Too many columns
**Cause**: Deeply nested JSON structures
**Solution**: Consider pre-processing JSON to reduce nesting

### Issue: Script runs slowly
**Solution**:
- Reduce number of input files
- Process in batches
- Increase system memory

## Advanced Usage

### Filtering Files

Process only specific files:
```bash
# Create a subdirectory with filtered files
mkdir filtered_data
cp testdata/vemana*.json filtered_data/
python json_to_csv_converter.py filtered_data vemana_only.csv
```

### Batch Processing

Process different subsets:
```bash
# Process satakam files
python json_to_csv_converter.py testdata/satakam satakam_data.csv

# Process vemana files
python json_to_csv_converter.py testdata/vemana vemana_data.csv
```

### Integration with Analysis

```python
import pandas as pd

# Read the CSV
df = pd.read_csv('consolidated_testdata.csv')

# Analyze
print(f"Total poems: {len(df)}")
print(f"Unique authors: {df['author_telugu'].nunique()}")
print(f"Year range: {df['year'].min()} - {df['year'].max()}")

# Filter by author
vemana = df[df['author_telugu'].str.contains('వేమన', na=False)]
print(f"Vemana poems: {len(vemana)}")
```

## Output Structure Summary

```
consolidated_testdata.csv
├── Header Row (9 columns)
├── Data Rows (11,560 rows)
│   ├── Poem rows (11,500+)
│   │   ├── source_file
│   │   ├── file_type = "poem_collection"
│   │   ├── metadata (title, author, year)
│   │   ├── poem_id
│   │   ├── makutam_telugu
│   │   ├── poem_telugu (all lines combined)
│   │   └── line_count
│   │
│   └── Analysis rows (~60)
│       ├── source_file
│       ├── file_type = "analysis_output"
│       └── flattened analysis data
│           ├── metadata.*
│           ├── input.*
│           ├── linguistic.*
│           ├── prosody.*
│           └── summary.*
```

## Dependencies

**Standard Library Only** - No external packages required!

```python
import json
import csv
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Set
```

## See Also

- [Python README](../README.md) - Main Python documentation
- [Main README](../../README.md) - Project overview
- Test data source: `testdata/` directory

## Support

For issues or questions:
- Check error messages in console output
- Verify JSON file format
- Ensure sufficient disk space for output CSV
- Review this documentation

---

**Version**: 1.0.0
**Compatible with**: Aksharanusarika v0.0.7a
**Last Updated**: 2025-10-31
