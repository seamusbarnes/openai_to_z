from pathlib import Path
from typing import Optional, Tuple, Union
import pandas as pd
from PIL import Image, UnidentifiedImageError
from io import BytesIO
import requests
import matplotlib.pyplot as plt

def fetch_esri_from_coords(
    coords: Tuple[float, float, float, float],
    width: int = 512,
    height: int = 512,
    save_path: Optional[Union[str, Path]] = None,
    timeout: Tuple[int, int] = (5, 30),
    overwrite: bool = False
) -> Optional[Image.Image]:
    min_lat, max_lat, min_lon, max_lon = coords

    if save_path is not None:
        save_path = Path(save_path)
        if save_path.exists() and not overwrite:
            print(f"[satellite] Image already exists at {save_path}, skipping download.")
            try:
                return Image.open(save_path)
            except Exception as e:
                print(f"[satellite] Error opening existing image: {e}")
                # continue to fetch if loading fails

    url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
    params = {
        "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
        "bboxSR": 4326,
        "imageSR": 4326,
        "size": f"{width},{height}",
        "format": "jpg",
        "f": "image"
    }
    try:
        response = requests.get(url, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        print(f"[satellite] Timeout fetching ESRI image for coords {coords}.")
        return None
    except requests.RequestException as e:
        print(f"[satellite] Error fetching ESRI image: {e}")
        return None

    try:
        img = Image.open(BytesIO(response.content))
    except UnidentifiedImageError as e:
        print(f"[satellite] Unable to decode ESRI image for {coords}: {e}")
        return None
    
    if save_path is not None:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            img.save(save_path, format="JPEG")
            print(f"[satellite] Saved: {save_path}")
        except Exception as e:
            print(f"[satellite] Error saving image: {e}")
    return img

def fetch_esri_from_row(
    df: pd.DataFrame, 
    filename: str,
    width: int = 512, 
    height: int = 512, 
    save_path: Optional[Union[str, Path]] = None,
    timeout: Tuple[int, int] = (5, 30),
    overwrite: bool = False
) -> Optional[Image.Image]:
    """
    Download ESRI satellite image using bounding box found in a row of the DataFrame.

    Args:
        df: DataFrame with tile metadata.
        filename: The row with this filename is used to get bounds.
        (rest: see fetch_esri_from_coords)

    Returns:
        PIL Image on success, None on failure.
    """
    row = df[df["filename"] == filename]
    if row.empty:
        print(f"[satellite] No row for filename {filename}")
        return None
    min_lat, max_lat, min_lon, max_lon = get_coords_from_row(row)

    # Just delegate
    return fetch_esri_from_coords(
        (min_lat, max_lat, min_lon, max_lon),
        width=width,
        height=height,
        save_path=save_path,
        timeout=timeout,
        overwrite=overwrite
    )

def get_coords_from_row(
        row: pd.DataFrame
) -> Tuple:
    min_lat = float(row["min_lat"])
    max_lat = float(row["max_lat"])
    min_lon = float(row["min_lon"])
    max_lon = float(row["max_lon"])

    return (min_lat, max_lat, min_lon, max_lon)


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

def show_sat_image(df, filename, save_path=None, overwrite=False):
    coords = get_coords_from_df(df, filename)

    img = fetch_esri_from_coords(coords, save_path=save_path, overwrite=overwrite)
    plt.figure(figsize=(6, 6))
    plt.imshow(img)
    plt.title(filename)
    plt.show()