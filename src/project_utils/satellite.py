# src/lidar_utils/satellite.py

import pathlib
import requests
from PIL import Image
from io import BytesIO

def fetch_esri_from_row(df, filename, width=512, height=512, save_path=None):
    """
    Download ESRI satellite image for a tile defined in DataFrame row.
    """
    print(f"[satellite] Downloading ESRI image for {filename}...")
    row = df[df["filename"] == filename]
    if row.empty:
        raise ValueError(f"[satellite] No row for filename {filename}")
    min_lat = row["min_lat"].values[0]
    max_lat = row["max_lat"].values[0]
    min_lon = row["min_lon"].values[0]
    max_lon = row["max_lon"].values[0]
    bbox = (min_lon, min_lat, max_lon, max_lat)
    url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
    params = {
        "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "bboxSR": 4326,
        "imageSR": 4326,
        "size": f"{width},{height}",
        "format": "jpg",
        "f": "image"
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    img = Image.open(BytesIO(response.content))
    if save_path:
        save_path = pathlib.Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(save_path, format="JPEG")
        print(f"[satellite] Saved: {save_path}")
    return img