# LiDAR + Satellite + Text + LLMs = Archaeology

**_A brand new technique for archeological research, combining LiDAR visualisations, satellite images, and 16th century biographies and LLMs_**

In this writeup, we present new techniques developed to process raw data from a range of domains (LiDAR, satellite and historical texts) using a combination of "traditional" deep-learning and "non-traditionl" LLM-driven methods, to give archaeologists new tools for making discoveries...

The work can be split into three main tracks:

1. LiDAR
2. Satellite
3. Textual data

### Kaggle Datasets:

#### LiDAR

- [LiDAR Survey of Brazil - .laz Metadata](https://www.kaggle.com/datasets/seamusbarnes/lidar-survey-of-brazil-laz-metadata)
  - Contents: LiDAR point-cloud metadata (for each tile, and for each class), original dataset inventory CSV, metadata for inventory CSV, and tile GPKG.
  - Purpose: This can be used for EDA of the LiDAR data, explaining the variation in LiDAR data quality and the problems we have to overcome to use it effectively.
  - STATUS: Documented, "finished"
- [LiDAR Survey of Brazil - Inventory File](https://www.kaggle.com/datasets/seamusbarnes/lidar-survey-of-brazil-inventory-file):
  - Contents: Original dataset inventory CSV
  - Purpose: This can be used in a Kaggle notebook to generate the point-cloud metadata dataset, for demonstration purposes.
  - STATUS: Documented, "finished"
- [LiDAR Survey of Brazil - .laz files - Subset](https://www.kaggle.com/datasets/seamusbarnes/lidar-survey-of-brazil-laz-files-subset)
  - Contents: Subset (37) of original LAZ files from dataset
  - Purpose: This can be used in a Kaggle notebook to demonstrate the LiDAR metadata extraction. The plan was to also use it to demonstrate the PDAL conversion to DTMs, but PDAL does not work on Kaggle.
  - STATUS: Documented, "finished"
- [Amazon LiDAR DTMs and VAT Visualisations](https://www.kaggle.com/datasets/seamusbarnes/amazon-lidar-dtms-generated-using-optimised-pdal)
  - Contents: 3,140 DTMs, processed through the PDAL pipeline (explained in the dataset "Data Card") and 3,140 VATs which were generated locally, but can also be generated on a Kaggle notebook for demonstration purposes.
  - Purpose: For use in down-stream inference, either with Matts ArchAI models, or using openai in a Kaggle notebook.
  - STATUS: Documented, "finished"
- [RVT Settings](https://www.kaggle.com/datasets/seamusbarnes/rvt-settings)
  - Contents: 6 JSON settings files
  - Purpose: These settings files are required by rvt_py to process DTMs into VATs, which is done in a Kaggle notebook.
  - STATUS: Not documented, needs documentation and link to Kaggle notebook where it is used.

#### Text

- [Historical Text dataset - Digitised](https://www.kaggle.com/datasets/seamusbarnes/amazon-historical-texts)
  - Contents: TXT data for the books "The expedition of Pedro de Ursua & Lope de Aguirre in search of El Dorado and Omagua in 1560-1" and "Up the Amazon and Madeira rivers, through Bolivia and Peru", and the GPKG for Amazonia Stricto.
  - Purpose: Required for processing in Kaggle notebook.
  - STATUS: Not documented
- [Historical Text Dataset - Scans](https://www.kaggle.com/datasets/seamusbarnes/orinoco-expedition-historical-text-dataset)
  - Contents: Scans of Orinoco Expedition book, and CSV of prompts/response/metadata for openai calls on the files.
  - Purpse: Scans used in demonstration of using openai to transcribe (digitise) and translate handwritten historical texts.
  - STATUS: Quite well documented. I still need to add the "Chandless - Ascent of the River Purus - 1866.pdf" and "Chandless - River Acquiry - Acre - 1866.pdf"
- [The Expedition of Pedro de Ursua: Amazon Location](https://www.kaggle.com/datasets/seamusbarnes/the-expedition-of-pedro-de-ursua-amazon-locations/data)
  - Contents: Two CSVs, one of the extracted sentences of the text, and one of the extracted locations in the text, with modern locations, text snippets, openai summary and whether the location is "lost". One HTML showing the interactive Folium map of the locations with the metadata.
  - Purpose: This dataset allows reproducibility, mapping, and simple extension (e.g. further LLM enrichment) in Kaggle or other environments that may have limited API quota or hardware.
  - STATUS: Documented, "finished"
- [The Expedition of Pedro de Ursua: Amazon Locations](https://www.kaggle.com/datasets/seamusbarnes/the-expedition-of-pedro-de-ursua-amazon-locations)
  - Contents: Location and openai response data from the digitised text.
  - Purpose: This can be used in a Kaggle notebook without reprocessing everything.
  - STATUS: Documented, "finished"

### Kaggle Notebooks:

#### LiDAR

- [LiDAR Survey of Brazil - .laz files -Gen. Metadata](https://www.kaggle.com/code/seamusbarnes/lidar-survey-of-brazil-laz-files-gen-metadata)
  - Contents: End-to-end processing of raw LiDAR .laz files to extract per-tile point-cloud metadata, statistics, scan angles, elevations, and spatial extents; exports both full and "tidy" summaries, plus GeoPackage polygons; includes code for group statistics and visual diagnostics.
  - Purpose: To demonstrate and document the raw LiDAR tile metadata extraction process, serving as an example workflow and the basis for generating downstream datasets.
  - STATUS: Documented, "finished"
- [LiDAR Metadata Processing and Visualisation](https://www.kaggle.com/code/seamusbarnes/lidar-metadata-processing-and-visualisation)
  - Contents: Exploratory data analysis of precomputed LiDAR metadata; includes ground point density plots, class statistics, distribution analysis, outlier detection, and interactive mapping; visualizes data quality and coverage.
  - Purpose: To help users understand the quality and characteristics of the LiDAR point cloud data, and to aid selection/filtering for downstream archaeological analysis.
  - STATUS: Documented, "finished"
- [Classify Archaeology on LiDAR data with Openai API](https://www.kaggle.com/code/seamusbarnes/classify-archaeology-on-lidar-data-with-openai-api)
  - Contents: Batch generation of VAT images from DTMs using RVT, followed by OpenAI API calls for automated image-based archaeological detection; includes prompt engineering, structured outputs, cost-tracking, and visualization.
  - Purpose: To test and prototype automated archaeological site detection in the Amazon from LiDAR-derived images using state-of-the-art LLM Vision models and structured outputs.
  - STATUS: Well documented, functional for both demo and batch; future extensions for pipeline automation possible.

#### Text

- [Analyse Locations in Historical Texts with openai](https://www.kaggle.com/code/seamusbarnes/analyse-locations-in-historical-texts-with-openai)
  - Contents: Loads, cleans, and tokenizes digitized Amazonian expedition texts; extracts and geocodes place names; uses OpenAI API for structured enrichment (modern name, confidence, lost guessing); interactive mapping of results.
  - Purpose: To demonstrate end-to-end LLM-assisted analysis of exploration narratives: extracting, validating, and georeferencing historical locations for spatial and archaeological research.
  - STATUS: Documented, functional and reproducible; can be extended with additional texts.
- [Handwriting Transcription with OpenAI](https://www.kaggle.com/code/seamusbarnes/handwriting-transcription-with-openai/notebook)
  - Contents: Presents a pipeline for transcribing and translating 18th-century Spanish colonial manuscript pages using GPT Vision models; displays images, prints LLM transcriptions and translations, and allows for batch or single-image operation.
  - Purpose: To demonstrate the use of latest LLM/vision models for robust, scalable transcription of complex historical handwriting, aiding rapid digitization and semantic analysis.
  - STATUS: Documented, works for provided samples; additional scans can be added as needed.
- [The Expedition of Pedro de Ursua - Code](https://www.kaggle.com/code/seamusbarnes/the-expedition-of-pedro-de-ursua-code)
  - Contents: Loads preprocessed data (sentences and location/respoonse metadata from openai calls) from the digitized text from the Amazonian expedition chronicled by Pedro de Ursua. Visualises the locations in Folium.
  - Purpose: To provide a reproducible, documented, and visually rich workflow for validating, and mapping historical locations in primary source narratives using a combination of NLP and LLM enrichment. Designed for use in both spatial history research and as a template for processing additional texts with minimal fuss.
  - STATUS: **Documented, tested, and fully functional in Kaggle.** Produces high-quality, color-coded maps and downloadable artifacts.
- [Analysing Locations from Historical Texts¶](https://www.kaggle.com/code/seamusbarnes/analysing-locations-from-historical-texts/notebook#Analysing-Locations-from-Historical-Texts)
  - Contents: The full workflow for processing digitised text, extracting locations, getting geocoordinates, making and loging openai api calls and plotting the folium map.
  - Purpose: Showing that we actually did the processing of the text that generated the Kaggle Dataset.
  - STATUS: BROKEN TO HELL! And I don't have time to refactor it nicely. Kaggle environments don't like the required spacy nlp package (`en_core_web_trf` transforemer-based NER required, which is hard to get working in the Kaggle environment)

_Team members:_

- Iris Kramer (ArchAI)
- Matt Painter (ArchAI)
- James Byers (Unaffiliated)
