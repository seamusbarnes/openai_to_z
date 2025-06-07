# Plan For How To Solve the Next Few Problems

## Single Goal

Process .laz tiles into DTM .geotif images, and process these DTM .geotif images into relief or hillshade visualisations.
Prejudice towards using pdal for .laz -> DTM processing and Relief Visualization Toolbox (`rvt_py`) for DTM -> visualizations.

## Current Status

I have experimented with processing the ORNL DAAC dataset [LiDAR Surveys over Selected Forest Research Sites, Brazilian Amazon, 2008-2018](https://daac.ornl.gov/CMS/guides/LiDAR_Forest_Inventory_Brazil.html). Structure:

1. Find dataset using doi (https://doi.org/10.3334/ORNLDAAC/1644).
   - `earthaccess.search_datasets(doi=doi)`
2. Download dataset metadata .csv file.
   - `earthaccess.download()`
3. Import dataset metadata .csv file into pandas dataframe (this is a len=3,154 row df with each row representing a particular .laz tile, with filename, coordinates, CRS information).
   - `pd.read_csv(csv_path)`
4. Use ESRI to download a satellite image for a particular tile.
   - `m = folium.Map(location=[centre_lat, centre_lon], zoom_start=17, tiles="Esri.WorldImagery")`
   - `requests.get()`, requires `url = "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"` and `params` which specify the bounding box, bboxSR, imageSR, size, format and f(?) (=image)
5. Download the .laz file.
   - Use requests.Session() with `base_url = "https://daac.ornl.gov/daacdata/cms/LiDAR_Forest_Inventory_Brazil/data/"` which is appended with the tile filename from the dataset metadata dataframe.
6. (Optional) Extract metadata from .laz file (e.g. number of points in each classification).
7. Process .laz file to .geotif DTM.
   - Define a pipeline_def.json and run it with `pdal`.
8. Process .geotif DTM to hillshade visualisation.
   - Use `rvt` (Relief Visualization Toolbox)

Directory structure:

```
.
├── LICENSE
├── README.md
├── client_secrets.json
├── config
│   ├── paths.yml
│   └── pdal_pipelines
│       ├── dsm_pipeline.json
│       └── dtm_pipeline.json
├── csf_ground.tif
├── data
│   ├── cms_brazil_lidar_tile_inventory.csv
│   ├── derived
│   │   ├── chm
│   │   ├── dsm
│   │   ├── dtm
│   │   └── hillshade
│   └── raw
│       ├── metadata
│       └── tiles
├── main
│   ├── config.yml
│   ├── environment.yml
│   └── main.py
├── mycreds.txt
├── notebooks
│   ├── 2018deSouza_create_geotiff.ipynb
│   ├── 2025_05_27_deSouza.ipynb
│   ├── create_dtm.ipynb
│   ├── data
│   ├── dataset_downloader_GEE.ipynb
│   ├── laz_to_dtm
│   │   ├── __pycache__
│   │   ├── pipeline_defs
│   │   ├── v01_archive.ipynb
│   │   ├── v02_sandbox.ipynb
│   │   ├── v03_batch_pipeline.ipynb
│   │   ├── v04_batch_pipeline.ipynb
│   │   └── v04_batch_pipeline.py
│   ├── pdal_test.ipynb
│   └── quick_gedi_o4.ipynb
├── openai_log.jsonl
├── plan.md
├── requirements.txt
└── src
    └── lidar_utils
        ├── __init__.py
        ├── __pycache__
        ├── geo.py
        ├── io.py
        ├── lidar.py
        ├── raster.py
        ├── satellite.py
        ├── setup.py
        └── vis.py

21 directories, 34 files
```

How do we come up with a minimalistic workflow to so I can do this from a main.py file, with CONFIG for all the different directory paths, and then point to src/lidar_utils/\*.py util files?
