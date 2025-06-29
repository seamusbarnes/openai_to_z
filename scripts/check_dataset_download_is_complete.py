#!/usr/bin/env python3
"""
Check for missing LAZ files based on a metadata CSV inventory.

This script compares a metadata CSV file (with a required column 'filename')
against the contents of a specified directory, and reports which expected LAZ
files are missing from that directory.

USAGE:
    python check_missing_laz.py --csv /path/to/metadata.csv --laz_dir /path/to/laz_folder

Arguments:
    --csv      Path to a CSV file listing expected LAZ filenames; must contain a 'filename' column.
    --laz_dir  Path to the directory where LAZ files should be located.

Example:
    python check_missing_laz.py --csv ./tiles_inventory.csv --laz_dir ./las_tiles/

Returns:
    Prints a list of missing filenames if any are found; otherwise confirms all are present.
"""

import os
import argparse
import pandas as pd

def check_missing_laz(csv_path, laz_dir):
    """
    Loads the metadata CSV and checks for missing files in the supplied `laz_dir`.
    Prints missing filenames, if any.

    Args:
        csv_path (str): Path to the metadata CSV file (must have a 'filename' column)
        laz_dir (str): Path to the directory containing LAZ files
    """
    # Load the metadata CSV into a DataFrame
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"ERROR: Metadata CSV not found at: {csv_path}")
        return
    except Exception as e:
        print(f"ERROR: Failed to load metadata CSV: {e}")
        return

    if "filename" not in df.columns:
        print("ERROR: The metadata CSV does not contain a 'filename' column!")
        return

    # Get all filenames in the LAZ directory
    try:
        laz_files = set(os.listdir(laz_dir))
    except FileNotFoundError:
        print(f"ERROR: LAZ directory not found at: {laz_dir}")
        return
    except Exception as e:
        print(f"ERROR: Failed to list files in LAZ_DIR: {e}")
        return

    # Find rows where the 'filename' from the CSV is not present in the directory
    missing = df[~df["filename"].isin(laz_files)]

    if missing.empty:
        print("All filenames listed in the metadata CSV exist in the LAZ directory.")
    else:
        print("The following filenames from the metadata CSV are missing in the LAZ directory:")
        print(missing['filename'].to_string(index=False))

def main():
    parser = argparse.ArgumentParser(
        description="Check which LAZ files from a metadata CSV are missing in a given directory."
    )
    parser.add_argument(
        '--csv',
        required=True,
        help="Path to the metadata CSV; must contain a 'filename' column."
    )
    parser.add_argument(
        '--laz_dir',
        required=True,
        help="Path to the directory containing the LAZ files."
    )
    args = parser.parse_args()
    check_missing_laz(args.csv, args.laz_dir)

if __name__ == "__main__":
    main()