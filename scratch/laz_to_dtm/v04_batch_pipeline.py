#!/usr/bin/env python
# coding: utf-8

# In[2]:


SRC


# In[3]:


# v04_batch_pipeline.py
"""
Batch LiDAR Processing Pipeline (v04)
-------------------------------------
- Modular, well-documented, step-by-step.
- Uses helpers from `src/lidar_utils/` for I/O and processing.
"""
import pathlib
import pandas as pd
import logging
import sys
import os

# Make sure lidar_utils is on sys.path (fine for notebook/dev flows)
SRC = os.path.join(
    os.getcwd(),
    "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from project_utils import io as utils_io
from project_utils import satellite
from project_utils import lidar
from project_utils import raster

# auto-reload any module that changes on disk
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


# In[19]:


# --- Load paths and configs ---
print("Loading config paths from YAML...")
paths = utils_io.load_paths_yaml("config/paths.yml", verbose=True)

# --- Authenticate with earthaccess ---
print("Authenticating earthaccess (will prompt if needed)...")
utils_io.authenticate_earthaccess()


# In[5]:


# --- Get dataset metadata and download CSV (granule listing) ---
print("\nQuerying dataset metadata and CSV from NASA/ORNL DAAC...")
metadata = utils_io.get_metadata()
concept_id = metadata["meta"]["concept-id"]

csv_path = utils_io.download_earthaccess_dataset_csv(concept_id, dest=paths["raw_meta"], overwrite=False)
print(f"Metadata CSV saved: {csv_path}")

# --- Load into DataFrame and preview ---
df = pd.read_csv(csv_path)
print(f"\nLoaded {len(df)} LiDAR tile entries.")
display(df.head(2))


# In[81]:


import pdal
import json

filename = "data/raw/tiles/laz/ANA_A01_2017_laz_0.laz"

pipeline = pdal.Pipeline(f"""
[
    {{
        "type": "readers.las",
        "filename": "{filename}"
    }}
]
""")

pipeline.execute()
metadata = pipeline.metadata

classification_counts = metadata['metadata']['readers.las']['dimensions']['Classification']['counts']
total_points = sum(classification_counts.values())

print("Classification\tCount\tPercentage")
for class_id, count in sorted(classification_counts.items(), key=lambda x: int(x[0])):
    percentage = (count / total_points) * 100
    print(f"{class_id}\t\t{count}\t{percentage:.2f}%")


# In[ ]:


import pdal
print(f"pdal.__file__: {pdal.__file__}")
print(f"pdal.__version__: {pdal.__version__}")
print(dir(pdal.Pipeline))


# In[23]:


# --- Load your PDAL DTM/DSM pipeline templates (JSON, can be small .json files you prepared) ---
print("Loading PDAL pipeline templates...")
pipeline_dir = paths["pdal_tpl_dir"]
pipeline_defs = {
    "dtm": pipeline_dir / "dtm_pipeline.json",
    "dsm": pipeline_dir / "dsm_pipeline.json",
}
for k, v in pipeline_defs.items():
    print(f"  {k.upper()} pipeline: {v}")


# In[26]:


print("Pipeline dir:", pipeline_dir)
print("DTM template exists:", (pipeline_dir / "dtm_pipeline.json").exists())


# In[24]:


def process_tile(row, pipeline_defs, paths, df):
    """
    Run the full workflow for a single LiDAR tile.
    """
    filename = row["filename"]
    print(f"\n--- Processing tile: {filename} ---")

    # 1. Download LAZ if needed
    laz_path = utils_io.fetch_laz_file(filename, paths["raw_laz"], verbose=True)
    print(f"LAZ file on disk: {laz_path}")

    # 2. Compute spatial bounds for output rasters
    bounds = lidar.tile_bounds(laz_path, res=2.0)
    min_x, max_x, min_y, max_y = bounds
    print(f"Tile bounds: X=({min_x}, {max_x})  Y=({min_y}, {max_y})")

    # 3. Output file locations
    stem = pathlib.Path(filename).stem
    dtm_path  = paths["dtm_dir"]  / f"{stem}_dtm.tif"
    dsm_path  = paths["dsm_dir"]  / f"{stem}_dsm.tif"
    chm_path  = paths["chm_dir"]  / f"{stem}_chm.tif"
    hill_path = paths["hill_dir"] / f"{stem}_hill.tif"
    sat_file  = paths["raw_sat"]  / f"{stem}.jpg"

    print(f"Plan to write: \n  DTM={dtm_path}\n  DSM={dsm_path}\n  CHM={chm_path}\n  Hillshade={hill_path}\n  SAT={sat_file}")

    # 4. Build/run DTM PDAL pipeline
    print("Building and running DTM pipeline...")
    dtm_tpl = lidar.load_template(pipeline_defs["dtm"])
    dtm_pipe = lidar.build_pipeline(dtm_tpl, in_laz=laz_path, out_tif=dtm_path)
    lidar.run_pipeline(dtm_pipe)
    print(f"DTM written: {dtm_path}")

    # 5. Build/run DSM PDAL pipeline
    print("Building and running DSM pipeline...")
    dsm_tpl = lidar.load_template(pipeline_defs["dsm"])
    dsm_pipe = lidar.build_pipeline(dsm_tpl, in_laz=laz_path, out_tif=dsm_path)
    lidar.run_pipeline(dsm_pipe)
    print(f"DSM written: {dsm_path}")

    # 6. Generate CHM, Hillshade
    print("Calculating CHM and hillshade products...")
    raster.create_chm(dsm_path, dtm_path, chm_path)
    raster.hillshade(dtm_path, hill_path)
    print(f"CHM, hillshade complete.")

    # 7. Download satellite image for tile bounds
    print("Fetching satellite image for tile...")
    satellite.fetch_esri_from_row(df, filename, save_path=sat_file)
    print(f"Satellite image saved: {sat_file}")

    return {
        "dtm": dtm_path,
        "dsm": dsm_path,
        "chm": chm_path,
        "hill": hill_path,
        "sat": sat_file
    }


# In[ ]:


# Process N tiles for demo; set NUM_TILES = None to run over *all*
NUM_TILES = 2  # for dev/test: set to None to do all tiles

for count, (_, row) in enumerate(df.iterrows()):
    if NUM_TILES and count >= NUM_TILES:
        break
    out = process_tile(row, pipeline_defs, paths, df)
    print(f"\nResult paths for {row['filename']}:\n{out}")


# In[40]:


# Process N tiles for demo; set NUM_TILES = None to run over *all*
TILE_INDEX = 27
row = df.iloc[TILE_INDEX]
out = process_tile(row, pipeline_defs, paths, df)
print(f"\nResult paths for {row['filename']}:\n{out}")


# In[41]:


from project_utils import vis

# Visualize the last processed tile
print("\nVisualizing results of last processed tile...")
vis.plot_products(
    sat_jpg=out["sat"],
    dsm_path=out["dsm"],
    dtm_path=out["dtm"],
    chm_path=out["chm"],
    hill_path=out["hill"],
    overlay="hillshade",
    title=f"Quick-look: {row['filename']}"
)


# In[43]:


import rasterio
import matplotlib.pyplot as plt

temp_files_chm = os.listdir(os.path.join(
    os.getcwd(),
    "data",
    "derived",
    "hillshade"))
print(temp_files_chm)


# In[54]:


fig = plt.figure(figsize=(5,5))
plt.hist(arr, bins=30)
plt.show()


# In[71]:


import numpy as np
data = arr
Q1 = np.percentile(data, 0.05)
Q3 = np.percentile(data, 0.95)
IQR = Q3 - Q1

# Define bounds for anomaly detection
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# Filter out anomalies
cleaned_arr = np.where(
    (arr < lower_bound) | (arr > upper_bound),
    np.nan,
    arr
)


# In[72]:


plt.imshow(cleaned_arr, cmap='viridis')
plt.title('Hillshade')
plt.colorbar(label='Height (m)')
plt.axis('off')
plt.show()


# In[ ]:


temp_path = os.path.join(
    os.getcwd(),
    "data",
    "derived",
    "hillshade",
    temp_files_chm[3]
)
with rasterio.open(temp_path) as src:
    arr = src.read(1)
    plt.figure(figsize=(8,6))
    plt.imshow(arr, cmap='viridis')
    plt.title('Hillshade')
    plt.colorbar(label='Height (m)')
    plt.axis('off')
    plt.show()

