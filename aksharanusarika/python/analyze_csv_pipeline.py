#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV Analysis Pipeline
Processes consolidated_testdata.csv and adds Aksharanusarika analysis columns.

For each row:
1. Extracts poem_telugu column
2. Runs aksharanusarika.generate_comprehensive_json() on it
3. Extracts minimal analysis data:
   - totalAksharas: Total number of aksharas
   - guruCount: Number of guru aksharas
   - laghuCount: Number of laghu aksharas
   - All 29 category counts from categoryCounts
4. Writes directly to output CSV (one row at a time)
5. Outputs new CSV with original + analysis columns (9 original + 32 analysis = 41 total)
"""

import csv
import sys
import os
from pathlib import Path
from typing import Dict, Any

# Import aksharanusarika module
sys.path.insert(0, str(Path(__file__).parent))
import aksharanusarika


def get_analysis_columns():
    """
    Returns the fixed list of analysis column names.
    Since we know exactly what columns will be generated, we don't need to discover them.
    """
    columns = ['totalAksharas', 'guruCount', 'laghuCount']

    # Add all category columns in alphabetical order
    categories = [
        'అంతస్తములు', 'అచ్చు', 'అనునాసికములు', 'అనుస్వారం',
        'ఊష్మాలు', 'ఓష్ఠ్యములు',
        'క వర్గము', 'కంఠతాలవ్యములు', 'కంఠోష్ఠ్యములు', 'కంఠ్యములు',
        'చ వర్గము', 'ట వర్గము', 'త వర్గము', 'తాలవ్యములు',
        'దంత్యములు', 'దంత్యోష్ఠ్యములు', 'దీర్ఘ', 'ద్విత్వాక్షరం',
        'ప వర్గము', 'పరుషములు', 'ప్లుతములు',
        'మూర్ధన్యములు', 'విసర్గ అక్షరం',
        'సంయుక్తాక్షరం', 'సరళములు', 'స్థిరములు', 'స్పర్శములు',
        'హల్లు', 'హ్రస్వాక్షరం'
    ]

    columns.extend(categories)
    return columns


def analyze_poem(poem_text: str) -> Dict[str, Any]:
    """
    Analyzes a Telugu poem using aksharanusarika and returns minimal analysis columns.

    Args:
        poem_text: The Telugu poem text to analyze

    Returns:
        Dictionary with minimal analysis columns:
        - totalAksharas: Total number of aksharas
        - guruCount: Number of guru aksharas
        - laghuCount: Number of laghu aksharas
        - All category counts from categoryCounts
    """
    if not poem_text or poem_text.strip() == '':
        # Return empty values for all columns
        result = {col: 0 for col in get_analysis_columns()}
        return result

    try:
        # Generate comprehensive JSON analysis (no file output)
        analysis_json = aksharanusarika.generate_comprehensive_json(poem_text, output_file=None, skip_gana_combinations = True)

        # Extract minimal required fields
        result = {}

        # Total aksharas
        result['totalAksharas'] = analysis_json['linguistic']['statistics']['totalAksharas']

        # Guru and Laghu counts from prosody statistics
        result['guruCount'] = analysis_json['prosody']['statistics']['guruCount']
        result['laghuCount'] = analysis_json['prosody']['statistics']['laghuCount']

        # All category counts
        category_counts = analysis_json['linguistic']['categoryCounts']

        # Add all categories with their counts (default to 0 if not present)
        all_categories = [
            'అచ్చు', 'హల్లు', 'దీర్ఘ', 'హ్రస్వాక్షరం', 'సంయుక్తాక్షరం', 'ద్విత్వాక్షరం',
            'విసర్గ అక్షరం', 'అనుస్వారం', 'ప్లుతములు', 'సరళములు', 'పరుషములు', 'స్థిరములు',
            'క వర్గము', 'చ వర్గము', 'ట వర్గము', 'త వర్గము', 'ప వర్గము',
            'స్పర్శములు', 'ఊష్మాలు', 'అంతస్తములు',
            'కంఠ్యములు', 'తాలవ్యములు', 'మూర్ధన్యములు', 'దంత్యములు', 'ఓష్ఠ్యములు',
            'అనునాసికములు', 'కంఠతాలవ్యములు', 'కంఠోష్ఠ్యములు', 'దంత్యోష్ఠ్యములు'
        ]

        for category in all_categories:
            result[category] = category_counts.get(category, 0)

        return result
    except Exception as e:
        print(f"Error analyzing poem: {e}")
        # Return zeros for all columns on error
        result = {col: 0 for col in get_analysis_columns()}
        return result


def process_csv_with_analysis(input_csv: str, output_csv: str):
    """
    Processes input CSV one row at a time, analyzes each poem, and writes output CSV.

    Args:
        input_csv: Path to input consolidated_testdata.csv
        output_csv: Path to output CSV with analysis columns
    """
    print("=" * 60)
    print("Aksharanusarika CSV Analysis Pipeline")
    print("=" * 60)
    print(f"Input CSV: {input_csv}")
    print(f"Output CSV: {output_csv}")
    print()

    # Check if input file exists
    if not os.path.exists(input_csv):
        print(f"Error: Input file '{input_csv}' does not exist!")
        sys.exit(1)

    # Get analysis columns (fixed, known ahead of time)
    analysis_columns = get_analysis_columns()

    print(f"Analysis columns: {len(analysis_columns)}")
    print("   - totalAksharas")
    print("   - guruCount")
    print("   - laghuCount")
    print(f"   - 29 category count columns")
    print()

    # Process row by row
    print("Processing poems one-by-one...")
    print()

    row_count = 0
    with open(input_csv, 'r', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        original_fieldnames = reader.fieldnames

        # Combine original columns with analysis columns
        output_fieldnames = list(original_fieldnames) + analysis_columns

        # Open output file for writing
        with open(output_csv, 'w', encoding='utf-8', newline='') as f_out:
            writer = csv.DictWriter(f_out, fieldnames=output_fieldnames)
            writer.writeheader()

            # Process each row immediately
            for row in reader:
                row_count += 1

                # Extract poem text
                poem_text = row.get('poem_telugu', '')

                # Analyze the poem
                analysis = analyze_poem(poem_text)

                # Combine original row with analysis
                output_row = row.copy()
                output_row.update(analysis)

                # Write immediately to CSV
                writer.writerow(output_row)

                # Progress indicator
                print(f"Processed poem {row_count}: {row.get('source_file', 'unknown')} - ID {row.get('poem_id', 'N/A')}")

    print()
    print("=" * 60)
    print("Analysis Complete!")
    print("=" * 60)
    print(f"Total poems processed: {row_count}")
    print(f"Original columns: {len(original_fieldnames)}")
    print(f"Analysis columns added: {len(analysis_columns)}")
    print(f"Total output columns: {len(output_fieldnames)}")
    print()
    print(f"[SUCCESS] Created '{output_csv}'")
    print("=" * 60)


def main():
    """Main entry point."""
    # Default paths
    default_input = "consolidated_testdata.csv"
    default_output = "consolidated_testdata_with_analysis.csv"

    # Parse command line arguments
    if len(sys.argv) > 1:
        input_csv = sys.argv[1]
    else:
        input_csv = default_input

    if len(sys.argv) > 2:
        output_csv = sys.argv[2]
    else:
        output_csv = default_output

    # Process the CSV
    process_csv_with_analysis(input_csv, output_csv)


if __name__ == "__main__":
    main()
