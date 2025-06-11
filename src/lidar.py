# src/lidar_utils/lidar.py

import os
import json
import pathlib
import pdal
import laspy
from collections import Counter
import numpy as np

def tile_bounds(laz_path, res=2.0):
    """
    Read the bounds of the LAZ file and return: (min_x, max_x, min_y, max_y)
    """
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

def get_metadata(
    path_to_laz, 
    tile_area_m2, 
    all_classes=range(0,20), 
    ground_class=2
):
    """
    Compute stats for a LAZ tile. Returns a dict with keys:
        - n_points_total
        - class_{i}_count, class_{i}_pct for i in all_classes
        - n_points_ground, ground_pct, ...
        - density_total, density_ground
        - z_min, z_max, z_mean, z_std (all points)
        - z_ground_min, z_ground_max, z_ground_mean, z_ground_std
        - intensity_min, intensity_max, intensity_mean, intensity_std
        - only_return_pct
        - scan_angle_min, scan_angle_max, scan_angle_mean, scan_angle_std
        - gps_time_min, gps_time_max
    """
    meta = {}
    with laspy.open(path_to_laz) as lfile:
        las = lfile.read()
        classifications = np.asarray(las.classification)
        n_total = len(classifications)
        meta['n_points_total'] = n_total

        # Class stats
        unique_classes, counts = np.unique(classifications, return_counts=True)
        class_count_dict = dict(zip(unique_classes, counts))
        for cls in all_classes:
            cnt = class_count_dict.get(cls, 0)
            meta[f'class_{cls}_count'] = int(cnt)
            meta[f'class_{cls}_pct'] = (float(cnt) / n_total) if n_total else 0.0

        meta['n_points_ground'] = meta[f'class_{ground_class}_count']
        meta['ground_pct'] = meta[f'class_{ground_class}_pct']
        for k, v in zip(
            ["unclassified", "veg_low", "veg_med", "veg_high"],
            [1, 3, 4, 5]
        ):
            meta[f'n_points_{k}'] = meta.get(f'class_{v}_count', 0)

        meta['tile_area_m2'] = tile_area_m2
        meta['density_total'] = n_total / tile_area_m2 if tile_area_m2 > 0 else np.nan
        meta['density_ground'] = meta['n_points_ground'] / tile_area_m2 if tile_area_m2 > 0 else np.nan

        z = np.asarray(las.z)
        meta['z_min'] = float(z.min())
        meta['z_max'] = float(z.max())
        meta['z_mean'] = float(z.mean())
        meta['z_std'] = float(z.std())

        ground_z = z[classifications == ground_class]
        if ground_z.size > 0:
            meta['z_ground_min'] = float(ground_z.min())
            meta['z_ground_max'] = float(ground_z.max())
            meta['z_ground_mean'] = float(ground_z.mean())
            meta['z_ground_std'] = float(ground_z.std())
        else:
            for f in ['z_ground_min','z_ground_max','z_ground_mean','z_ground_std']:
                meta[f] = np.nan

        # Intensity
        inten = getattr(las, "intensity", None)
        if inten is not None:
            inten = np.asarray(inten)
            meta['intensity_min'] = float(inten.min())
            meta['intensity_max'] = float(inten.max())
            meta['intensity_mean'] = float(inten.mean())
            meta['intensity_std'] = float(inten.std())
        else:
            for f in ['intensity_min', 'intensity_max', 'intensity_mean', 'intensity_std']:
                meta[f] = np.nan

        # Only-return
        try:
            return_number = np.asarray(las.return_number)
            num_returns = np.asarray(las.number_of_returns)
            only_return = (return_number == num_returns)
            meta['only_return_pct'] = only_return.sum() / n_total if n_total else 0
        except Exception:
            meta['only_return_pct'] = np.nan

        # Scan angle
        scan = getattr(las, 'scan_angle', None)
        if scan is not None:
            scan = np.asarray(scan)
            meta['scan_angle_min'] = float(scan.min())
            meta['scan_angle_max'] = float(scan.max())
            meta['scan_angle_mean'] = float(scan.mean())
            meta['scan_angle_std'] = float(scan.std())
        else:
            for f in ['scan_angle_min','scan_angle_max','scan_angle_mean','scan_angle_std']:
                meta[f] = np.nan

        gps = getattr(las, 'gps_time', None)
        if gps is not None:
            gps = np.asarray(gps)
            meta['gps_time_min'] = float(gps.min())
            meta['gps_time_max'] = float(gps.max())
        else:
            meta['gps_time_min'] = meta['gps_time_max'] = np.nan

    return meta

def get_laz_classification_counts(path_to_file, all_classes=range(0, 20)):
    """
    Efficiently reads a LAS/LAZ file and returns the counts of point classifications,
    by using the optimized get_metadata() function.
    :param path_to_file: Path to the LAS file.
    :param all_classes: range or list of classification codes to include
    :return: Counter object with classification counts, and total number of points.
    """
    meta = get_metadata(path_to_file, tile_area_m2=1.0, all_classes=all_classes)
    counts = Counter({
        cls: meta.get(f'class_{cls}_count', 0) for cls in all_classes
    })
    total = meta.get('n_points_total', 0)
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

import os
import json
from typing import Any
import pdal

def laz_to_dtm(
    config: Any,
    filename_laz: str,
    dtm_path: str,
    pipeline_template_path: str,
    verbose: int = 0
) -> str:
    """
    Converts a .laz file to a DTM raster (.tif) using a parameterized PDAL pipeline template.

    Args:
        config (Any): Project configuration object, must support .get("paths", ...)
        filename_laz (str): The filename of the input .laz file (e.g., 'foo.laz')
        dtm_path (str): Full path (including filename) where the output .tif file should be saved
        pipeline_template_path (str): Path to a PDAL JSON pipeline template (with {in_laz}, {out_tif} placeholders)
        verbose (int): Level of verbosity:
            0 - Silent (only raise exceptions)
            1 - Print major steps (pipeline loading, file paths)
            2 - Print full intermediate values (pipeline templates, filled JSON, paths)

    Returns:
        str: Path to the generated DTM .tif file

    Raises:
        FileNotFoundError: If input files do not exist
        RuntimeError: If PDAL pipeline fails
        ValueError: If the resulting JSON is invalid

    Notes:
        - The pipeline template must use doubled braces `{{` and `}}` for all JSON structure,
          and single braces `{in_laz}` and `{out_tif}` for variable placeholders.
        - Example template snippet (not valid JSON until formatted):

            {{
              "pipeline": [
                {{
                  "type": "readers.las",
                  "filename": "{in_laz}"
                }},
                ...
                {{
                  "type": "writers.gdal",
                  "filename": "{out_tif}",
                  "resolution": 2.0
                }}
              ]
            }}
    """
    # 1. Resolve paths
    laz_full_path = os.path.join(config.get("paths", "raw", "laz"), filename_laz)
    if not os.path.isfile(laz_full_path):
        raise FileNotFoundError(f"Input .laz file not found: {laz_full_path}")
    if not os.path.isfile(pipeline_template_path):
        raise FileNotFoundError(f"PDAL pipeline template not found: {pipeline_template_path}")

    # 2. Read pipeline template as string
    try:
        with open(pipeline_template_path, 'r', encoding='utf-8') as f:
            pipeline_template = f.read()
        if verbose >= 2:
            print("[laz_to_dtm] Read pipeline template (may not be valid JSON yet!):")
            print(pipeline_template)
    except Exception as e:
        raise RuntimeError(f"Error reading pipeline template: {e}")

    # 3. Substitute in the variable placeholders
    try:
        pipeline_filled = pipeline_template.format(
            in_laz=laz_full_path,
            out_tif=dtm_path
        )
        if verbose >= 2:
            print("[laz_to_dtm] Pipeline after .format() (should be valid JSON):")
            print(pipeline_filled)
    except KeyError as e:
        raise ValueError(f"Missing template variable in pipeline: {e}")
    except Exception as e:
        raise ValueError(f"Error formatting pipeline template: {e}")

    # 4. Load JSON
    try:
        pipeline_dict = json.loads(pipeline_filled)
        if verbose >= 2:
            print("[laz_to_dtm] Parsed pipeline JSON (Python dict):")
            print(json.dumps(pipeline_dict, indent=2))
    except Exception as e:
        raise ValueError(f"Formatted pipeline is not valid JSON: {e}")

    # 5. Get the actual pipeline steps (list)
    if isinstance(pipeline_dict, dict) and "pipeline" in pipeline_dict:
        pdal_pipeline = pipeline_dict["pipeline"]
    elif isinstance(pipeline_dict, list):
        pdal_pipeline = pipeline_dict
    else:
        raise ValueError("Pipeline template must be a list or a dict with a 'pipeline' key.")

    # 6. Report output path if verbose
    if verbose >= 1:
        print(f"[laz_to_dtm] Full path to generated DTM (tif): {dtm_path}")

    # 7. Construct and execute PDAL pipeline
    try:
        pipeline_json_str = json.dumps(pdal_pipeline)
        pl = pdal.Pipeline(pipeline_json_str)
        count = pl.execute()
        if verbose >= 1:
            print(f"[laz_to_dtm] PDAL pipeline executed successfully, {count} points processed.")
    except RuntimeError as e:
        raise RuntimeError(f"PDAL pipeline execution failed: {e}")
    except Exception as e:
        raise RuntimeError(f"Error running PDAL pipeline: {e}")

    # 8. Confirm output file exists
    if not os.path.isfile(dtm_path):
        raise RuntimeError(f"PDAL pipeline ran without error, but output DTM file was not created: {dtm_path}")

    if verbose >= 1:
        print(f"[laz_to_dtm] Output DTM file created at: {dtm_path}")

    return dtm_path