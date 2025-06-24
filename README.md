# openai_to_z

This repo can be used to download .laz files from the ORNL DAAC dataset [LiDAR Surveys over Selected Forest Research Sites, Brazilian Amazon, 2008-2018](https://daac.ornl.gov/CMS/guides/LiDAR_Forest_Inventory_Brazil.html) and run a pipeline to process them into DTMs using [PDAL (Point Data Abstraction Library)](https://pdal.io/en/stable/).

## Quick Start

### 1. Clone the repository

```bash
git clone <repo-url>
cd openai_to_z
```

### 2. Install Conda environment

Make sure you have conda or mamba installed.

```bash
conda env create -f environment.yml
conda activate openai_to_z
```

### 3. Configure data

- Put your LiDAR `.laz` files in `data/raw/laz`
- Put your satellite data (if needed) in `data/raw/sat`
- Ensure your `data/metadata/cms_brazil_lidar_tile_metadata.csv` metadata CSV is present

### 4. Edit config as needed

- See `config/config.yml` for pipeline paths and filenames
- Adjust pdal_pipeline_filename or other options as needed (see also config/pdal_pipeline_templates)

### 5. Run the main pipeline

```bash
python main.py config/config.yml --n-tiles 3
```

#### Arguments:

- `config/config.yml`: Path to YAML config (required)
- `--n-tiles N`: Number of tiles to process (default: 1)
- `--print-metadata`: Print tile/point-cloud metadata
- `--show-sat`: Show intermediate satellite images
- `--show-dtm`: Show intermediate DTM images
- `--tile-name TILE`: Process a specific tile by name

Example:

```bash
python main.py config/config.yml --print-metadata --n-tiles 2
```

#### 6. View DTM outputs

You can visualise the last DTM result (or specify a file) with:

```bash
python view_dtm.py
# or with a specific file:
python view_dtm.py --file data/processed/dtm/your_output.tif
```

## Repo Structure

```text
.
├── LICENSE
├── README.md
├── client_secrets.json
├── config
│   ├── config.yml
│   └── pdal_pipeline_templates/
├── data
│   ├── example/
│   ├── metadata/
│   ├── processed/
│   │   ├── denoised/
│   │   └── dtm/
│   └── raw/
│       ├── laz/
│       └── sat/
├── earthdata_token.txt
├── environment.yml
├── log.txt
├── main.py
├── mycreds.txt
├── scratch/
│   ... (various experimental/notebooks/scripts)
├── situation_report.md
├── src
│   ├── config.py
│   ├── lidar.py
│   └── satellite.py
└── view_dtm.py
```

#### Key locations:

- Config: `config/config.yml` and pipeline templates in `config/pdal_pipeline_templates/`
- Raw Data: `data/raw/laz/` (LiDAR LAZ), `data/raw/sat/` (satellite)
- Metadata: `data/metadata/cms_brazil_lidar_tile_metadata.csv`
- Processed Output: `data/processed/dtm/`
- Entry Point: `main.py` (pipeline), `view_dtm.py` (visualisation)

#### Example files are provided in `data/example/` for testing and demonstration:

- `RIB_A01_2014_laz_2.laz`: Sample LiDAR tile.
- `*.tif`, `*.png`: Example DTM rasters and visualisations.

These files are sufficient to test pipeline code and visualisation tools without downloading the full dataset. BUT the `config.yml` will have to be amended to point to the .laz example file in the example directory, instead of the `data/raw/laz directory`.

## To-Do

### Categories

- A: analysis
- F0: feature (top-level like `main.py` or `view_dtm.py`, or utils files used directly for top-level scripts)
- F1: feature (lower-level like `count_unique_locations.py` (not yet written) or `robust_downloader.py`)
- R: refactor

### List:

-

## BIG PROBLEMS!!!

2014 good, 2018 bad

- BON_A01_2013_laz_13_fnands.tif
- BON_A01_2018_LAS_11_fnands.tif

- RIB_A01_2014_laz_2_fnands.tif
- RIB_A01_2018_LAS_11_fnands.tif

proccessing .laz files with: `python main.py config/config.yml --tile-name FILENAME.laz`
processed files in `data/processed/dtm/`
processed .tif name format: `FILENAME_fnands_openai_optimised_02.tif`
