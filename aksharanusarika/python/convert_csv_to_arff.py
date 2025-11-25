#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CSV to ARFF Converter
Converts final_data.csv to ARFF format for use with Weka and machine learning tools.

ARFF (Attribute-Relation File Format) is a text file format used by Weka.
It consists of a header section defining attributes and a data section.
"""

import csv
import sys
import os
from typing import List, Dict, Set


def infer_attribute_type(column_name: str, all_values: List[str]) -> str:
    """
    Infers the ARFF attribute type based on column name and ALL values.

    Args:
        column_name: Name of the column
        all_values: ALL values from the column (not just a sample)

    Returns:
        ARFF attribute type (NUMERIC, STRING, or {value1,value2,...})
    """
    # Text columns should be STRING
    text_columns = {'source_file', 'file_type', 'author_telugu',
                   'shatakam_title_telugu', 'makutam_telugu', 'poem_telugu'}

    if column_name in text_columns:
        return 'STRING'

    # Check if all non-empty values are numeric
    numeric_values = []
    for val in all_values:
        if val and val.strip():
            try:
                float(val)
                numeric_values.append(True)
            except ValueError:
                numeric_values.append(False)

    # If all values are numeric, it's NUMERIC
    if numeric_values and all(numeric_values):
        return 'NUMERIC'

    # Check if it's a categorical variable with few unique values
    unique_values = set(v.strip() for v in all_values if v and v.strip())

    # If fewer than 100 unique values and not a text column, make it nominal
    if len(unique_values) < 100 and column_name not in text_columns:
        # Create nominal type: {value1,value2,value3}
        # Quote values that contain spaces, commas, or special characters
        sorted_values = sorted(unique_values)
        quoted_values = []
        for val in sorted_values:
            # Quote if contains space, comma, or special chars
            if ' ' in val or ',' in val or '-' in val or any(c in val for c in '{}[]()'):
                quoted_values.append(f"'{val}'")
            else:
                quoted_values.append(val)
        return '{' + ','.join(quoted_values) + '}'

    return 'STRING'


def escape_arff_value(value: str, attr_type: str) -> str:
    """
    Escapes a value for ARFF format.

    Args:
        value: The value to escape
        attr_type: The attribute type

    Returns:
        Escaped value
    """
    if not value or value.strip() == '':
        return '?'  # Missing value in ARFF

    # If STRING type, wrap in quotes and escape internal quotes
    if attr_type == 'STRING':
        # Escape quotes and backslashes
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        # Replace newlines with space
        escaped = escaped.replace('\n', ' ').replace('\r', '')
        return f'"{escaped}"'

    # For NOMINAL types (start with {), check if value needs quoting
    if attr_type.startswith('{'):
        val = value.strip()
        # Quote if contains space, comma, or special chars
        if ' ' in val or ',' in val or any(c in val for c in '{}[]()'):
            # Escape single quotes inside the value
            escaped = val.replace("'", "\\'")
            return f"'{escaped}'"
        return val

    # For NUMERIC, return as-is
    return value.strip()


def convert_csv_to_arff(input_csv: str, output_arff: str, relation_name: str = 'telugu_poems'):
    """
    Converts CSV file to ARFF format.

    Args:
        input_csv: Path to input CSV file
        output_arff: Path to output ARFF file
        relation_name: Name of the relation (dataset name)
    """
    print("=" * 60)
    print("CSV to ARFF Converter")
    print("=" * 60)
    print(f"Input CSV: {input_csv}")
    print(f"Output ARFF: {output_arff}")
    print(f"Relation name: {relation_name}")
    print()

    # Check if input file exists
    if not os.path.exists(input_csv):
        print(f"Error: Input file '{input_csv}' does not exist!")
        sys.exit(1)

    # Read CSV and collect ALL data to infer types accurately
    print("Reading CSV and collecting all values for type inference...")

    all_data = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames

        # Read ALL rows to ensure we catch all nominal values
        for row in reader:
            all_data.append(row)

    print(f"Read {len(all_data)} rows")
    print(f"Total attributes: {len(fieldnames)}")
    print()

    # Infer attribute types from ALL data
    print("Inferring attribute types from complete dataset...")
    attribute_types = {}

    for col in fieldnames:
        all_values = [row[col] for row in all_data]
        attr_type = infer_attribute_type(col, all_values)
        attribute_types[col] = attr_type
        print(f"  {col}: {attr_type[:50]}{'...' if len(attr_type) > 50 else ''}")

    print()

    # Write ARFF file
    print("Writing ARFF file...")

    with open(output_arff, 'w', encoding='utf-8') as f_out:
        # Write header
        f_out.write(f"@RELATION {relation_name}\n\n")

        # Write attributes
        for col in fieldnames:
            attr_type = attribute_types[col]
            f_out.write(f"@ATTRIBUTE {col} {attr_type}\n")

        f_out.write("\n@DATA\n")

        # Write data section from already-loaded data
        row_count = 0

        for row in all_data:
            row_count += 1

            # Convert row to ARFF format
            values = []
            for col in fieldnames:
                value = row[col]
                attr_type = attribute_types[col]
                escaped_value = escape_arff_value(value, attr_type)
                values.append(escaped_value)

            # Write comma-separated values
            f_out.write(','.join(values) + '\n')

            # Progress indicator
            if row_count % 1000 == 0:
                print(f"  Processed {row_count} rows...")

    print(f"  Processed all {row_count} rows")
    print()

    # Get file size
    file_size = os.path.getsize(output_arff)
    size_mb = file_size / (1024 * 1024)

    print("=" * 60)
    print("Conversion Complete!")
    print("=" * 60)
    print(f"Total rows: {row_count}")
    print(f"Total attributes: {len(fieldnames)}")
    print(f"Output file size: {size_mb:.2f} MB")
    print()
    print(f"[SUCCESS] Created '{output_arff}'")
    print("=" * 60)


def main():
    """Main entry point."""
    # Default paths
    default_input = "data/final/final_data.csv"
    default_output = "data/final/final_data.arff"
    default_relation = "telugu_poems"

    # Parse command line arguments
    if len(sys.argv) > 1:
        input_csv = sys.argv[1]
    else:
        input_csv = default_input

    if len(sys.argv) > 2:
        output_arff = sys.argv[2]
    else:
        output_arff = default_output

    if len(sys.argv) > 3:
        relation_name = sys.argv[3]
    else:
        relation_name = default_relation

    # Convert CSV to ARFF
    convert_csv_to_arff(input_csv, output_arff, relation_name)


if __name__ == "__main__":
    main()
