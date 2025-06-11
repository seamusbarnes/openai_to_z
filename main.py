"""
main_v02.py
"""

import os
import sys
import time
import argparse
import pandas as pd
import matplotlib.pyplot as plt

import src.config as config
import src.satellite as satellite
import src.proj_io as proj_io
import src.lidar as lidar

# helper functions
def pt(msg=None):
    current_time = time.strftime("%H:%M:%S")
    if msg:
        print(f"{current_time}: {msg}")
    else:
        print(current_time)

def check_positive(value):
    ivalue = int(value)
    if ivalue < 1:
        raise argparse.ArgumentTypeError("%s is an invalid positive int value, must be >= 1" % value)
    return ivalue

if __name__ == "__main__":

    # ARGPARSE
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config_file", type=str, help="Path to YAML config file"
    )
    parser.add_argument(
        "--show-sat", action="store_true",
        help="Show intermediate satellite images"
    )
    parser.add_argument(
        "--show-dtm", action="store_true",
        help="Show intermediate DTM images"
    )
    parser.add_argument(
        "--n-tiles",
        type=check_positive,
        default=1,
        metavar="N",
        help="Number of tiles (integer >= 1, default: 1)"
    )
    parser.add_argument(
        "--print-metadata", action="store_true",
        help="Print tile and point-cloud metadata: area, number of counts, all-point density, classification-2-point density"
    )
    parser.add_argument(
        "--tile-name",
        default=None,
        help="Specify specific tile name (optional)"
    )
    args = parser.parse_args()

    # GET CONFIG DETAILS
    cfg = config.Config(args.config_file)

    # SOME VARIABLES
    CWD = os.getcwd()
    PATH_TO_DATASET_METADATA = os.path.join(
        CWD,
        cfg["path_to_metadata"],
        cfg["dataset_metadata_filename"]
    )
    LAZ_RAW_DIR = cfg["path_to_laz_raw"]
    LAZ_PRC_DIR = cfg["path_to_laz_processed"]
    SAT_RAW_DIR = cfg["path_to_sat"]

    DTM_DIR = cfg["path_to_dtm"]
    VIS_DIR = cfg["path_to_vis"]

    PATH_TO_PDAL_TEMPLATE_DIR = cfg["path_to_pdal_templates"]
    PDAL_PIPELINE_FILENAME = cfg["pdal_pipeline_filename"]
    PIPELINE_PATH = os.path.join(CWD, PATH_TO_PDAL_TEMPLATE_DIR, PDAL_PIPELINE_FILENAME)

    # GET EARTHDATA BEARER TOKEN
    EARTHDATA_BEARER_TOKEN = proj_io.get_earthdata_token()


    # AUTHENTICATE EARTHACCESES
    # proj_io.authenticate_earthaccess()

    # import dataset metadata into pandas dataframe
    df = pd.read_csv(PATH_TO_DATASET_METADATA)

    for index in range(args.n_tiles):

        # if user has chosen a specific tile-name, disregate n-tiles and process that specific tile
        if args.tile_name:
            print(f"User specified tile name: {args.tile_name}")
            row = df[df["filename"] == args.tile_name]
            if len(row) == 0:
                raise ValueError(f"Tile name '{args.tile_name}' not found in metadata!")
            row = row.iloc[0]
        else:
            row = df.iloc[index]
        filename = row["filename"]

        pt(f"Processing row: {index+1}/{len(df)}; Filename: {filename}")

        # laz_path = proj_io.fetch_laz_file(
        #     filename,
        #     LAZ_RAW_DIR,
        #     overwrite=False,
        #     show_progress=False,
        #     token=EARTHDATA_BEARER_TOKEN,
        #     verbose=True
        # )

        laz_path = proj_io.fetch_laz_file_earthaccess(
            filename,
            LAZ_RAW_DIR,
            overwrite=True,
            show_progress=False,
            verbose=True
        )
        if args.show_sat:
            satellite.show_sat_image(df, filename,save_path=SAT_RAW_DIR, overwrite=True)

        if args.print_metadata:
            lidar.print_metadata_table(laz_path, row["tile_area_m2"])

        output_path = lidar.run_pdal_pipeline(
            laz_path,
            DTM_DIR,
            PIPELINE_PATH,
            verbose=2
        )

        if args.tile_name:
            break