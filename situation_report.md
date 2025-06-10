## Stay on Track

- Week level goal:
- Month level goal: Win OpenAI to Z Kaggle competition

## Current Focus (What am I doing right now?)

- Working on notebook [Searching the Amazon with Remote Sensing 🛰️ and AI 🤖](https://www.kaggle.com/code/seamusbarnes/search-the-amazon-with-remote-sensing-and-ai/edit).

## Next Steps

- Run `rvt` using example notebooks (`/notebooks/rvt_py_examples/rvt_default_example.ipynb` and `/../../rvt_vis_example.ipynb`) on DTM from .laz file, alongside the DTM provided by `rvt` `/data/example/processed/TM1_564_146.tif`.
- Experiment with Kaggle notebook: [Search the Amazon with Remote Sensing and AI](https://www.kaggle.com/code/fnands/search-the-amazon-with-remote-sensing-and-ai) by Kaggle user FNANDS, which their custom dataset with processed DTM tiles: [NASA Amazon Lidar 2008-2018](https://www.kaggle.com/datasets/fnands/nasa-amazon-lidar-2008-2018/). Try to see if my DTM's look similar to theirs.

## Context

- Using conda environment named `openai_to_z`. Using jupyter kernel which points to this environment called `openai_to_z`.

## Open Questions

(B = bugs; Q = questions; F = features, D = documentation; R = refactor; M = miscellaneous)

- (F) Add purpose, status, next and conclusion tags to .ipynb files and miscellaneous .py files (but not `main.py` or `src/project_utils/*.py` which have their own docstrings). Write script to auto-generate \_notes.md with index of files and their tags. Discussion of feature with ChatGPT: [ChatGPT link](https://chatgpt.com/share/6846ce0d-555c-8005-bcee-3387602a0ef4).
- (B) Fix the bug in `satellite.fetch_esri_from_row()` whereby if the selected bounding box is too small, the request to `https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export` returns an error. Protect user from inputting a bounding box with minimum width < 120 m.
- (B) `lidar.get_laz_classification_counts()` is really slow for some reason.
- (M) The three most promising datasets:
  1. [LiDAR Surveys over Selected Forest Research Sites, Brazilian Amazon, 2008-2018](https://daac.ornl.gov/cgi-bin/dsviewer.pl?ds_id=1644) (Currently working with)
  2. [LiDAR and DTM Data from Forested Land Near Manaus, Amazonas, Brazil, 2008](LiDAR and DTM Data from Forested Land Near Manaus, Amazonas, Brazil, 2008).
  3. [CMS: LiDAR Data for Forested Areas in Paragominas, Para, Brazil, 2012-2014](https://daac.ornl.gov/CMS/guides/CMS_Landscapes_Brazil_LiDAR.html). LiDAR AND DTM files
- (F) Add tye-hints to my utils functions.

## Development Log

- _2025-06-10 (Tuesday)_ |
  1. Refactored lidar.laz_to_dtm so that it is robust to invalid json (pipeline definition template) which it can then convert to valid json for the pdal pipeline.
  2. Amended pdal pipeline definition so it includes smrf (simple morphological filter), Classification[2:2], and gdaldriver GTiff output. Also edited `notebooks/rvt_py_examples/rvt_default_example.ipynb` so it applies the different visualisations to the "correctly processed" DTM.
  3. Wrote `scratch/experimental_pdal_pipeline.ipynb` which successfully processes a .laz file by denoising and then converting to DTM, and then applies "manual" hill shade visualisation, reproducing the results of a good Kaggle notebook [🛰️Search the Amazon with Remote Sensing and AI🤖](https://www.kaggle.com/code/fnands/search-the-amazon-with-remote-sensing-and-ai).
- _2025-06-09 (Monday)_ |
  1. Wrote initial `situation_report.md`.
  2. Identified bug in `satellite.fetch_esri_from_row()` whereaby it returns error 500 from the server when the bounding box side length < 120 m.
- _2025-06-07/08_ |
  1. Partially re-wrote utils functions.
  2. Refactored and simplified main.ipynb into main.py, which now runs the entire pipeline from identify and download dataset metadata to processing a .laz file to a DTM using `new_dtm.json` pipeline definition.
  3. Wrote `/scratch/get_dataset_metadata.ipynb` which downloads all .laz files, extracts .laz metadata and saves it to .csv.
  4. Wrote `/scratch/analyse_metadata.ipynb` which shows cumulative plots of ground point percentage vs cumulative fraction of tiles, and attempts to download a high ground classification tiles (fails due to bug).
