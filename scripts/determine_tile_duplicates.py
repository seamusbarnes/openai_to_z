#!/usr/bin/env python3
"""
Determine Tile Duplicates

This script reads a CSV file with LiDAR tile metadata (including min/max latitude and longitude columns), and quantizes the bounding box coordinates to identify overlapping/duplicate tiles, based on a user-specified precision in meters (e.g. 10m, 100m, 1000m). The precision for quantization defaults to 100 meters unless changed with --precision. The script reports the number of unique sites at the chosen quantization and, optionally, can print filenames of tiles that overlap according to the quantization.

Usage:
    python determine_tile_duplicates.py --csv PATH_TO_CSV [--precision PRECISION_METERS] --overlap_examples N

Arguments:
    --csv              (str, required)    Path to CSV containing columns: min_lat, max_lat, min_lon, max_lon (and ideally a filename/tile-id). MUST be provided, e.g. /path/to/your/file.csv
    --precision        (float, optional)  Quantization precision in meters. Defaults to 100 if not specified.
    --overlap_examples (int, required)    Print up to this number of groups of overlapping tile filenames. This must be specified, e.g. 5

Example:
    python determine_tile_duplicates.py --csv your_tiles.csv --overlap_examples 5
    python determine_tile_duplicates.py --csv your_tiles.csv --precision 10 --overlap_examples 5
"""

import pandas as pd
import numpy as np
import argparse
import math

def meters_to_decimal_places(meters):
    """Convert a precision in meters to an approximate number of decimal places for latitude/longitude quantization."""
    # At the equator, 1 degree of latitude is ~111,320 meters
    if meters < 1:
        return 7
    decimal_places = max(0, int(abs(round(-math.log10(meters / 111320)))))
    return decimal_places

def parse_args():
    parser = argparse.ArgumentParser(
        description="Deduplicate overlapping tiles by quantizing boundaries."
    )
    parser.add_argument(
        "--csv",
        type=str,
        required=True,
        help="Path to CSV file (MUST be provided, e.g. /path/to/your/file.csv)"
    )
    parser.add_argument(
        "--precision",
        type=float,
        default=100,
        help="Precision for deduplication in meters (default: 100)"
    )
    parser.add_argument(
        "--overlap_examples",
        type=int,
        required=True,
        help="Print up to this number of groups of overlapping tile filenames (MUST be provided, e.g. 5)"
    )
    return parser.parse_args()

def main():
    args = parse_args()
    df = pd.read_csv(args.csv)

    # Check for required columns
    for col in ['min_lat', 'max_lat', 'min_lon', 'max_lon']:
        if col not in df.columns:
            raise ValueError(f"CSV is missing required column: {col}")

    # Determine decimal precision (~1 degree latitude = 111,320 meters)
    dec = meters_to_decimal_places(args.precision)
    print(f"Using a quantization precision of ~{args.precision:.1f} meters -> {dec} decimal places for lat/lon.")

    # Quantize bounding box
    df['min_lat_q'] = np.round(df['min_lat'], dec)
    df['max_lat_q'] = np.round(df['max_lat'], dec)
    df['min_lon_q'] = np.round(df['min_lon'], dec)
    df['max_lon_q'] = np.round(df['max_lon'], dec)

    unique_sites = df[['min_lat_q', 'max_lat_q', 'min_lon_q', 'max_lon_q']].drop_duplicates()
    print(f"Number of unique ~{args.precision:.1f}m buffered sites: {len(unique_sites)}")
    print(f"Total number of tiles read from {args.csv}: {len(df)}")
    
    n_duplicates = len(df) - len(unique_sites)
    print(f"Number of tiles that overlap with at least one other tile at this precision: {n_duplicates}")

    if args.overlap_examples > 0:
        # Find groups of overlapping tiles (i.e., duplicates by quantization)
        grouped = df.groupby(['min_lat_q', 'max_lat_q', 'min_lon_q', 'max_lon_q'])
        filename_col_candidates = [c for c in df.columns if 'file' in c.lower() or 'name' in c.lower() or 'id' in c.lower()]
        filename_col = filename_col_candidates[0] if filename_col_candidates else None

        n_reported = 0
        print(f"\nExamples of overlapping/duplicated tiles (up to {args.overlap_examples} groups):")
        for _, group in grouped:
            if len(group) > 1:
                n_reported += 1
                if filename_col:
                    print(f"  Quantized site (coords: "
                          f"{group.iloc[0]['min_lat_q']}, {group.iloc[0]['max_lat_q']}, {group.iloc[0]['min_lon_q']}, {group.iloc[0]['max_lon_q']})"
                          f": {list(group[filename_col])}")
                else:
                    print(f"  Quantized site (coords: "
                          f"{group.iloc[0]['min_lat_q']}, {group.iloc[0]['max_lat_q']}, {group.iloc[0]['min_lon_q']}, {group.iloc[0]['max_lon_q']})"
                          f": Indexes {list(group.index)}")
                if n_reported >= args.overlap_examples:
                    break
        if n_reported == 0:
            print("  No overlapping/duplicate tiles found at this precision.")

if __name__ == "__main__":
    main()