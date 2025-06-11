# src/lidar_utils/raster.py

import rasterio
import numpy as np
from matplotlib.colors import LightSource

def create_chm(dsm_path, dtm_path, chm_path, nodata=-9999., max_height=60.):
    """
    Calculate CHM = DSM-DTM, cap at max_height, write to GeoTIFF (float32).
    """
    print(f"[raster] Creating CHM from DSM:{dsm_path}, DTM:{dtm_path}")
    with rasterio.open(dsm_path) as dsm, rasterio.open(dtm_path) as dtm:
        arr = np.clip(
            dsm.read(1, masked=True) - dtm.read(1, masked=True), 0, max_height
        ).filled(nodata).astype("float32")
        profile = dsm.profile.copy()
        profile.update(dtype="float32", nodata=nodata)
        with rasterio.open(chm_path, "w", **profile) as dst:
            dst.write(arr, 1)
    print(f"[raster] CHM written: {chm_path}")

def hillshade(dtm_path, hill_path, azim=315, alt=45, exaggeration=1.2):
    """
    Generate and save hillshade image from DTM.
    """
    print(f"[raster] Hillshading {dtm_path} -> {hill_path}")
    with rasterio.open(dtm_path) as src:
        z = src.read(1, masked=True)
        dx, dy = src.res
        ls = LightSource(azdeg=azim, altdeg=alt)
        shaded = ls.hillshade(z, vert_exag=exaggeration, dx=dx, dy=dy)
        profile = src.profile.copy()
        profile.update(dtype="float32", count=1, nodata=None)
        with rasterio.open(hill_path, "w", **profile) as dst:
            dst.write(shaded.astype("float32"), 1)
    print(f"[raster] Hillshade written: {hill_path}")