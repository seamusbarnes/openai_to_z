# src/lidar_utils/lidar.py

import os
import json
import pathlib
import pdal
import laspy
from collections import Counter

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

    print(f"[lidar] Running PDAL pipeline with {len(pipeline_def['pipeline'])} stages...")
    print(f"[lidar] Pipeline definition: {json.dumps(pipeline_def, indent=2)[:1000]} ...")
    pl = pdal.Pipeline(json.dumps(pipeline_def))
    print("[lidar] Starting PDAL execution...")
    count = pl.execute()
    print(f"[lidar] PDAL complete, {count} points processed.")

def get_laz_classification_counts(path_to_file):
    """
    Reads a LAS file and returns the counts of point classifications.

    :param path_to_file: Path to the LAS file.
    :return: Counter object with classification counts.
    """
    with laspy.open(path_to_file) as fh:
        las = fh.read()
        classifications = las.classification

    # Count occurrences
    counts = Counter(classifications)
    total = sum(counts.values())
    
    return counts, total

def print_laz_classification_counts(counts, total):
    """
    Prints the classification counts in a formatted way.

    :param counts: Counter object with classification counts.
    :param total: Total number of classifications.
    """
    # Classification names (ASPRS standard codes)
    class_names = {
        0: "Created, never classified",
        1: "Unclassified",
        2: "Ground",
        3: "Low Vegetation",
        4: "Medium Vegetation",
        5: "High Vegetation",
        6: "Building",
        7: "Low Point (noise)",
        8: "Model Key-point",
        9: "Water",
        10: "Reserved",
        11: "Reserved",
        12: "Overlap Points",
        13: "Reserved",
        14: "Reserved",
        15: "Reserved"
    }

    # Prepare output
    header = f"{'Class Code':<10} {'Count':>10} {'Percent':>10}  {'Name'}"
    print(header)
    print('-' * len(header))
    for class_code, count in sorted(counts.items()):
        percent = count / total * 100
        name = class_names.get(class_code, 'Unknown')
        print(f"{class_code:<10} {count:>10} {percent:9.2f}%  {name}")

    # Print total for reference
    print('-' * len(header))
    print(f"{'TOTAL':<10} {total:>10} {100:9.2f}%")

def laz_to_dtm(config, filename_laz, filename_tif, filename_pipeline, resolution=2.0):
    path_to_laz = os.path.join(
        config.get("paths", "raw", "laz"),
        filename_laz
    )
    path_to_tif = os.path.join(
        config.get("paths", "processed", "dtm"),
        filename_tif
    )
    path_to_pipeline = os.path.join(
        config.get("paths", "pdal_pipelines"),
        filename_pipeline)

    template_text = load_template(path_to_pipeline)
    pipeline_dict = build_pipeline(
        template_text,
        in_laz=path_to_laz,
        out_tif=path_to_tif,
        res=resolution
    )
    run_pipeline(pipeline_dict)
    return path_to_tif