#!/usr/bin/env python3
"""
Split a list of filenames from a metadata CSV into multiple .txt files for parallel download.

This CLI tool reads a metadata CSV file (which MUST contain a 'filename' column),
splits the filenames into N groups in round-robin fashion, and writes each group
into a separate .txt file. These output text files can be used for parallel downloads.

USAGE:
    python split_filenames.py -i /path/to/metadata.csv -n 5 -o laz_files

ARGUMENTS:
    -i, --input_csv       Path to the input metadata CSV file with a 'filename' column.
    -n, --num_splits      Number of .txt files to split the filenames into (default: 5).
    -o, --output_prefix   Prefix for the output .txt files. Output files will be named:
                          <prefix>_0.txt, <prefix>_1.txt, ..., etc. (default: "laz_files").
EXAMPLES:
    python split_filenames.py -i meta.csv -n 8 -o download_chunk

Each output .txt file will contain (about) 1/N of the filenames from the CSV, suitable for parallel processing.
"""

import argparse
import pandas as pd
import sys

def generate_file_list(df, output_filename, split_idx, num_splits):
    """
    Write every Nth filename from df['filename'] into output_filename, starting from split_idx.
    """
    with open(output_filename, "w", encoding="utf-8") as f:
        for i in range(split_idx, len(df), num_splits):
            line = df.at[i, "filename"]
            f.write(f"{line}\n")

def main():
    parser = argparse.ArgumentParser(
        description="Split CSV filename list into multiple .txt files for parallel download.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("-i", "--input_csv", required=True, help="Path to metadata CSV with 'filename' column.")
    parser.add_argument("-n", "--num_splits", type=int, default=5, help="Number of splits (default: 5).")
    parser.add_argument("-o", "--output_prefix", default="laz_files", help="Prefix for output .txt files (default: laz_files)")
    
    args = parser.parse_args()

    # Read the CSV
    try:
        df = pd.read_csv(args.input_csv)
    except Exception as e:
        print(f"ERROR: Could not read metadata CSV: {e}", file=sys.stderr)
        sys.exit(1)

    if "filename" not in df.columns:
        print("ERROR: 'filename' column not found in metadata CSV!", file=sys.stderr)
        sys.exit(1)

    # Write split files
    for split_idx in range(args.num_splits):
        output_filename = f"{args.output_prefix}_{split_idx}.txt"
        generate_file_list(df, output_filename, split_idx, args.num_splits)
        print(f"Wrote: {output_filename}")

    print("Done! Each .txt contains a subset of filenames for parallel download.")

if __name__ == "__main__":
    main()