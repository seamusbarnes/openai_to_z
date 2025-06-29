#!/usr/bin/env python
# coding: utf-8

# In[58]:


import os
import sys
import json

import rasterio
import numpy as np
import matplotlib.pyplot as plt
import rvt
import pandas as pd
from time import sleep


# In[ ]:


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
from scratch import utils_scratch as proj_scratch

# auto-reload any module that changes on disk
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '')
# %reload_ext autoreload


# In[3]:


PATH_TO_CONFIG = "main/config.yml"

config = proj_config.Config(PATH_TO_CONFIG)


# In[5]:


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


# In[18]:


df = pd.read_csv(path_to_csv)
print(df.head(1))
print("\nMetadata dataframe columns")
print("--------------------")
for column in df.columns:
    print(column)


# In[70]:


index = 0
row = df.iloc[index]
filename_laz = row["filename"]

path_to_laz = proj_io.fetch_laz_file(
    filename_laz,
    config.get("paths", "raw", "laz"),
    verbose=False,
    overwrite=True
)


# In[ ]:


# print(f"Filename: {filename_laz}")
# counts, total = proj_lidar.get_laz_classification_counts(path_to_laz)
# proj_lidar.print_laz_classification_counts(counts, total)


# In[52]:


import geographiclib
from geographiclib.geodesic import Geodesic

def bbox_area_m2(min_lat, max_lat, min_lon, max_lon):
    poly = [
        (min_lat, min_lon),
        (min_lat, max_lon),
        (max_lat, max_lon),
        (max_lat, min_lon),
        (min_lat, min_lon),
    ]
    geod = Geodesic.WGS84
    g = geod.Polygon()
    for lat, lon in poly:
        g.AddPoint(lat, lon)
    num, perimeter, area = g.Compute()
    return abs(area)


# In[68]:


def get_metadata(
    path_to_laz, 
    tile_area_m2, 
    all_classes=range(0,20), 
    ground_class=2
):
    """
    Compute stats for a LAZ tile. Returns a dict with keys:
        - n_points_total
        - class_{i}_count, class_{i}_pct for i in all_classes
        - n_points_ground, ground_pct, ...
        - density_total, density_ground
        - z_min, z_max, z_mean, z_std (all points)
        - z_ground_min, z_ground_max, z_ground_mean, z_ground_std
        - intensity_min, intensity_max, intensity_mean, intensity_std
        - only_return_pct
        - scan_angle_min, scan_angle_max, scan_angle_mean, scan_angle_std
        - gps_time_min, gps_time_max
    """
    import laspy
    import numpy as np
    meta = {}
    with laspy.open(path_to_laz) as lfile:
        las = lfile.read()
        classifications = np.asarray(las.classification)
        n_total = len(classifications)
        meta['n_points_total'] = n_total

        # Class stats
        unique_classes, counts = np.unique(classifications, return_counts=True)
        class_count_dict = dict(zip(unique_classes, counts))
        for cls in all_classes:
            cnt = class_count_dict.get(cls, 0)
            meta[f'class_{cls}_count'] = int(cnt)
            meta[f'class_{cls}_pct'] = (float(cnt) / n_total) if n_total else 0.0

        meta['n_points_ground'] = meta[f'class_{ground_class}_count']
        meta['ground_pct'] = meta[f'class_{ground_class}_pct']
        for k, v in zip(
            ["unclassified", "veg_low", "veg_med", "veg_high"],
            [1, 3, 4, 5]
        ):
            meta[f'n_points_{k}'] = meta.get(f'class_{v}_count', 0)

        meta['tile_area_m2'] = tile_area_m2
        meta['density_total'] = n_total / tile_area_m2 if tile_area_m2 > 0 else np.nan
        meta['density_ground'] = meta['n_points_ground'] / tile_area_m2 if tile_area_m2 > 0 else np.nan

        z = np.asarray(las.z)
        meta['z_min'] = float(z.min())
        meta['z_max'] = float(z.max())
        meta['z_mean'] = float(z.mean())
        meta['z_std'] = float(z.std())

        ground_z = z[classifications == ground_class]
        if ground_z.size > 0:
            meta['z_ground_min'] = float(ground_z.min())
            meta['z_ground_max'] = float(ground_z.max())
            meta['z_ground_mean'] = float(ground_z.mean())
            meta['z_ground_std'] = float(ground_z.std())
        else:
            for f in ['z_ground_min','z_ground_max','z_ground_mean','z_ground_std']:
                meta[f] = np.nan

        # Intensity
        inten = getattr(las, "intensity", None)
        if inten is not None:
            inten = np.asarray(inten)
            meta['intensity_min'] = float(inten.min())
            meta['intensity_max'] = float(inten.max())
            meta['intensity_mean'] = float(inten.mean())
            meta['intensity_std'] = float(inten.std())
        else:
            for f in ['intensity_min', 'intensity_max', 'intensity_mean', 'intensity_std']:
                meta[f] = np.nan

        # Only-return
        try:
            return_number = np.asarray(las.return_number)
            num_returns = np.asarray(las.number_of_returns)
            only_return = (return_number == num_returns)
            meta['only_return_pct'] = only_return.sum() / n_total if n_total else 0
        except Exception:
            meta['only_return_pct'] = np.nan

        # Scan angle
        scan = getattr(las, 'scan_angle', None)
        if scan is not None:
            scan = np.asarray(scan)
            meta['scan_angle_min'] = float(scan.min())
            meta['scan_angle_max'] = float(scan.max())
            meta['scan_angle_mean'] = float(scan.mean())
            meta['scan_angle_std'] = float(scan.std())
        else:
            for f in ['scan_angle_min','scan_angle_max','scan_angle_mean','scan_angle_std']:
                meta[f] = np.nan

        gps = getattr(las, 'gps_time', None)
        if gps is not None:
            gps = np.asarray(gps)
            meta['gps_time_min'] = float(gps.min())
            meta['gps_time_max'] = float(gps.max())
        else:
            meta['gps_time_min'] = meta['gps_time_max'] = np.nan

    return meta


# In[71]:


area_m2 = bbox_area_m2(row['min_lat'], row['max_lat'], row['min_lon'], row['max_lon'])
meta = get_metadata(path_to_laz, tile_area_m2=area_m2)
print(type(meta))


# In[75]:


results = []
output_csv = "temp.csv"
if os.path.isfile(output_csv):
    os.remove(output_csv)
count = 0
for idx, row in df.iterrows():
    try:
        filename_laz = row["filename"]
        laz_dir = config.get("paths", "raw", "laz")
        print(f"Downloading {filename_laz} into directory {laz_dir}")

        path_to_laz = proj_io.fetch_laz_file(
            filename_laz,      # the filename onl
            laz_dir,           # the target directory only
            verbose=False,
            overwrite=True
        )
        area_m2 = bbox_area_m2(row['min_lat'], row['max_lat'], row['min_lon'], row['max_lon'])
        meta = get_metadata(path_to_laz, tile_area_m2=area_m2)

        row_out = row.to_dict()

        # Merge all meta data
        row_out.update(meta)
        results.append(row_out)

        os.remove(path_to_laz)  # Enable when ready

    except Exception as e:
        print(f"Failed for {filename_laz}: {e}")
        continue

    # Optional: Sleep
    sleep(0.1)

    # Save progress often
    if (idx+1) % 10 == 0 or (idx+1) == len(df):
        pd.DataFrame(results).to_csv(output_csv, index=False)
        print(f"Progress saved at {idx+1}/{len(df)} files.")
    count += 1

# Final save
pd.DataFrame(results).to_csv(output_csv, index=False)
print("DONE and saved to", output_csv)


# In[ ]:




