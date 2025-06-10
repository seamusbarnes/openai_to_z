#!/usr/bin/env python
# coding: utf-8

# In[7]:


import os
import sys
import json

import rasterio
import numpy as np
import matplotlib.pyplot as plt
import rvt
import pandas as pd


# In[2]:


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


# In[20]:


index = 0
row = df.iloc[index]
filename_laz = row["filename"]

path_to_laz = proj_io.fetch_laz_file(
    filename_laz,
    config.get("paths", "raw", "laz"),
    verbose=False,
    overwrite=True
)


# In[45]:


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


# In[46]:


area_m2 = bbox_area_m2(row['min_lat'], row['max_lat'], row['min_lon'], row['max_lon'])
meta = get_metadata(path_to_laz, tile_area_m2=area_m2)


# In[47]:


meta


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:


def get_metadata(path_to_laz, tile_area_m2, all_classes=range(0,20)):
    import laspy
    import numpy as np
    meta = {}
    with laspy.open(path_to_laz) as lfile:
        las = lfile.read()
        classifications = np.asarray(las.classification)
        n_total = len(classifications)
        meta['n_points_total'] = n_total

        # Class counts for all possible (0–19)
        unique_classes, counts = np.unique(classifications, return_counts=True)
        class_count_dict = dict(zip(unique_classes, counts))

        for cls in all_classes:
            cnt = class_count_dict.get(cls, 0)
            meta[f'class_{cls}_count'] = int(cnt)
            meta[f'class_{cls}_pct'] = (float(cnt) / n_total) if n_total else 0.0

        # Main expected classes (for easier filtering downstream)
        meta['n_points_ground'] = meta['class_2_count']
        meta['ground_pct'] = meta['class_2_pct']
        meta['n_points_unclassified'] = meta['class_1_count']
        meta['n_points_veg_low'] = meta['class_3_count']
        meta['n_points_veg_med'] = meta['class_4_count']
        meta['n_points_veg_high'] = meta['class_5_count']

        # Area
        meta['tile_area_m2'] = tile_area_m2

        # Density
        meta['density_total'] = n_total / tile_area_m2
        meta['density_ground'] = meta['n_points_ground'] / tile_area_m2

        # Elevation stats (all points)
        z = np.asarray(las.z)
        meta['z_min'] = float(z.min())
        meta['z_max'] = float(z.max())
        meta['z_mean'] = float(z.mean())
        meta['z_std'] = float(z.std())

        # Elevation stats (ground only)
        ground_z = z[classifications == 2]
        if ground_z.size > 0:
            meta['z_ground_min'] = float(ground_z.min())
            meta['z_ground_max'] = float(ground_z.max())
            meta['z_ground_mean'] = float(ground_z.mean())
            meta['z_ground_std'] = float(ground_z.std())
        else:
            for field in ['z_ground_min','z_ground_max','z_ground_mean','z_ground_std']:
                meta[field] = np.nan

        # Intensity stats (all points)
        if hasattr(las, "intensity"):
            inten = np.asarray(las.intensity)
            meta['intensity_min'] = float(inten.min())
            meta['intensity_max'] = float(inten.max())
            meta['intensity_mean'] = float(inten.mean())
            meta['intensity_std'] = float(inten.std())
        else:
            meta['intensity_min'] = meta['intensity_max'] = meta['intensity_mean'] = meta['intensity_std'] = np.nan

        # Only return stats: Only those with return_number == number_of_returns
        return_number = np.asarray(las.return_number)
        num_returns = np.asarray(las.number_of_returns)
        only_return = (return_number == num_returns)
        meta['only_return_pct'] = only_return.sum() / n_total if n_total else 0

        # Scan angle stats
        if hasattr(las, "scan_angle"):
            scan_angle = np.asarray(las.scan_angle)
            meta['scan_angle_min'] = float(scan_angle.min())
            meta['scan_angle_max'] = float(scan_angle.max())
            meta['scan_angle_mean'] = float(scan_angle.mean())
            meta['scan_angle_std'] = float(scan_angle.std())
        else:
            meta['scan_angle_min'] = meta['scan_angle_max'] = meta['scan_angle_mean'] = meta['scan_angle_std'] = np.nan

        # Optionally, GPS time bounds
        if hasattr(las, "gps_time"):
            gps_time = np.asarray(las.gps_time)
            meta['gps_time_min'] = float(gps_time.min())
            meta['gps_time_max'] = float(gps_time.max())
        else:
            meta['gps_time_min'] = meta['gps_time_max'] = np.nan

    return meta


# In[21]:


print(f"Filename: {filename_laz}")
counts, total = proj_lidar.get_laz_classification_counts(path_to_laz)
proj_lidar.print_laz_classification_counts(counts, total)


# In[35]:


meta = get_metadata(path_to_laz)
print(pd.Series(meta))


# In[43]:


for key in sorted(meta.keys()):
    print(f"{key:<15}: {meta[key]}")


# In[ ]:




