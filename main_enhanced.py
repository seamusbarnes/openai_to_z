import os
import sys
import time
import argparse
import logging
from pathlib import Path
import yaml

import src.lidar as lidar

def setup_logging(logfile="log_enhanced.txt"):
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(logfile, mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("=== Enhanced Pipeline run started ===")

def load_config(config_file):
    with open(config_file) as f:
        return yaml.safe_load(f)

if __name__ == "__main__":
    setup_logging()

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", type=str, help="Path to YAML config_enhanced.yml")
    args = parser.parse_args()

    try:
        cfg = load_config(args.config_file)
    except Exception as e:
        logging.error(f"Failed to load config: {e}")
        sys.exit(1)

    laz_enhanced_dir = cfg["path_to_laz_enhanced"]
    dtm_dir = cfg["path_to_dtm"]
    pipeline_template_dir = cfg["path_to_pdal_templates"]
    pdal_pipeline_filename = cfg["pdal_pipeline_filename"]
    pipeline_path = os.path.join(pipeline_template_dir, pdal_pipeline_filename)
    enhanced_filenames = cfg["enhanced_filenames"]

    for i, fname in enumerate(enhanced_filenames, 1):
        laz_path = os.path.join(laz_enhanced_dir, fname)
        logging.info(f"[{i}/{len(enhanced_filenames)}] Processing: {laz_path}")

        if not os.path.exists(laz_path):
            logging.error(f"Input file does not exist: {laz_path}")
            continue
        if not os.path.exists(pipeline_path):
            logging.error(f"Pipeline template not found: {pipeline_path}")
            continue

        start_time = time.time()
        try:
            output_path = lidar.run_pdal_pipeline(
                laz_path,
                dtm_dir,
                pipeline_path,
                verbose=2
            )
            duration = time.time() - start_time
            logging.info(f"Pipeline for {fname} output: {output_path} (elapsed: {duration:.1f}s)")
        except Exception as e:
            logging.error(f"Failed processing {fname}: {e}")
            continue

    logging.info("=== Enhanced Pipeline run completed ===")