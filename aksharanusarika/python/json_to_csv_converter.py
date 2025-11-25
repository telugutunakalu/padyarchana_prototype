#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON to CSV Converter for Aksharanusarika Test Data
====================================================

This script converts all JSON files in the testdata directory into a single
consolidated CSV file with all attributes as column headers.

Features:
- Recursively flattens nested JSON structures
- Handles both poem/satakam files and analysis output files
- Preserves all data without loss
- Creates null columns for missing attributes
- Generates comprehensive CSV with all possible columns

Usage:
    python json_to_csv_converter.py [input_directory] [output_file]

Example:
    python json_to_csv_converter.py ../testdata output.csv
    python json_to_csv_converter.py  # Uses defaults: ../testdata and consolidated_data.csv
"""

import json
import csv
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Set


def flatten_json(nested_json: Any, parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Recursively flatten a nested JSON object.

    Args:
        nested_json: The JSON object to flatten (dict, list, or primitive)
        parent_key: The base key for nested items
        sep: Separator between nested keys

    Returns:
        Flattened dictionary with dot-notation keys

    Examples:
        >>> flatten_json({'a': {'b': 1}})
        {'a.b': 1}
        >>> flatten_json({'a': [1, 2]})
        {'a.0': 1, 'a.1': 2}
    """
    items = []

    if isinstance(nested_json, dict):
        for key, value in nested_json.items():
            new_key = f"{parent_key}{sep}{key}" if parent_key else key

            if isinstance(value, (dict, list)):
                items.extend(flatten_json(value, new_key, sep=sep).items())
            else:
                items.append((new_key, value))

    elif isinstance(nested_json, list):
        for i, value in enumerate(nested_json):
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)

            if isinstance(value, (dict, list)):
                items.extend(flatten_json(value, new_key, sep=sep).items())
            else:
                items.append((new_key, value))
    else:
        items.append((parent_key, nested_json))

    return dict(items)


def process_poem_json(file_path: str, data: Dict) -> List[Dict[str, Any]]:
    """
    Process a poem/satakam JSON file into flat rows.

    Args:
        file_path: Path to the JSON file
        data: Loaded JSON data

    Returns:
        List of flattened dictionaries (one per poem)
    """
    rows = []

    # Extract metadata
    metadata = {
        'source_file': os.path.basename(file_path),
        'file_type': 'poem_collection',
        'shatakam_title_telugu': data.get('shatakam_title_telugu', ''),
        'author_telugu': data.get('author_telugu', ''),
        'year': data.get('year', None)
    }

    # Process each poem
    poems = data.get('poems', [])
    for poem in poems:
        row = metadata.copy()

        # Add poem-specific data
        row['poem_id'] = poem.get('id', None)
        row['makutam_telugu'] = poem.get('makutam_telugu', '')

        # Combine all lines into a single poem column
        lines = poem.get('lines_telugu', [])
        row['poem_telugu'] = '\n'.join(lines)  # Join lines with newline
        row['line_count'] = len(lines)  # Add line count

        rows.append(row)

    return rows


def process_analysis_json(file_path: str, data: Dict) -> List[Dict[str, Any]]:
    """
    Process an analysis output JSON file into flat rows.

    Args:
        file_path: Path to the JSON file
        data: Loaded JSON data

    Returns:
        List with single flattened dictionary
    """
    # Add source file info
    flat_data = {
        'source_file': os.path.basename(file_path),
        'file_type': 'analysis_output'
    }

    # Flatten the entire JSON structure
    flat_data.update(flatten_json(data))

    return [flat_data]


def collect_all_columns(rows: List[Dict[str, Any]]) -> List[str]:
    """
    Collect all unique column names from all rows.

    Args:
        rows: List of data rows

    Returns:
        Sorted list of all unique column names
    """
    all_columns: Set[str] = set()

    for row in rows:
        all_columns.update(row.keys())

    # Sort columns logically
    sorted_columns = sorted(all_columns, key=lambda x: (
        # Source file info first
        0 if x == 'source_file' else
        1 if x == 'file_type' else
        # Metadata next
        2 if x.startswith('shatakam_') or x.startswith('author_') or x == 'year' else
        # Poem ID and makutam
        3 if x == 'poem_id' else
        4 if x == 'makutam_telugu' else
        # Poem content and line count
        5 if x == 'poem_telugu' else
        6 if x == 'line_count' else
        # Analysis metadata
        7 if x.startswith('metadata.') else
        # Input data
        8 if x.startswith('input.') else
        # Linguistic data
        9 if x.startswith('linguistic.') else
        # Prosody data
        10 if x.startswith('prosody.') else
        # Summary data
        11 if x.startswith('summary.') else
        # Everything else
        12,
        x
    ))

    return sorted_columns


def convert_json_directory_to_csv(input_dir: str, output_csv: str) -> None:
    """
    Convert all JSON files in a directory to a single consolidated CSV.

    Args:
        input_dir: Directory containing JSON files
        output_csv: Path to output CSV file
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"Error: Input directory '{input_dir}' does not exist!")
        sys.exit(1)

    # Find all JSON files
    json_files = list(input_path.glob('*.json'))

    if not json_files:
        print(f"Error: No JSON files found in '{input_dir}'!")
        sys.exit(1)

    print(f"Found {len(json_files)} JSON files in '{input_dir}'")

    all_rows = []
    file_count = 0
    error_count = 0

    # Process each JSON file
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Determine file type and process accordingly
            if 'poems' in data:
                # Poem/Satakam file
                rows = process_poem_json(str(json_file), data)
            elif 'metadata' in data or 'linguistic' in data:
                # Analysis output file
                rows = process_analysis_json(str(json_file), data)
            else:
                # Generic JSON - flatten completely
                rows = process_analysis_json(str(json_file), data)

            all_rows.extend(rows)
            file_count += 1

            if file_count % 10 == 0:
                print(f"Processed {file_count} files...")

        except Exception as e:
            print(f"Error processing {json_file.name}: {e}")
            error_count += 1

    print(f"\nProcessed {file_count} files successfully, {error_count} errors")
    print(f"Total rows: {len(all_rows)}")

    # Collect all unique columns
    all_columns = collect_all_columns(all_rows)
    print(f"Total columns: {len(all_columns)}")

    # Write to CSV
    print(f"\nWriting to '{output_csv}'...")

    with open(output_csv, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_columns, extrasaction='ignore')

        # Write header
        writer.writeheader()

        # Write rows (fill missing columns with None)
        for row in all_rows:
            # Fill missing columns with None/empty string
            complete_row = {col: row.get(col, None) for col in all_columns}
            writer.writerow(complete_row)

    print(f"[SUCCESS] Created '{output_csv}'")
    print(f"  - Rows: {len(all_rows)}")
    print(f"  - Columns: {len(all_columns)}")

    # Print sample columns
    print(f"\nSample columns (first 20):")
    for i, col in enumerate(all_columns[:20], 1):
        print(f"  {i:2d}. {col}")

    if len(all_columns) > 20:
        print(f"  ... and {len(all_columns) - 20} more columns")


def main():
    """Main entry point for the script."""
    # Parse command line arguments
    if len(sys.argv) > 2:
        input_dir = sys.argv[1]
        output_csv = sys.argv[2]
    elif len(sys.argv) > 1:
        input_dir = sys.argv[1]
        output_csv = 'consolidated_data.csv'
    else:
        # Default values
        script_dir = Path(__file__).parent
        input_dir = script_dir.parent / 'testdata'
        output_csv = script_dir.parent / 'consolidated_testdata.csv'

    print("="*60)
    print("JSON to CSV Converter")
    print("="*60)
    print(f"Input directory: {input_dir}")
    print(f"Output CSV: {output_csv}")
    print()

    convert_json_directory_to_csv(str(input_dir), str(output_csv))

    print("\n" + "="*60)
    print("Conversion Complete!")
    print("="*60)


if __name__ == '__main__':
    main()
