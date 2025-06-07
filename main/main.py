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
    # print(formatted_time)
    print(" ")
    if msg:
        print(f"{formatted_time}: {msg}")
    else:
        print(f"{formatted_time}")
    print("------------------------------")

if __name__ == "__main__":

    # setup constants
    print_time(msg="Setting up constants", longform=True)
    PATH_TO_CONFIG = "main/config.yml"
    TILE_INDEX = 28
    FILENAME_PIPELINE = "new_dtm.json"

    # test setup
    test_setup(PATH_TO_CONFIG)

    # get config from config.yml
    config = proj_config.Config(PATH_TO_CONFIG)

    # authenticate)
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

    # process .laz to DTM with pdal
    print_time(msg="Processing .laz to DTM")
    os.makedirs(config.get("paths", "processed", "dtm"), exist_ok=True)

    filename_laz = df.iloc[TILE_INDEX]["filename"]
    filename_tif = ((df.iloc[TILE_INDEX]["filename"]).split(".")[0] +
                    "_" +
                    FILENAME_PIPELINE.split(".")[0] +
                    ".tif"
    )
    FILENAME_PIPELINE = "new_dtm.json"

    temp = proj_lidar.laz_to_dtm(
        config,
        filename_laz,
        filename_tif,
        FILENAME_PIPELINE
    )

    # showing DTM (cleaned to remove anomalous points
    print_time(msg="Showing DTM")
    dtm_path = os.path.join(
        config.get("paths", "processed", "dtm"),
        filename_tif
        )
    
    with rasterio.open(dtm_path) as src:
        arr = src.read(1)
        profile = src.profile

    # Example: mask anything outside plausible range
    arr_clean = np.where((arr > 0) & (arr < 1000), arr, np.nan)

    # with rasterio.open(dtm_path) as src:
    #     arr = src.read(1)  # Read the first band
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