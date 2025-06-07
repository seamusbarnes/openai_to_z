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

#
def test_setup(path_to_config):
    proj_scratch.test_imports()
    _ = proj_scratch.test_config(path_to_config)

if __name__ == "__main__":

    path_to_config = "main/config.yml"

    # test setup
    test_setup(path_to_config)

    # get config from config.yml
    config = proj_config.Config(path_to_config)

    # authenticate
    proj_io.authenticate_earthaccess()

    # download dataset metadata and csv
    concept_id = config.get("dataset", "concept_id")
    # doi = config.get("dataset", "doi")
    path_to_csv_dir = config.get("paths", "dataset_csv")

    # metadata = earthaccess.search_datasets(doi=doi)[0]

    path_to_csv = proj_io.download_earthaccess_dataset_csv(
        concept_id,
        path_to_csv_dir,
        overwrite=False
    )

    index = 28
    df = pd.read_csv(path_to_csv)

    laz_filename = df.iloc[index]["filename"]

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

    min_lat = float(df.iloc[index]["min_lat"])
    max_lat = float(df.iloc[index]["max_lat"])
    min_lon = float(df.iloc[index]["min_lon"])
    max_lon = float(df.iloc[index]["max_lon"])

    centre = ((min_lat + max_lat)/2, (min_lon + max_lon)/2)

    title = f"""ESRI Satellite image of
    {laz_filename}
    centre coord (lat, lon): {centre[0]:.4f}, {centre[1]:.4f}"""

    plt.imshow(img)
    plt.title(title)
    plt.axis('off')
    plt.tight_layout(pad=0)
    plt.show()  # Required to actually display the image in a .py script
    print(f"centre coord (lat, lon): {centre[0]:.4f}, {centre[1]:.4f}")