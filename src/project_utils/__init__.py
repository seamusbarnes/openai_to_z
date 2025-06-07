"""
Light-weight helpers for LiDAR + satellite batch processing.

Sub-packages
------------
io          – search & download (earthaccess, HTTP, local FS)
geo         – pure geometry helpers (bounds, mid-points, CRS)
satellite   – fetch & crop visual basemaps
lidar       – PDAL pipeline templating & execution
raster      – DSM/DTM/CHM maths, hillshade
vis         – quick-look plots & overlays
"""

# from importlib import metadata as _m

# __version__: str = _m.version(__name__) if _m.version else "0.0.0"
