"""
Analyze percentage of LiDAR tiles with high ground-point classification.

- Loads tile inventory and metadata CSVs.
- Plots histogram and CDF of per-tile ground classification fraction.
- Calculates fraction and count of tiles over ground-point thresholds.
- (Optionally) fetches and displays ESRI satellite images for tiles of interest.
"""

import os
import pandas as pd
import numpy as np
import requests
from PIL import Image
from io import BytesIO
import matplotlib.pyplot as plt
import argparse

# ---- Config Defaults ----

DEFAULT_CONFIG = {
    "inventory_csv": "cms_brazil_lidar_tile_inventory.csv",
    "metadata_csv": "cms_brazil_lidar_tile_metadata.csv",
    "data_dir": os.path.join(os.getcwd(), "data", "metadata"),

    "ground_pct_thresholds": [5, 10, 20, 30],  # percent
    "high_ground_filter": 0.1,                 # decimal fraction
    "esri_px_width": 512,
    "esri_px_height": 512,
}


def get_path_to_data(data_dir, filename):
    """Return absolute path to file in supplied directory."""
    return os.path.join(data_dir, filename)


def load_tile_data(data_dir, inventory_csv, metadata_csv):
    """Load tile inventory and metadata CSVs as pandas DataFrames."""
    df_inv = pd.read_csv(get_path_to_data(data_dir, inventory_csv))
    df_meta = pd.read_csv(get_path_to_data(data_dir, metadata_csv))
    return df_inv, df_meta


def plot_ground_pct_histogram(df_meta, savefig_path=None):
    """Plot histogram of percentage ground points in tiles."""
    ground_pcts = (df_meta['ground_pct'] * 100).dropna()
    plt.figure()
    plt.hist(ground_pcts, bins=30)
    plt.xlabel('Ground Point Percentage')
    plt.ylabel('Number of Tiles')
    plt.title('Distribution of % Ground Points per Tile')
    plt.tight_layout()
    if savefig_path:
        plt.savefig(savefig_path)
    else:
        plt.show()


def plot_ground_pct_cdf(df_meta, savefig_path=None):
    """Plot cumulative distribution of ground percentage across tiles."""
    ground_pcts = (df_meta['ground_pct'] * 100).dropna()
    sorted_pcts = np.sort(ground_pcts)
    cum_frac = np.arange(1, len(sorted_pcts) + 1) / len(sorted_pcts)
    plt.figure(figsize=(8, 5))
    plt.step(sorted_pcts, cum_frac, where='post')
    plt.xlabel('Ground Points Percentage')
    plt.ylabel('Cumulative Fraction of Tiles')
    plt.title('Cumulative Distribution of % Ground Points per Tile')
    plt.grid(True)
    plt.tight_layout()
    if savefig_path:
        plt.savefig(savefig_path)
    else:
        plt.show()


def print_threshold_stats(df_meta, thresholds):
    """Print counts/fractions of tiles above various ground-point % thresholds."""
    ground_pcts = (df_meta['ground_pct'] * 100).dropna()  # in percent
    for thresh in thresholds:
        pct_above = np.mean(ground_pcts > thresh)
        count_above = np.sum(ground_pcts > thresh)
        print(f"Percent of tiles with ground point % > {thresh}%: {(pct_above*100):.2f}% ({count_above} tiles)")


def get_tile_bbox(df_meta, filename):
    """Return bounding box (min_lat, max_lat, min_lon, max_lon) for a given tile."""
    row = df_meta[df_meta["filename"] == filename]
    if row.empty:
        raise ValueError(f"{filename} not found in metadata")
    return float(row['min_lat'].values[0]), float(row['max_lat'].values[0]), float(row['min_lon'].values[0]), float(row['max_lon'].values[0])


def fetch_esri_satellite_by_bbox(bbox, px_width=512, px_height=512):
    """
    Fetch ESRI satellite image from bounding box.
    bbox: (min_lat, max_lat, min_lon, max_lon)
    Returns a PIL Image.
    """
    min_lat, max_lat, min_lon, max_lon = bbox
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


def show_esri_image_for_tile(df_meta, filename, px_width=512, px_height=512):
    """
    Fetch and display ESRI satellite image for given tile filename.
    """
    bbox = get_tile_bbox(df_meta, filename)
    try:
        img = fetch_esri_satellite_by_bbox(bbox, px_width=px_width, px_height=px_height)
        plt.figure(figsize=(5, 5))
        plt.imshow(img)
        plt.title(filename)
        plt.axis('off')
        plt.show()
    except Exception as e:
        print(f"ESRI server/image error for {filename}: {e}")


def main(
    data_dir=DEFAULT_CONFIG['data_dir'],
    inventory_csv=DEFAULT_CONFIG['inventory_csv'],
    metadata_csv=DEFAULT_CONFIG['metadata_csv'],
    ground_pct_thresholds=DEFAULT_CONFIG['ground_pct_thresholds'],
    high_ground_filter=DEFAULT_CONFIG['high_ground_filter'],
    do_plots=True,
    show_example_tile=True,
    esri_px_width=DEFAULT_CONFIG['esri_px_width'],
    esri_px_height=DEFAULT_CONFIG['esri_px_height'],
):
    """
    Main analysis routine for LiDAR ground-classified point stats and ESRI image examples.
    """
    df_inv, df_meta = load_tile_data(data_dir, inventory_csv, metadata_csv)
    print(f"Loaded {len(df_inv)} inventory records; {len(df_meta)} metadata records.")

    if do_plots:
        plot_ground_pct_histogram(df_meta)
        plot_ground_pct_cdf(df_meta)
        print_threshold_stats(df_meta, ground_pct_thresholds)

    if show_example_tile:
        df_high_ground = df_meta[df_meta['ground_pct'] > high_ground_filter]  # e.g. >10%
        if len(df_high_ground) == 0:
            print(f"No tiles with > {high_ground_filter*100:.1f}% ground points found.")
            return
        example_filename = df_high_ground.iloc[0]["filename"]
        print(f"Example tile with high ground points: {example_filename}")
        show_esri_image_for_tile(df_meta, example_filename, px_width=esri_px_width, px_height=esri_px_height)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Analyze LiDAR tile ground point statistics and browse imagery.')

    parser.add_argument('--data_dir', type=str, default=DEFAULT_CONFIG['data_dir'],
                        help='Directory containing inventory/metadata CSV files.')
    parser.add_argument('--inventory_csv', type=str, default=DEFAULT_CONFIG['inventory_csv'],
                        help='Inventory CSV filename.')
    parser.add_argument('--metadata_csv', type=str, default=DEFAULT_CONFIG['metadata_csv'],
                        help='Metadata CSV filename.')
    parser.add_argument('--ground_pct_thresholds', type=float, nargs='+',
                        default=DEFAULT_CONFIG['ground_pct_thresholds'],
                        help='List of ground point percent thresholds, e.g. 5 10 20 30')
    parser.add_argument('--high_ground_filter', type=float, default=DEFAULT_CONFIG['high_ground_filter'],
                        help='Fraction threshold for "high ground" tiles (e.g. 0.1 for 10%)')
    parser.add_argument('--no_plots', dest='do_plots', default=True, action='store_false',
                        help='Disable plots.')
    parser.add_argument('--no_image', dest='show_example_tile', default=True, action='store_false',
                        help='Disable fetching/displaying an ESRI tile.')
    parser.add_argument('--esri_px_width', type=int, default=DEFAULT_CONFIG['esri_px_width'],
                        help='Satellite image width (pixels)')
    parser.add_argument('--esri_px_height', type=int, default=DEFAULT_CONFIG['esri_px_height'],
                        help='Satellite image height (pixels)')

    args = parser.parse_args()

    main(
        data_dir=args.data_dir,
        inventory_csv=args.inventory_csv,
        metadata_csv=args.metadata_csv,
        ground_pct_thresholds=args.ground_pct_thresholds,
        high_ground_filter=args.high_ground_filter,
        do_plots=args.do_plots,
        show_example_tile=args.show_example_tile,
        esri_px_width=args.esri_px_width,
        esri_px_height=args.esri_px_height
    )