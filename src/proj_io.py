# src/lidar_utils/io.py

import pathlib
import requests
import os
import yaml
import earthaccess
import logging

def authenticate_earthaccess(verbose=True):
    """
    Authenticate with earthaccess and print the result.
    """
    if verbose:
        print("[io] Authenticating with earthaccess...")
        auth = earthaccess.login()
        print(f"[io] Authenticated: {auth.authenticated}")
    else:
        auth = earthaccess.login()
    return auth.authenticated

def load_paths_yaml(path_to_yaml, verbose=False):
    """
    Load YAML config file mapping path names to directories.
    Returns dictionary with pathlib.Path values.
    """
    print(f"[io] Loading YAML config: {path_to_yaml}")
    cfg = yaml.safe_load(pathlib.Path(path_to_yaml).read_text())
    paths = {k: pathlib.Path(v) for k, v in cfg.items()}
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)
    if verbose:
        print("[io] Paths loaded:")
        for k, v in paths.items():
            print(f"    {k:<10}: {v}")
    return paths

def get_metadata(doi="10.3334/ORNLDAAC/1644"):
    """
    Retrieve dataset metadata for the given DOI.
    """
    print(f"[io] Querying metadata for DOI {doi}")
    ds = earthaccess.search_datasets(doi=doi)
    if not ds:
        raise ValueError(f"No dataset found for DOI {doi}")
    print(f"[io] Found concept ID: {ds[0]['meta']['concept-id']}")
    return ds[0]

def download_earthaccess_dataset_csv(concept_id, dest, overwrite=False):
    """
    Download the product CSV for a dataset using earthaccess.
    """
    print(f"[io] Downloading dataset CSV for concept_id: {concept_id}")
    lATITUDE    = -9.8654
    LONGITUDE   = -57.6760
    DELTA       = 0.1
    bbox = (
        LONGITUDE - DELTA,
        lATITUDE - DELTA,
        LONGITUDE + DELTA,
        lATITUDE + DELTA
    )
    results = earthaccess.search_data(
        concept_id=concept_id,
        bounding_box=bbox,
        cloud_hosted=False,
    )
    if not results:
        raise RuntimeError("[io] No search results for the bounding box.")
    downloaded_paths = earthaccess.download(results[0], dest)[0]
    print(f"[io] CSV downloaded: {downloaded_paths}")
    return downloaded_paths

def fetch_laz_file(
        filename,
        dest_dir,
        verbose=True,
        chunk_timeout=5,
        overwrite=False):
    """
    Download a LAZ file into dest_dir, if it doesn't already exist.
    """
    BASE_URL = "https://daac.ornl.gov/daacdata/cms/LiDAR_Forest_Inventory_Brazil/data/"
    url = f"{BASE_URL}/{filename}"
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = pathlib.Path(dest_dir) / filename
    if dest_path.exists() and not overwrite:
        if verbose:
            print(f"[io] {filename} already exists in {dest_dir}, skipping download.")
        return dest_path

    print(f"[io] Downloading {filename}...")
    try:
        with requests.get(url, stream=True, timeout=(5, chunk_timeout)) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        if verbose:
            print(f"[io] Downloaded {filename} to {dest_path}")
        return dest_path
    except Exception as exc:
        print(f"[io] Failed to download {filename}: {exc}")
        return None