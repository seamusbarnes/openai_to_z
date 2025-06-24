import os
import rasterio
import numpy as np
import matplotlib.pyplot as plt
import argparse
import glob

# Specify the directory containing your images
DATA_DIR = 'data/processed/dtm'

def hillshade(array, azimuth, angle_altitude):
    """Returns hillshade image from elevation array."""
    azimuth = 360.0 - azimuth
    x, y = np.gradient(array)
    slope = np.pi / 2. - np.arctan(np.sqrt(x * x + y * y))
    aspect = np.arctan2(-x, y)
    azm_rad = azimuth * np.pi / 180.
    alt_rad = angle_altitude * np.pi / 180.
    shaded = (
        np.sin(alt_rad) * np.sin(slope) +
        np.cos(alt_rad) * np.cos(slope) *
        np.cos((azm_rad - np.pi / 2.) - aspect)
    )
    result = 255 * (shaded + 1) / 2
    return np.clip(result, 0, 255)

def plot_dtm_and_hillshade(dem, hs, vmin, vmax, title):
    plt.figure(figsize=(10, 10))
    plt.imshow(dem, cmap='terrain', vmin=vmin, vmax=vmax)
    plt.title(f"DTM: {title}")
    plt.colorbar(fraction=0.04, pad=0.02)
    plt.show()

    plt.figure(figsize=(10, 10))
    plt.imshow(hs, cmap='gray')
    plt.title(f"Hillshade: {title}")
    plt.show()

def process_dtm_tile_array(dtm_path):
    title = os.path.split(dtm_path)[-1]
    with rasterio.open(dtm_path) as src:
        dem = src.read(1)
        nodata = src.nodata
        dem = np.where((dem == nodata) | (dem < -100) | (dem > 9999), np.nan, dem)
        vmin = np.nanpercentile(dem, 1)
        vmax = np.nanpercentile(dem, 99)
        dem_filled = np.nan_to_num(dem, nan=np.nanmean(dem))
        hs = hillshade(dem_filled, azimuth=315, angle_altitude=45)
        plot_dtm_and_hillshade(dem, hs, vmin, vmax, title)
    return dem, hs

def find_most_recent_tif(data_dir):
    # Match both .tif and .tiff files (case-insensitive)
    pattern1 = os.path.join(data_dir, '*.tif')
    pattern2 = os.path.join(data_dir, '*.tiff')
    files = glob.glob(pattern1) + glob.glob(pattern2)
    if not files:
        raise FileNotFoundError(f"No '.tif' or '.tiff' files found in {data_dir}")
    most_recent = max(files, key=os.path.getmtime)
    return most_recent

def main():
    parser = argparse.ArgumentParser(
        description="Plot DTM and hillshade from a GeoTIFF. If --file is not given, defaults to the most recently saved image in DATA_DIR: '{}'.".format(DATA_DIR)
    )
    parser.add_argument(
        '--file',
        type=str,
        help=f"Path to a GeoTIFF file. If omitted, will use the most recently modified *.tif or *.tiff in DATA_DIR ({DATA_DIR})"
    )
    args = parser.parse_args()

    if args.file:
        path_to_file = args.file
        if not os.path.isfile(path_to_file):
            parser.error(f"File not found: {path_to_file}")
    else:
        path_to_file = find_most_recent_tif(DATA_DIR)
        print(f"No file specified. Using most recent file: {path_to_file}")

    print(f"Processing: {path_to_file}")
    dem, hs = process_dtm_tile_array(path_to_file)

if __name__ == "__main__":
    main()