# src/lidar_utils/satellite.py

import pathlib
import requests
import math
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

def fetch_esri_from_coords(coords, width=512, height=512):
    min_lat, max_lat, min_lon, max_lon = coords

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
    return img


def get_coords_from_df(df, filename):
    row = df[df["filename"] == filename]
    min_lat = row["min_lat"].values[0]
    max_lat = row["max_lat"].values[0]
    min_lon = row["min_lon"].values[0]
    max_lon = row["max_lon"].values[0]

    return min_lat, max_lat, min_lon, max_lon

def get_centre_coord(coords):
    min_lat, max_lat, min_lon, max_lon = coords
    centre_lat = (min_lat + max_lat) / 2
    centre_lon = (min_lon + max_lon) / 2

    return centre_lat, centre_lon

def get_bbox_sides_from_coords(coords):
    min_lat, max_lat, min_lon, max_lon = coords
    mean_lat = (min_lat + max_lat) / 2
    lat_deg_to_m = 111_320
    lon_deg_to_m = 111_320 * math.cos(math.radians(mean_lat))
    width_m = abs(max_lon - min_lon) * lon_deg_to_m
    height_m = abs(max_lat - min_lat) * lat_deg_to_m
    return width_m, height_m

def get_bbox_area_from_coords(coords):
    width_m, height_m = get_bbox_sides_from_coords(coords)
    return width_m * height_m