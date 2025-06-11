# src/lidar_utils/io.py

import pathlib
import requests
import os
import yaml
import earthaccess
import logging
from typing import Optional, Union
from tqdm import tqdm

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
    filename: str,
    dest_dir: Union[str, pathlib.Path],
    verbose: bool = True,
    chunk_timeout: int = 5,
    overwrite: bool = False,
    token: Optional[str] = None,
    show_progress: bool = False,
) -> Optional[pathlib.Path]:
    """
    Download a LAZ file into dest_dir, if it doesn't already exist.

    Args:
        filename: Name of the file to download.
        dest_dir: Directory to save the file.
        verbose: Print status messages.
        chunk_timeout: Timeout (seconds) for each chunk.
        overwrite: If True, overwrite the file if it exists.
        token: Bearer token for authenticated requests.
        show_progress: If True, display tqdm progress bar.
            **Warning:** Enabling this adds one extra HEAD request to the server
            to get the file size (for progress reporting). If minimizing API calls is
            important (to avoid throttling), set show_progress=False to download
            without the size info, and only one GET request will be made.

    Returns:
        Path to downloaded file, or None on failure.
    """
    BASE_URL = "https://daac.ornl.gov/daacdata/cms/LiDAR_Forest_Inventory_Brazil/data"
    dest_dir = pathlib.Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename
    url = f"{BASE_URL}/{filename}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # Skip redundant download
    if dest_path.exists() and not overwrite:
        if verbose:
            print(f"[io] {filename} already exists in {dest_dir}, skipping download.")
        return dest_path

    if verbose:
        print(f"[io] Downloading {filename}...")

    # Get file size for progress bar, if requested
    total = None
    if show_progress:
        try:
            resp = requests.head(url, headers=headers, timeout=5)
            resp.raise_for_status()
            total = int(resp.headers.get('Content-Length', 0))
        except Exception:
            total = None  # Proceed without total file size

    try:
        with requests.get(url, stream=True, headers=headers, timeout=(5, chunk_timeout)) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                # Only show tqdm if show_progress is True and total is available
                use_tqdm = show_progress and (total is not None)
                progress = tqdm(
                    total=total, unit='B', unit_scale=True, 
                    disable=not use_tqdm, desc=filename
                )
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        if use_tqdm:
                            progress.update(len(chunk))
                if use_tqdm:
                    progress.close()

        if verbose:
            print(f"[io] Downloaded {filename} to {dest_path}")
        return dest_path
    except (KeyboardInterrupt, SystemExit):
        if dest_path.exists():
            dest_path.unlink()
        raise
    except Exception as exc:
        if dest_path.exists():
            dest_path.unlink()
        print(f"[io] Failed to download {filename}: {exc}")
        return None