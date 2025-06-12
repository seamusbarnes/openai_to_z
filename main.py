"""
main.py

Used functions in main.py:

src/config.py: Config
src/satellite.py: show_sat_image
src/lidar.py: print_metadata_table, run_pdal_pipeline

"""

import os
import sys
import time
import argparse
import pandas as pd
import logging
from pathlib import Path

import src.config as config
import src.satellite as satellite
import src.lidar as lidar

def check_positive(value):
    ivalue = int(value)
    if ivalue < 1:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value, must be >= 1" % value)
    return ivalue

def setup_logging(logfile="log.txt"):
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(logfile, mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("=== Pipeline run started ===")

if __name__ == "__main__":
    setup_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", type=str, help="Path to YAML config file")
    parser.add_argument("--show-sat", action="store_true", help="Show intermediate satellite images")
    parser.add_argument("--show-dtm", action="store_true", help="Show intermediate DTM images")
    parser.add_argument("--n-tiles", type=check_positive, default=1, metavar="N", help="Number of tiles (integer >= 1, default: 1)")
    parser.add_argument("--print-metadata", action="store_true", help="Print tile/point-cloud metadata")
    parser.add_argument("--tile-name", default=None, help="Specify a specific tile (optional)")
    args = parser.parse_args()

    try:
        # GET CONFIG DETAILS
        cfg = config.Config(args.config_file)
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        sys.exit(1)

    # Compose all key paths
    CWD = os.getcwd()
    dataset_metadata_path = os.path.join(CWD, cfg["path_to_metadata"], cfg["dataset_metadata_filename"])
    laz_raw_dir = cfg["path_to_laz_raw"]
    sat_raw_dir = cfg["path_to_sat"]
    dtm_dir = cfg["path_to_dtm"]
    pipeline_template_dir = cfg["path_to_pdal_templates"]
    pdal_pipeline_filename = cfg["pdal_pipeline_filename"]
    pipeline_path = os.path.join(CWD, pipeline_template_dir, pdal_pipeline_filename)

    # Verify critical files exist
    if not os.path.exists(dataset_metadata_path):
        logging.error(f"Metadata file not found: {dataset_metadata_path}")
        sys.exit(1)
    if not os.path.exists(pipeline_path):
        logging.error(f"PDAL pipeline file not found: {pipeline_path}")
        sys.exit(1)

    try:
        df = pd.read_csv(dataset_metadata_path)
    except Exception as e:
        logging.error(f"Failed to read dataset metadata: {e}")
        sys.exit(1)

    logging.info(f"Loaded metadata: {dataset_metadata_path}, {len(df)} rows")
    logging.info(f"Pipeline JSON: {pipeline_path}")

    tiles_to_process = [args.tile_name] if args.tile_name else df["filename"].head(args.n_tiles)

    for i, tile_name in enumerate(tiles_to_process, 1):
        try:
            if args.tile_name:
                row = df[df["filename"] == tile_name]
                if len(row) == 0:
                    logging.error(f"Tile '{tile_name}' not found in metadata!")
                    continue
                row = row.iloc[0]
            else:
                row = df[df["filename"] == tile_name].iloc[0]
            filename = row["filename"]
            laz_path = os.path.join(laz_raw_dir, filename)

            logging.info(f"Tile {i}/{len(tiles_to_process)}: {filename}")
            logging.info(f"RAW LAZ path: {laz_path}")

            if not os.path.exists(laz_path):
                logging.warning(f"{filename} not downloaded (skipping)")
                continue

            if args.show_sat:
                satellite_img_path = Path(sat_raw_dir) / f"{Path(filename).stem}.png"
                logging.info(f"Showing satellite image for {filename} (output: {satellite_img_path})")
                satellite.show_sat_image(df, filename, save_path=satellite_img_path, overwrite=True)

            if args.print_metadata:
                logging.info(f"Printing metadata for {filename}")
                lidar.print_metadata_table(laz_path, row["tile_area_m2"])

            start_time = time.time()
            output_path = lidar.run_pdal_pipeline(
                laz_path,
                dtm_dir,
                pipeline_path,
                verbose=2
            )
            duration = time.time() - start_time

            logging.info(f"Pipeline for {filename} output: {output_path} (elapsed: {duration:.1f}s)")

            if args.tile_name:
                break

        except Exception as e:
            logging.exception(f"Error processing tile {tile_name}: {e}")
            continue

    logging.info("=== Pipeline run completed ===")