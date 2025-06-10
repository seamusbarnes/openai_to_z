#!/usr/bin/env python
# coding: utf-8

# - **purpose**: 1. Determine what percentage of the tiles in the dataset has have what percentage of ground classified points. 2. Show ESRI satellite data images of tiles with the highest percentage of ground classified points.
# 
# - **status**: Working. Getting ESRI satellite images (with `satellite.fetch_esri_from_XXX()`) is brittle and returns server error 500 for small tiles (minimum tile width determined by location, but >250 m is usually safe).
# 
# - **next**: None
# 
# - **conclusion**: Percent of tiles with ground point % > 5% (10%): 0.14% (0.06%) (425 counts (180 counts))

# In[63]:


import os
import pandas as pd
import numpy as np
import sys
import requests

from PIL import Image
from io import BytesIO
import pathlib

# compute absolute path to the project root's src/
sys.path.insert(0, os.path.join(os.getcwd(), "src"))

# import project specific (src/project_utils/...) packages #
from project_utils import config as proj_config
from project_utils import io as proj_io
from project_utils import geo as proj_geo
from project_utils import lidar as proj_lidar
from project_utils import raster as proj_raster
from project_utils import satellite as proj_satellite
from project_utils import vis as proj_vis
from project_utils import scratch as proj_scratch

# auto-reload any module that changes on disk
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '')
# %reload_ext autoreload


# In[8]:


inventory_name = "cms_brazil_lidar_tile_inventory.csv"
metadata_name = "cms_brazil_lidar_tile_metadata.csv"

def get_path_to_data(filename):
    path_to_file = os.path.join(
        os.getcwd(),
        "data",
        "metadata",
        filename
    )
    return path_to_file

path_to_inv = get_path_to_data(inventory_name)
path_to_meta =  get_path_to_data(metadata_name)


# In[23]:


df_inv = pd.read_csv(path_to_inv)
df_meta = pd.read_csv(path_to_meta)

print(f"Length of inventory: {len(df_inv)}")
print(f"Length of metadata: {len(df_meta)}")
print("")

print(f"Inventory columns: {df_inv.columns}")
print(f"Metadata columns: {df_meta.columns}")
print("")

print(f"Filename of row 0 entry for inventory: {df_inv.iloc[0]['filename']}")
print(f"Filename of row 0 entry for metadata: {df_meta.iloc[0]['filename']}")


# In[25]:


import matplotlib.pyplot as plt

plt.hist((df_meta['ground_pct']*100).dropna(), bins=30)
plt.xlabel('Ground Point Percentage')
plt.ylabel('Number of Tiles')
plt.title('Distribution of % Ground Points per Tile')
plt.show()


# In[27]:


# Drop NaN values for safety
ground_pcts = (df_meta['ground_pct']*100).dropna()

# Sort values
sorted_pcts = np.sort(ground_pcts)

# Compute cumulative sum (in terms of counts or percentages)
cum_counts = np.arange(1, len(sorted_pcts) + 1)
cum_frac = cum_counts / len(sorted_pcts)

plt.figure(figsize=(8, 5))
plt.step(sorted_pcts, cum_frac, where='post')
plt.xlabel('Ground Points Percentage')
plt.ylabel('Cumulative Fraction of Tiles')
plt.title('Cumulative Distribution of % Ground Points per Tile')
plt.grid(True)
plt.show()


# In[112]:


for thresh in [5, 10, 20, 30]:
    pct_above = np.mean(sorted_pcts > thresh)
    count_above = np.sum(sorted_pcts > thresh)
    print(f"Percent of tiles with ground point % > {thresh}%: {pct_above:.2f} % ({count_above} counts)")


# In[58]:


selected = df_meta[df_meta['ground_pct'] > 0.1]

# Step 2: Print info for first 5 such tiles (modify as needed)
filename = "CAN_A01_2014_laz_5.laz"
row = df_meta[df_meta["filename"] == filename]
min_lat = row['min_lat']
max_lat = row['max_lat']
min_lon = row['min_lon']
max_lon = row['max_lon']
tile_area_km2 = row['tile_area_m2']*1e-6
ground_pct = row['ground_pct']
print(f"Filename: {filename}")
# print(f"Bounding box: min_lat={min_lat}, max_lat={max_lat}, min_lon={min_lon}, max_lon={max_lon}, ground percentage={ground_pct*100:.2f}, tile area (m**2): {tile_area_km2:.2f}")
print("-" * 40)

# (Optional) Fetch and display/save the ESRI satellite image

img = proj_satellite.fetch_esri_from_row(df_meta, filename)
img.show()  # or save with save_path="path/to/save.jpg"


# In[59]:


filename


# In[109]:


filename = selected.iloc[5]["filename"]
deg_dif = 0.00

coords = proj_satellite.get_coords_from_df(selected, filename)
min_lat, max_lat, min_lon, max_lon = coords
min_lat -= deg_dif
max_lat += deg_dif
min_lon -= deg_dif
max_lon += deg_dif
coords = min_lat, max_lat, min_lon, max_lon

width_m, height_m = proj_satellite.get_bbox_sides_from_coords(coords)
area = proj_satellite.get_bbox_area_from_coords(coords)

print(filename)
print(f"Dimensions (w x h): {width_m:.0f} x {height_m:.0f}")
print(f"Area: {area*1e-6:.2f} km**2")

px_width=512
px_height=512

url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
params = {
    "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
    "bboxSR": 4326,
    "imageSR": 4326,
    "size": f"{px_width},{px_height}",
    "format": "jpg",
    "f": "image"
}
response = requests.get(url, params=params)
response.raise_for_status()
img = Image.open(BytesIO(response.content))

plt.figure(figsize=(5,5))
plt.imshow(img)
plt.title(filename)


# In[ ]:




