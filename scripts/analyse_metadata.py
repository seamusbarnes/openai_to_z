"""
LiDAR Ground Classification Tile Analysis

This script analyzes LiDAR tile statistics with respect to ground-point classifications.

Inputs:
    - Inventory CSV (required): Path to LiDAR tile inventory CSV file.
    - Metadata CSV (required): Path to per-tile ground-point metadata CSV file.

Features:
    - Plots histogram and CDF of per-tile ground point percentage.
    - Reports fraction/count of tiles over user-supplied threshold percent ground points.
    - Optionally fetches a satellite image for a user-chosen ground density tile (via ESRI).

Usage example:
    python analyze_lidar_ground.py --inventory_csv my_inventory.csv --metadata_csv my_metadata.csv --example_tile_density medium

Command-line arguments:
    --inventory_csv PATH         Path to tile inventory CSV file (required)
    --metadata_csv PATH          Path to tile ground-point metadata CSV file (required)
    --ground_pct_thresholds ...  Thresholds (percent) for high ground-point tiles (default: 5 10 20 30)
    --high_ground_filter FLOAT   Fraction threshold for "high ground" tiles (default 0.1 = 10%)
    --example_tile_density STR   Show ESRI image for [high|medium|low] ground tile (default: high)
    --no_plots                   Disable all histograms and CDF plots
    --no_image                   Disable the ESRI image display
    --esri_px_width INT          Satellite image width (pixels, default: 512)
    --esri_px_height INT         Satellite image height (pixels, default: 512)

Outputs:
    - Displays histogram and CDF of % ground points per tile.
    - Prints fraction and count of tiles above each threshold.
    - Optionally, displays an ESRI imagery tile for a tile with high/medium/low ground point percentage.
"""

import pandas as pd
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import argparse

def load_tile_data(inventory_csv, metadata_csv):
    """Load inventory and metadata CSV files as pandas DataFrames."""
    df_inv = pd.read_csv(inventory_csv)
    df_meta = pd.read_csv(metadata_csv)
    return df_inv, df_meta

def plot_ground_pct_histogram(df_meta):
    """Plot histogram of percentage ground points in tiles."""
    ground_pcts = df_meta['ground_pct'].dropna() * 100
    plt.figure()
    plt.hist(ground_pcts, bins=30)
    plt.xlabel('Ground Point Percentage')
    plt.ylabel('Number of Tiles')
    plt.title('Distribution of % Ground Points per Tile')
    plt.tight_layout()
    plt.show()

def plot_ground_pct_cdf(df_meta):
    """Plot cumulative distribution of ground percentage across tiles."""
    ground_pcts = df_meta['ground_pct'].dropna() * 100
    sorted_pcts = np.sort(ground_pcts)
    cum_frac = np.arange(1, len(sorted_pcts) + 1) / len(sorted_pcts)
    plt.figure(figsize=(8, 5))
    plt.step(sorted_pcts, cum_frac, where='post')
    plt.xlabel('Ground Points Percentage')
    plt.ylabel('Cumulative Fraction of Tiles')
    plt.title('Cumulative Distribution of % Ground Points per Tile')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def print_threshold_stats(df_meta, thresholds):
    """Print counts/fractions of tiles above various ground-point % thresholds."""
    ground_pcts = df_meta['ground_pct'].dropna() * 100
    for thresh in thresholds:
        pct_above = np.mean(ground_pcts > thresh)
        count_above = np.sum(ground_pcts > thresh)
        print(f"Tiles with ground point % > {thresh}%: {pct_above*100:.2f}% ({count_above} tiles)")

def get_tile_bbox(df_meta, filename, expand=0.02):
    """Return slightly padded bbox (min_lat, max_lat, min_lon, max_lon)."""
    row = df_meta[df_meta["filename"] == filename]
    if row.empty:
        raise ValueError(f"{filename} not found in metadata")
    min_lat = float(row['min_lat'].values[0]) - expand
    max_lat = float(row['max_lat'].values[0]) + expand
    min_lon = float(row['min_lon'].values[0]) - expand
    max_lon = float(row['max_lon'].values[0]) + expand
    return min_lat, max_lat, min_lon, max_lon

def fetch_esri_satellite_by_bbox(bbox, px_width=512, px_height=512):
    """
    Fetch ESRI satellite image from bounding box.
    bbox: (min_lat, max_lat, min_lon, max_lon)
    Returns a PIL Image.
    """
    min_lat, max_lat, min_lon, max_lon = bbox
    if abs(max_lat - min_lat) < 1e-4 or abs(max_lon - min_lon) < 1e-4:
        raise ValueError("Bounding box is too small for satellite imagery request.")
    url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
    params = {
        "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "bboxSR": 4326,
        "imageSR": 4326,
        "size": f"{px_width},{px_height}",
        "format": "jpg",
        "f": "image"
    }
    resp = requests.get(url, params=params)
    resp.raise_for_status()
    return Image.open(BytesIO(resp.content))

def show_esri_image_for_tile(df_meta, filename, px_width=512, px_height=512, expand=0.02):
    """Fetch and display ESRI satellite image for given tile filename."""
    bbox = get_tile_bbox(df_meta, filename, expand=expand)
    try:
        img = fetch_esri_satellite_by_bbox(bbox, px_width=px_width, px_height=px_height)
        plt.figure(figsize=(5, 5))
        plt.imshow(img)
        plt.title(filename)
        plt.axis('off')
        plt.show()
    except Exception as e:
        print(f"ESRI server/image error for {filename}: {e}")

def pick_example_tile(df_meta, density='high', high_ground_filter=0.1):
    """
    Select a tile filename based on requested ground density.
    density = 'high', 'medium', or 'low'
    """
    ground_pcts = df_meta['ground_pct'].dropna()
    idx = None

    if density == 'high':
        subset = df_meta[ground_pcts > high_ground_filter]
        if not subset.empty:
            idx = subset['ground_pct'].idxmax()
    elif density == 'medium':
        median_val = ground_pcts.median()
        idx = (ground_pcts - median_val).abs().idxmin()
    elif density == 'low':
        subset = df_meta[ground_pcts == ground_pcts.min()]
        if not subset.empty:
            idx = subset.index[0]
    else:
        raise ValueError(f"Unknown density type: {density}")

    if idx is not None:
        filename = df_meta.loc[idx, "filename"]
        pct = df_meta.loc[idx, "ground_pct"] * 100
        return filename, pct
    else:
        return None, None

def main(
    inventory_csv,
    metadata_csv,
    ground_pct_thresholds=[5, 10, 20, 30],
    high_ground_filter=0.1,
    do_plots=True,
    show_example_tile=True,
    example_tile_density='high',
    esri_px_width=512,
    esri_px_height=512,
):
    """
    Main analysis routine for LiDAR ground-classified point stats and ESRI image examples.
    """
    df_inv, df_meta = load_tile_data(inventory_csv, metadata_csv)
    print(f"Loaded {len(df_inv)} inventory records; {len(df_meta)} metadata records.")

    if do_plots:
        plot_ground_pct_histogram(df_meta)
        plot_ground_pct_cdf(df_meta)
        print_threshold_stats(df_meta, ground_pct_thresholds)

    if show_example_tile:
        example_filename, pct = pick_example_tile(
            df_meta,
            density=example_tile_density,
            high_ground_filter=high_ground_filter
        )
        if example_filename is None:
            print(f"No tile found for density '{example_tile_density}'.")
            return
        print(f"Example tile ({example_tile_density} ground density, {pct:.2f}% ground points): {example_filename}")
        show_esri_image_for_tile(
            df_meta,
            example_filename,
            px_width=esri_px_width,
            px_height=esri_px_height,
            expand=0.02
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Analyze LiDAR tile ground point statistics and browse satellite imagery. '
                    'Both --inventory_csv and --metadata_csv are required.'
    )
    parser.add_argument('--inventory_csv', type=str, required=True,
                        help='Path to the tile inventory CSV file.')
    parser.add_argument('--metadata_csv', type=str, required=True,
                        help='Path to the per-tile ground-point metadata CSV file.')
    parser.add_argument('--ground_pct_thresholds', type=float, nargs='+', default=[5, 10, 20, 30],
                        help='List of ground point percent thresholds, e.g. 5 10 20 30')
    parser.add_argument('--high_ground_filter', type=float, default=0.1,
                        help='Fraction threshold for "high ground" tiles (e.g. 0.1 for 10%%)')
    parser.add_argument('--example_tile_density', choices=['high', 'medium', 'low'], default='high',
                        help='Show example for a [high|medium|low] ground density tile (default: high)')
    parser.add_argument('--no_plots', dest='do_plots', default=True, action='store_false',
                        help='Disable plots.')
    parser.add_argument('--no_image', dest='show_example_tile', default=True, action='store_false',
                        help='Disable fetching/displaying an ESRI tile.')
    parser.add_argument('--esri_px_width', type=int, default=512,
                        help='Satellite image width (pixels)')
    parser.add_argument('--esri_px_height', type=int, default=512,
                        help='Satellite image height (pixels)')

    args = parser.parse_args()

    main(
        inventory_csv=args.inventory_csv,
        metadata_csv=args.metadata_csv,
        ground_pct_thresholds=args.ground_pct_thresholds,
        high_ground_filter=args.high_ground_filter,
        do_plots=args.do_plots,
        show_example_tile=args.show_example_tile,
        example_tile_density=args.example_tile_density,
        esri_px_width=args.esri_px_width,
        esri_px_height=args.esri_px_height
    )