# main.py
"""
Purpose of script:
    - Process .laz tiles into DTM .geotif images, and process these DTM .geotif images into relief or hillshade visualisations.
    - Prejudice towards using pdal for .laz -> DTM processing and Relief Visualization Toolbox (`rvt_py`) for DTM -> visualizations.
Current status:
    - In development (fragile)
"""

# import top-level packages
import os
import sys
import json
import yaml

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import rasterio
from datetime import datetime

import earthaccess
import pdal
import rvt

# compute absolute path to the project root's src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# import project specific (src/project_utils/...) packages #
from project_utils import config as proj_config
from project_utils import io as proj_io
from project_utils import geo as proj_geo
from project_utils import lidar as proj_lidar
from project_utils import raster as proj_raster
from project_utils import satellite as proj_satellite
from project_utils import vis as proj_vis
from project_utils import scratch as proj_scratch

# --- CONSTANTS MOVED TO TOP ---
PATH_TO_CONFIG = "main/config.yml"
FILENAME_PIPELINE = "new_new_dtm.json"   # <--- MOVED TO TOP
# TILE_INDICES is now only used for selection demo, can be set as needed.

# scratch functions for testing
def test_setup(path_to_config):
    proj_scratch.test_imports()
    _ = proj_scratch.test_config(path_to_config)

def calculate_tile_centre(df, tile_index):
    row = df.iloc[tile_index]
    min_lat = row["min_lat"]
    max_lat = row["max_lat"]
    min_lon = row["min_lon"]
    max_lon = row["max_lon"]

    centre = ((min_lat + max_lat)/2, (min_lon + max_lon)/2)
    return centre

def print_time(msg=None, longform=False):
    t0 = datetime.now()
    if longform:
        formatted_time = t0.strftime("%Y:%m:%d %H:%M:%S")
    else:
        formatted_time = t0.strftime("%H:%M:%S")

    print(" ")
    if msg:
        print(f"{formatted_time}: {msg}")
    else:
        print(f"{formatted_time}")
    print("------------------------------")

if __name__ == "__main__":

    # --- CONSTANTS (already moved to top) ---
    print_time(msg="Setting up constants", longform=True)
    # PATH_TO_CONFIG = "main/config.yml"
    # FILENAME_PIPELINE = "new_dtm.json"

    # test setup
    test_setup(PATH_TO_CONFIG)

    # get config from config.yml
    config = proj_config.Config(PATH_TO_CONFIG)

    # authenticate
    proj_io.authenticate_earthaccess()

    # download dataset metadata and csv
    print_time(msg="Downloading dataset metadata and .csv")
    concept_id = config.get("dataset", "concept_id")
    # doi = config.get("dataset", "doi")
    path_to_csv_dir = config.get("paths", "dataset_csv")
    # metadata = earthaccess.search_datasets(doi=doi)[0]
    path_to_csv = proj_io.download_earthaccess_dataset_csv(
        concept_id,
        path_to_csv_dir,
        overwrite=False
    )

    # read dataset metadata csv into pandas dataframe
    df = pd.read_csv(path_to_csv)

    # --- CHANGED: Selecting indices for demo (replace as needed) ---
    TILE_INDICES = df.index[df["filename"] == "CAN_A01_2014_laz_5.laz"]
    TILE_INDICES = df.index[df["filename"] == "SAN_A02_2014_laz_0.laz"]

    for TILE_INDEX in TILE_INDICES:
        # fetch and view ESRI satellite image of .laz file area
        print_time(msg="fetching ESRI satellite image")
        laz_filename = df.iloc[TILE_INDEX]["filename"]
        path_to_laz = proj_io.fetch_laz_file(
            laz_filename,
            config.get("paths", "raw", "laz"),
            verbose=False,
            overwrite=False
        )
        img = proj_satellite.fetch_esri_from_row(
            df,
            laz_filename,
            save_path=os.path.join(
                config.get("paths", "raw", "sat"),
                laz_filename.split('.')[0] + '.png'
            )
        )

        # view satellite image
        tile_centre = calculate_tile_centre(df, TILE_INDEX)

        title = f"""ESRI Satellite image of
        {laz_filename}
        centre coord (lat, lon): {tile_centre[0]:.4f}, {tile_centre[1]:.4f}"""

        plt.figure(figsize=(6,6))
        plt.imshow(img)
        plt.title(title)
        plt.axis('off')
        plt.tight_layout(pad=0)
        plt.show(block=False)  # Required to actually display the image in a .py script
        print(f"tile_centre coord (lat, lon): {tile_centre[0]:.4f}, {tile_centre[1]:.4f}")

        # print laz classification point data
        print_time(msg="Getting counts of points of each classification")
        counts, total = proj_lidar.get_laz_classification_counts(path_to_laz)
        proj_lidar.print_laz_classification_counts(counts, total)

        # --- CHANGED: Save .tif image to the correct directory, with correct filename ---
        print_time(msg="Processing .laz to DTM")
        dtm_dir = config.get("paths", "processed", "dtm")
        os.makedirs(dtm_dir, exist_ok=True)  # Ensure output dir exists

        filename_laz = df.iloc[TILE_INDEX]["filename"]
        laz_base = os.path.splitext(filename_laz)[0]
        pipeline_base = os.path.splitext(FILENAME_PIPELINE)[0]
        filename_tif = f"{laz_base}_{pipeline_base}.tif"
        pipeline_def_fullpath = os.path.join(
            config.get("paths", "pdal_pipelines"),
            FILENAME_PIPELINE
        )
                       

        dtm_path = os.path.join(dtm_dir, filename_tif)

        # --- Call the DTM generation with the proper output filename ---
        created_tif = proj_lidar.laz_to_dtm(
            config,
            filename_laz,
            dtm_path,
            pipeline_def_fullpath,
            verbose=2        # Set 0 for silent, 1 for main events, 2 for full debug
        )
        # --- END CHANGE (you may need to adjust laz_to_dtm to pass dtm_path if the function expects FULL PATH) ---

        # --- REMOVED: temp variable, as it wasn't used anymore ---

        # --- Visualize the DTM ---
        print_time(msg="Showing DTM")
        # dtm_path was already constructed above, so use it here
        with rasterio.open(dtm_path) as src:
            arr = src.read(1)
            profile = src.profile

        # Example: mask anything outside plausible range
        arr_clean = np.where((arr > 0) & (arr < 1000), arr, np.nan)

        plt.figure(figsize=(8,6))
        im = plt.imshow(arr_clean, cmap='terrain')
        plt.colorbar(im, label='Elevation (meters)')
        plt.title("DTM from LAZ tile")
        plt.axis('off')
        plt.show()

        plt.figure(figsize=(8, 6))
        plt.hist(arr_clean.flatten(), bins=256)
        plt.title("Elevation Histogram")
        plt.xlabel("Elevation (meters)")
        plt.ylabel("Count")
        plt.show()

        with rasterio.open(created_tif) as src:
            print("Band count:", src.count)
            if src.count == 1:
                dem = src.read(1)
                print("Single-band DTM loaded! Min:", dem.min(), "Max:", dem.max())
            else:
                print("Still multiple bands: something is wrong.")