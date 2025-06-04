import os
import io
from io import BytesIO
from datetime import datetime
import math

import earthaccess
import pandas as pd

import folium

from IPython.display import Image, display
import IPython.display
import IPython

import requests

# from PIL import Image, ImageDraw
import PIL.Image as PILImage
import IPython.display as ipd
from PIL import ImageDraw

class Tile:
    def __init__(self, row, index=None):
        self._extract_metadata(row)

        self.index = index

    def _extract_metadata(self, row):
        self.tile_name = row["filename"]
        self.mid_lat = float((row["min_lat"] + row["max_lat"])/2)
        self.mid_lon = float((row["min_lon"] + row["max_lon"])/2)

        self.min_lat = float(row["min_lat"])
        self.max_lat = float(row["max_lat"])

        self.min_lon = float(row["min_lon"])
        self.max_lon = float(row["max_lon"])

        self._calculate_tile_dimensions(
            self.mid_lat,
            self.min_lat,
            self.max_lat,
            self.min_lon,
            self.max_lon
        )

        self.area = (self.width * self.height) * 10**-6

    def _calculate_tile_dimensions(self, mid_lat, min_lat, max_lat, min_lon, max_lon):
        metres_per_deg_lat = 111320
        metres_per_deg_lon = 111320 * math.cos(math.radians(mid_lat))

        self.width = abs(min_lat - max_lat) * metres_per_deg_lat
        self.height = abs(min_lon - max_lon) * metres_per_deg_lon

    def fetch_satellite_image_interactive(self, buffer=0.5):
        m = folium.Map(
            locationself = [self.mid_lat, self.mid_lon],
            zoom_start=17,
            tiles="Esri.WorldImagery"
        )

        bounds = (
            [self.min_lat, self.min_lon],
            [self.max_lat, self.max_lon]
        )

        m.fit_bounds(bounds)

        folium.Rectangle(
            bounds=bounds,
            color="red",
            fill=False
        ).add_to(m)

        IPython.display.display(m)
    '''
    def fetch_satellite_image_static(
        self, *,
        width: int = 1024,
        buffer_m: int = 250,
        annotate: bool = False,
        save_path: str | None = None,
        # ─ caching ─
        cache: bool = True,
        cache_dir: str = "tile_cache",
        force_download: bool = False,
        # ─ connection control ─
        timeout: int = 15,
    ):
        """
        Download (or load from cache) an Esri World-Imagery JPEG for this tile.

        • width         – pixel width of the downloaded JPEG  
        • buffer_m      – metres added on each side of the tile  
        • annotate      – draw a red rectangle around the original tile on the
                        *returned* image (the cached file stays unmodified)  
        • save_path     – optional extra location to save the JPEG  
        • cache         – use on-disk cache (default *True*)  
        • cache_dir     – folder for cached images  
        • force_download– ignore any cached file and re-download  
        • timeout       – seconds before the HTTP request is aborted

        Returns a PIL.Image and stores it on ``self.sat_image``.
        """
        # ──────────────────── 0. work out cache path ───────────────────────────
        # accept a directory: auto-create a sensible file-name
        if save_path and os.path.isdir(save_path):
            save_path = os.path.join(
                save_path, f"{self.tile_name}_{buffer_m}m_{width}px.jpg"
            )

        if cache:
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(
                cache_dir,
                f"{self.tile_name}_{buffer_m}m_{width}px.jpg"
            )
            if os.path.exists(cache_file) and not force_download:
                img = Image.open(cache_file)
                # optional annotation (done on an in-memory *copy*)
                if annotate:
                    draw = ImageDraw.Draw(img)
                    # rectangle that hugs the *cropped* image
                    draw.rectangle(
                        [(0, 0), (img.width - 1, img.height - 1)],
                        outline="red", width=3
                    )
                self.sat_image = img
                if save_path:
                    img.save(save_path, format="JPEG")
                return img

        # ──────────────────── 1. buffer metres → degrees ───────────────────────
        m_per_deg_lat = 111_320
        m_per_deg_lon = 111_320 * math.cos(math.radians(self.mid_lat))
        d_lat = buffer_m / m_per_deg_lat
        d_lon = buffer_m / m_per_deg_lon

        ext_min_lat = self.min_lat - d_lat
        ext_max_lat = self.max_lat + d_lat
        ext_min_lon = self.min_lon - d_lon
        ext_max_lon = self.max_lon + d_lon

        lon_span, lat_span = ext_max_lon - ext_min_lon, ext_max_lat - ext_min_lat
        height = round(width * lat_span / lon_span)

        # ──────────────────── 2. HTTP request with timeout ─────────────────────
        url = ("https://services.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/export")
        params = {
            "bbox": f"{ext_min_lon},{ext_min_lat},{ext_max_lon},{ext_max_lat}",
            "bboxSR": 4326,
            "imageSR": 4326,
            "size": f"{width},{height}",
            "format": "jpg",
            "f": "image",
        }
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Satellite request timed out after {timeout} s; try again later."
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Satellite request failed: {e}")

        img = Image.open(BytesIO(r.content))   # in-memory decode

        # ── NEW: crop back to the true tile extent ──────────────────────
        crop_to_tile = True            # set to False if you ever want the collar
        if crop_to_tile:
            def lonlat_px(lon, lat):
                x = (lon - ext_min_lon) / lon_span * width
                y = (1 - (lat - ext_min_lat) / lat_span) * height
                return int(round(x)), int(round(y))

            x0, y0 = lonlat_px(self.min_lon, self.max_lat)  # upper-left
            x1, y1 = lonlat_px(self.max_lon, self.min_lat)  # lower-right
            img = img.crop((x0, y0, x1, y1))
        # ────────────────────────────────────────────────────────────────

        # ──────────────────── 3. save to cache (raw) ────────────────────────────
        if cache:
            img.save(cache_file, format="JPEG")

        # ──────────────────── 4. optional annotation ───────────────────────────
        if annotate and buffer_m > 0:
            draw = ImageDraw.Draw(img)

            def lonlat_px(lon, lat):
                x = (lon - ext_min_lon) / lon_span * width
                y = (1 - (lat - ext_min_lat) / lat_span) * height
                return int(x), int(y)

            draw.rectangle(
                [lonlat_px(self.min_lon, self.max_lat),
                lonlat_px(self.max_lon, self.min_lat)],
                outline="red", width=3
            )

        # ──────────────────── 5. final bookkeeping ─────────────────────────────
        self.sat_image = img
        if save_path:
            img.save(save_path, format="JPEG")
        return img
    '''
    def fetch_satellite_image_static(
        self, *,
        width: int = 1024,
        buffer_m: int = 250,
        annotate: bool = False,
        save_path: str | None = None,
        # ─ caching ─
        cache: bool = True,
        cache_dir: str = "tile_cache",
        force_download: bool = False,
        # ─ connection control ─
        timeout: int = 15,
    ):
        """
        Download (or load from cache) an Esri World-Imagery JPEG for this tile.

        Parameters
        ----------
        width        : pixel width of the *downloaded* image
        buffer_m     : metres added on every side (0 → none)
        annotate     : draw a red rectangle around the original tile
        save_path    : optional extra filename or directory
        cache        : use on-disk cache
        cache_dir    : folder for cached images
        force_download : ignore cache even if present
        timeout      : seconds before the HTTP request is aborted

        Returns
        -------
        PIL.Image.Image    (also stored on ``self.sat_image``)
        """

        BUFFER_REQUIRED = 500
        # ───────────────────── 0.  resolve save_path  ──────────────────────────
        if save_path and os.path.isdir(save_path):
            save_path = os.path.join(
                save_path,
                f"{self.tile_name}_{buffer_m}m_{width}px.jpg"
            )

        # ───────────────────── 1.  cache lookup  ───────────────────────────────
        if cache:
            os.makedirs(cache_dir, exist_ok=True)
            cache_file = os.path.join(
                cache_dir,
                f"{self.tile_name}_{buffer_m}m_{width}px.jpg"
            )
            if os.path.exists(cache_file) and not force_download:
                img = PILImage.open(cache_file)
                if annotate:
                    # no buffered extent known – fall back to exact tile bounds
                    self._annotate_tile(
                        img,
                        self.min_lon, self.max_lon,
                        self.min_lat, self.max_lat)
                self.sat_image = img
                if save_path:
                    img.save(save_path, format="JPEG")
                return img

        # ───────────────────── 2.  buffer metres → degrees  ────────────────────
        m_per_deg_lat = 111_320
        m_per_deg_lon = 111_320 * math.cos(math.radians(self.mid_lat))
        if buffer_m == 0:
            d_lat = BUFFER_REQUIRED / m_per_deg_lat
            d_lon = BUFFER_REQUIRED / m_per_deg_lon
        else:
            d_lat = buffer_m / m_per_deg_lat
            d_lon = buffer_m / m_per_deg_lon

        # buffered geographic extent
        ext_min_lat = self.min_lat - d_lat
        ext_max_lat = self.max_lat + d_lat
        ext_min_lon = self.min_lon - d_lon
        ext_max_lon = self.max_lon + d_lon

        # pixel height that keeps square pixels
        lon_span, lat_span = ext_max_lon - ext_min_lon, ext_max_lat - ext_min_lat
        height = round(width * lat_span / lon_span)

        # ───────────────────── 3.  HTTP request  ───────────────────────────────
        url = ("https://services.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/export")
        params = {
            "bbox"   : f"{ext_min_lon},{ext_min_lat},{ext_max_lon},{ext_max_lat}",
            "bboxSR" : 4326,
            "imageSR": 4326,
            "size"   : f"{width},{height}",
            "format" : "jpg",
            "f"      : "image",
        }
        try:
            r = requests.get(url, params=params, timeout=timeout)
            r.raise_for_status()
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Satellite request timed out after {timeout} s; try again later."
            )
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Satellite request failed: {e}")

        img = PILImage.open(BytesIO(r.content))     # full (possibly buffered) image

        if buffer_m == 0:                      # nothing to do if no buffer
            w, h = img.size                   # the *buffered* pixel dims

            lon_span = ext_max_lon - ext_min_lon
            lat_span = ext_max_lat - ext_min_lat

            def lonlat_px(lon, lat):
                """Convert lon/lat to pixel in the buffered image coordinate system."""
                x = (lon - ext_min_lon) / lon_span * w
                y = (1 - (lat - ext_min_lat) / lat_span) * h
                return int(round(x)), int(round(y))

            # pixel corners of the original tile inside the buffered picture
            x0, y0 = lonlat_px(self.min_lon, self.max_lat)   # upper-left
            x1, y1 = lonlat_px(self.max_lon, self.min_lat)   # lower-right

            img = img.crop((x0, y0, x1, y1))                 # <-- REMOVE THE BUFFER

        # ───────────────────── 4.  save to cache  ──────────────────────────────
        if cache:
            img.save(cache_file, format="JPEG")

        # ───────────────────── 5.  optional annotation  ────────────────────────
        if annotate:
            self._annotate_tile(
                img,
                ext_min_lon, ext_max_lon,
                ext_min_lat, ext_max_lat)

        # ───────────────────── 6.  bookkeeping & return  ───────────────────────
        self.sat_image = img
        if save_path:
            img.save(save_path, format="JPEG")
        return img


    # --------------------------------------------------------------------------
    # helper that knows how to turn tile lat/lon into pixels of the
    # *buffered* image and draw the rectangle.
    # --------------------------------------------------------------------------
    def _annotate_tile(self, img,
                   ext_min_lon, ext_max_lon,
                   ext_min_lat, ext_max_lat):
        """Draw a red rectangle for this tile inside *img*."""
        draw = ImageDraw.Draw(img)

        w, h = img.size
        lon_span = ext_max_lon - ext_min_lon
        lat_span = ext_max_lat - ext_min_lat

        def lonlat_px(lon, lat):
            x = (lon - ext_min_lon) / lon_span * w
            y = (1 - (lat - ext_min_lat) / lat_span) * h
            return int(round(x)), int(round(y))

        draw.rectangle(
            [lonlat_px(self.min_lon, self.max_lat),
            lonlat_px(self.max_lon, self.min_lat)],
            outline="red", width=3
        )

    def display_sat_image(self, scale=1.0):
        img = self.sat_image
        new_size = (int(img.width * scale), int(img.height * scale))
        img_resized = img.resize(new_size, resample=PILImage.Resampling.LANCZOS)

        # Save to bytes
        buf = io.BytesIO()
        img_resized.save(buf, format='PNG')
        buf.seek(0)

        # Display
        ipd.display(Image(data=buf.getvalue()))

    def print_metadata(self):
        print(f"Tile index: {self.index}")
        print(f"Tile name: {self.tile_name}")
        print(f"Tile dimensions (w x h): {self.width:.0f} x {self.height:.0f} m")
        print(f"Tile area: {self.area:.2f} km**2")
        print(f"Tile centre coordinates: {self.mid_lat:.4f}, {self.mid_lon:.4f}")
        


class TileMetadata:
    def __init__(self, doi, path_to_tiles, verbose=True):
        self.doi = doi
        self.verbose = verbose
        self.dataset = self._fetch_dataset_metadata()
        self._extract_dataset_metadata(self.dataset)
        self._fetch_tile_metadata(path_to_tiles)

        self._extract_tile_metadata()

    def _fetch_dataset_metadata(self):
        try:
            datasets = earthaccess.search_datasets(doi=self.doi)
            if self.verbose:
                print(f"Found {len(datasets)} datasets for DOI: {self.doi}")
            return datasets[0]
        except Exception as e:
            print(f"Failed to download dataset; error: {e}")
            return []

    def _extract_dataset_metadata(self, dataset):
        try:
            meta = dataset["meta"]
            umm = dataset["umm"]

            self.native_id = meta["native-id"]
            self.concept_id = meta["concept-id"]
            self.granule_count = meta["granule-count"]

            spatial = umm["SpatialExtent"]["HorizontalSpatialDomain"]["Geometry"]["BoundingRectangles"][0]
            self.west = spatial["WestBoundingCoordinate"]
            self.north = spatial["NorthBoundingCoordinate"]
            self.east = spatial["EastBoundingCoordinate"]
            self.south = spatial["SouthBoundingCoordinate"]

            self.temporal_extent = umm["TemporalExtents"][0]["RangeDateTimes"][0]
            self.abstract = umm["Abstract"]

        except (KeyError, IndexError, TypeError) as e:
            print(f"Metadata extraction failed: {e}")

    def _fetch_tile_metadata(self, path_to_tiles):
        try:

            # Coordinates of site Z-Mt-04
            lATITUDE    = -9.8654
            LONGITUDE   = -57.6760
            DELTA       = 0.1

            bbox = (
                LONGITUDE - DELTA,
                lATITUDE - DELTA,
                LONGITUDE + DELTA,
                lATITUDE + DELTA
                )
            
            result = earthaccess.search_data(
                concept_id=self.concept_id,
                bounding_box = bbox,
                cloud_hosted=False
            )[0]

            tile_metadata_file_path = earthaccess.download(result, path_to_tiles)[0]
            self.df_tile_metadata = pd.read_csv(tile_metadata_file_path)
            if self.verbose:
                print(f"Tile metadata CSV loaded from: {tile_metadata_file_path}")
        except Exception as e:
            print(f"Error fetching tile metadata: {e}")

    def _extract_tile_metadata(self):
        meta = self.dataset["meta"]
        umm = self.dataset["umm"]

        self.native_id = meta["native-id"]
        self.concept_id = meta["concept-id"]
        self.abstract = umm["Abstract"]

        spatial_extent = umm["SpatialExtent"]["HorizontalSpatialDomain"]["Geometry"]["BoundingRectangles"][0]
        self.west = spatial_extent["WestBoundingCoordinate"]
        self.north = spatial_extent["NorthBoundingCoordinate"]
        self.east = spatial_extent["EastBoundingCoordinate"]
        self.south = spatial_extent["SouthBoundingCoordinate"]

        temporal_extent = umm["TemporalExtents"][0]["RangeDateTimes"][0]
        self.start_date = datetime.strptime(temporal_extent["BeginningDateTime"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")
        self.end_date = datetime.strptime(temporal_extent["EndingDateTime"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%Y-%m-%d")

    def print_metadata(self):
        print(f"Native ID: {self.native_id}")
        print(f"Granule count: {self.granule_count}")
        print(f"Spatial extent (west, north, east, south): {self.west:.4f}, {self.north:.4f}, {self.east:.4f}, {self.south:.4f}")
        print(f"Temporal extent: {self.start_date} to {self.end_date}")
        print("Abstract:")
        print(self.abstract)


def login(verbose=True):
    try:
        auth = earthaccess.login()
        if auth.authenticated:
            if verbose:
                print("Successfully authenticated with earthaccess.")
        else:
            if verbose:
                print("Authentication failed. Check credentials.")
        return auth.authenticated
    except Exception as e:
        if verbose:
            print(f"An error occurred during earthaccess login: {e}")
        return False
