# openai_to_z

This repo can be used to download .laz files from the ORNL DAAC dataset [LiDAR Surveys over Selected Forest Research Sites, Brazilian Amazon, 2008-2018](https://daac.ornl.gov/CMS/guides/LiDAR_Forest_Inventory_Brazil.html) and run a pipeline to process them into DTMs using [PDAL (Point Data Abstraction Library)](https://pdal.io/en/stable/).

## Quick Start

## Repo Structure

- data

  - example

    - `TM1_564_146.tif`: RVT_py example DTM used in example notebook
    - `TM1_564_146_nodata.tif`: RVT_py example DTM used in example notebook
    - `sinthetic_dem15_0.50_all.tif`: RVT_py example DTM used in example notebook
    - `synthetic_dem15_0.50.tif`: RVT_py example DTM used in example notebook
    - `RIB_A01_2014_laz_2.laz`: tile [fnands](https://www.kaggle.com/fnands) used to generate an example hillshade visualisation. The tile appears to show a square man-made site (~10 m diameter?) and a banked road leading to it
    - `RIB_A01_2014_laz_2_hillshade.png`: hillshade example made by [fnands](https://www.kaggle.com/fnands)

  - metadata

    - `cms_brazil_lidar_tile_metadata.csv` (metadata for 3,146/3,152 tiles. Each row corresponds to a specific tile. "filename" can be used to download the .laz file. Contains point-cloud metadata (e.g. number of points, number of points in each classification, percentage of poits in each classification, tile area). Also includes tile coordinates and SRS.

  - processed
    - dir for processed data (DTMs, denoised DTMs)
  - raw
    - dir for raw .laz and satellite data
  - visualisations
    - dir for visualisations (e.g. hillshade, VAT etc.)

- main
  - pdal_templates
    - TEMPLATES
    - `config.yml`: configuration of full pipeline run, including paths to raw data, processed data, pdal_template data and log data, and filenames of pdal_templates used.
    - `main.py`: CLI executable script for running pipeline
- `environment.yml`: conda environment package dependencies
- `README.md`

## Top-level Pipeline description

0. .laz point-cloud metadata:
   - Classification 2 (ground) points are a small percentage of all points (mean = 3.2 %; std. = 4.7 %)
   - All points point density is high (mean = 27.9 points per m2; std. = 34.1 points per m2)
   - Classification 2 point density is low (mean = 0.6 classification 2 points per m2; std. = 0.7 classification 2 points per m2
1. Process .laz file to DTM using the following pdil pipelines:

   - Denoise

   ```json
   {
     "pipeline": [
       {
         "type": "readers.las",
         "filename": "{in_laz}"
       },
       {
         "type": "filters.outlier",
         "method": "statistical",
         "mean_k": 8,
         "multiplier": 3.0
       },
       {
         "type": "filters.smrf",
         "ignore": "Classification[7:7]"
       },
       {
         "type": "filters.expression",
         "expression": "Classification == 2"
       },
       {
         "type": "writers.copc",
         "filename": "{out_laz}"
       }
     ]
   }
   ```

   - Generate DTM

   ```json
   {
     "pipeline": [
       {
         "type": "readers.las",
         "filename": "{in_laz}"
       },
       {
         "filename": "{out_tif}",
         "gdaldriver": "GTiff",
         "output_type": "min",
         "resolution": "2.0",
         "type": "writers.gdal"
       }
     ]
   }
   ```

2. Post-processing
   - Normalise DEM for colour image (remove outliers below 2nd percentile and above 98th percentile)
   - Generate hillshade
3. Results: Normalised DEM and hillshade visualisation
   - Example DTM: `SFX_A01_2012_laz_1.laz_denoised_tutorial_denoise_ground.tif`
   - Example DTM (post-processed): `example_dtm_highres.png`
   - Example hillshade: `example_hillshade_highres.png`
