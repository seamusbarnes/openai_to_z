import os
import sys
import argparse
import logging
from pathlib import Path
import tempfile
import shutil
import pdal
import json

def setup_logging(logfile="enhance_laz_log.txt"):
    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(logfile, mode='a'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info("=== enhance_laz.py run started ===")

def find_laz_files(input_dir, prefix="RIB"):
    # Finds all .laz files that start with specified prefix in input_dir
    return sorted(str(p) for p in Path(input_dir).glob(f"{prefix}*.laz"))

def filter_ground_points(infile, outfile):
    pipeline = [
        {"type": "readers.las", "filename": str(infile)},
        {"type": "filters.range", "limits": "Classification[2:2]"},
        {"type": "writers.las", "filename": str(outfile)}
    ]
    pl = pdal.Pipeline(json.dumps(pipeline))
    count = pl.execute()
    logging.info(f"Filtered '{infile}' -> '{outfile}': {count} ground points")
    return count

def merge_laz_files(laz_files, out_merged_laz):
    readers = [{"type": "readers.las", "filename": f} for f in laz_files]
    pipeline = readers + [  # concatenate instead of insert!
        {"type": "filters.voxelcentroidnearestneighbor", "cell": 0.01},
        {"type": "writers.las", "filename": str(out_merged_laz)}
    ]
    pl = pdal.Pipeline(json.dumps({"pipeline": pipeline}))
    total = pl.execute()
    logging.info(f"Merged {len(laz_files)} ground-only files -> '{out_merged_laz}': {total} points")
    return total

def main():
    parser = argparse.ArgumentParser(description="Enhance LiDAR ground point coverage by merging ground points from overlapping .laz tiles.")
    parser.add_argument('input_dir', type=str, help='Directory with input RIB*.laz files (read-only)')
    parser.add_argument('output_dir', type=str, help='Directory to save the enhanced output LAZ')
    parser.add_argument('--output-name', default='enhanced_ground.laz', help="Filename for the enhanced merged .laz (default: enhanced_ground.laz)")
    parser.add_argument('--keep-tmp', action='store_true', help="Keep temporary ground-only files")
    parser.add_argument('--prefix', default='RIB', help="Filename prefix to filter input (default: 'RIB')")
    args = parser.parse_args()

    setup_logging()

    in_dir = Path(args.input_dir).resolve()
    out_dir = Path(args.output_dir).resolve()
    out_laz = out_dir / args.output_name

    # Safety: input and output directories must be different!
    if in_dir == out_dir:
        logging.error("Input and output directories must be different! Refusing to run.")
        sys.exit(1)

    # Input dir exists, output dir created if needed
    if not in_dir.is_dir():
        logging.error(f"Input directory does not exist: {in_dir}")
        sys.exit(1)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Safety: refuse to overwrite any existing LAZ in input directory!
    forbidden = in_dir / args.output_name
    if forbidden.exists():
        logging.error(f"Would overwrite an existing file in input directory: {forbidden}")
        sys.exit(1)

    # Step 1: Find all input tiles
    files = find_laz_files(in_dir, args.prefix)
    if not files:
        logging.error(f"No .laz files found in {in_dir} with prefix '{args.prefix}'")
        sys.exit(1)
    logging.info(f"Found {len(files)} files, e.g.: {files[:4]}{' ...' if len(files)>4 else ''}")

    # Step 2: Extract ground points to temp files
    tmp_dir = tempfile.mkdtemp(prefix="ground_extract_")
    ground_files = []
    for f in files:
        out = Path(tmp_dir) / (Path(f).stem + "_ground.laz")
        try:
            filter_ground_points(f, out)
            ground_files.append(str(out))
        except Exception as e:
            logging.error(f"Failed filtering {f}: {e}")

    if not ground_files:
        logging.error("No ground-classified LAS/LAZ files produced.")
        shutil.rmtree(tmp_dir)
        sys.exit(1)

    # Step 3: Merge all ground-only files
    try:
        merge_laz_files(ground_files, str(out_laz))
    except Exception as e:
        logging.error(f"Failed merging ground-only files: {e}")
        if not args.keep_tmp:
            shutil.rmtree(tmp_dir)
        sys.exit(1)

    logging.info(f"Enhanced ground points .laz written to: {out_laz}")

    # Step 4: Clean up
    if not args.keep_tmp:
        shutil.rmtree(tmp_dir)
    else:
        logging.info(f"Temporary ground-only files kept in: {tmp_dir}")

    logging.info("=== enhance_laz.py completed successfully ===")

if __name__ == '__main__':
    main()