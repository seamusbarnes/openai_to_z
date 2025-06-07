# src/lidar_utils/vis.py

import matplotlib.pyplot as plt
import rasterio
from rasterio.plot import show

def plot_products(sat_jpg, dsm_path, dtm_path, chm_path, hill_path, overlay="hillshade", overlay_alpha=0.3, title=""):
    """
    Plot 2x2 grid of: Satellite, DSM, DTM, CHM (optionally overlay hillshade).
    """
    print("[vis] Generating quick-look plot...")
    fig, axs = plt.subplots(2, 2, figsize=(10, 10))
    axs = axs.ravel()
    # Satellite
    with rasterio.open(sat_jpg) as src:
        arr = src.read()
        show(arr, transform=src.transform, ax=axs[0], title="Satellite")
    # DSM (+hill)
    with rasterio.open(dsm_path) as src:
        dsm = src.read(1)
        show(dsm, transform=src.transform, ax=axs[1], title="DSM", cmap="viridis")
    if overlay == "hillshade":
        with rasterio.open(hill_path) as hs:
            axs[1].imshow(hs.read(1), cmap="gray", alpha=overlay_alpha)
    # DTM
    with rasterio.open(dtm_path) as src:
        show(src.read(1), transform=src.transform, ax=axs[2], title="DTM", cmap="terrain")
    # CHM
    with rasterio.open(chm_path) as src:
        show(src.read(1), transform=src.transform, ax=axs[3], title="CHM", cmap="viridis")
    for ax in axs:
        ax.axis("off")
    fig.suptitle(title, fontsize=16)
    plt.tight_layout()
    plt.show()