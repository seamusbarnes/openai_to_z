# src/lidar_utils/lidar.py

import json
import pathlib
import pdal

def tile_bounds(laz_path, res=2.0):
    """
    Read the bounds of the LAZ file and return: (min_x, max_x, min_y, max_y)
    """
    import laspy
    print(f"[lidar] Getting tile bounds for {laz_path}...")
    with laspy.open(str(laz_path)) as fh:
        hdr = fh.header
        min_x, max_x = hdr.min[0], hdr.max[0]
        min_y, max_y = hdr.min[1], hdr.max[1]
        # Optionally snap to even grid with res, you can adjust
    print(f"[lidar] Bounds: x=({min_x}, {max_x}), y=({min_y}, {max_y})")
    return min_x, max_x, min_y, max_y

def load_template(path):
    """
    Load a JSON string (may contain placeholders like '{in_laz}', '{out_tif}').
    """
    print(f"[lidar] Loading pipeline template from: {path}")
    return pathlib.Path(path).read_text()

def build_pipeline(template_text, **kwargs):
    """
    Fill placeholders in *template_text* and return as parsed dict.
    """
    print(f"[lidar] Building PDAL pipeline from template...")
    tpl = template_text.format(**{k: str(v) for k, v in kwargs.items()})
    pipeline_def = json.loads(tpl)
    return pipeline_def

def run_pipeline(pipeline_def):
    """
    Run the given pipeline JSON dict via PDAL.
    """
    print(f"[lidar] Running PDAL pipeline with {len(pipeline_def['pipeline'])} stages...")
    pl = pdal.Pipeline(json.dumps(pipeline_def))
    count = pl.execute()
    print(f"[lidar] PDAL complete, {count} points processed.")