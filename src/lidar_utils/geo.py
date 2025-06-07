"""
Pure geometry helpers (no disk I/O).
"""
from __future__ import annotations
import dataclasses as _dc
import rasterio, pyproj
from shapely.geometry import box
from typing import Tuple


@_dc.dataclass(slots=True)
class TileMeta:
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

    @property
    def midpoint(self) -> Tuple[float, float]:
        """(lat, lon) centre of tile."""
        return ((self.max_lat + self.min_lat) / 2, (self.max_lon + self.min_lon) / 2)

    @property
    def bounds(self):
        """Return a Shapely bbox in WGS84."""
        return box(self.min_lon, self.min_lat, self.max_lon, self.max_lat)

    @property
    def width_m(self) -> float:
        """Approximate east-west dimension (metres)."""
        geod = pyproj.Geod(ellps="WGS84")
        _, _, dist = geod.inv(self.min_lon, self.min_lat, self.max_lon, self.min_lat)
        return dist
