"""
Robust Multi-threaded Downloader with Resume Support

This script downloads a list of files from URLs (e.g., NASA Earth observation data) 
in a highly robust, resumable, and multi-threaded manner. It supports automatic retries, 
logging, partial/resumed downloads, and customizable parameters.

Parameters (via command line):
    --download_dir: Target directory where files will be downloaded.
    --urls_file:    Path to a text file containing URLs (one per line).
    --num_threads:  Number of worker threads for parallel downloads.

Usage:
    python downloader.py --download_dir ./my_data --urls_file urls.txt --num_threads 8

Dependencies:
    requests

Example:
    $ python downloader.py --download_dir "downloads" --urls_file "nasa_urls.txt" --num_threads 12

Logging:
    Logs are streamed to both 'log.txt' (file) and STDOUT (console).
"""

import logging
import os
import time
import requests
import threading
import argparse

def sizeof_fmt(num, suffix='B'):
    """
    Converts a file size in bytes to a human-readable string (e.g., 10.3M).
    """
    for unit in ['','K','M','G','T']:
        if abs(num) < 1024.0:
            return f"{num:.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}P{suffix}"

def get_local_path(url, download_dir):
    """
    Given a URL and download directory, return the target local file path.
    """
    fname = url.split("/")[-1]
    return os.path.join(download_dir, fname)

def download_with_resume(url, download_dir):
    """
    Downloads a file from the specified URL to the given download_dir.
    Supports resuming partial/incomplete downloads and retries upon failures.

    Args:
        url (str): The remote file URL.
        download_dir (str): Local target directory for the download.
    """
    local_path = get_local_path(url, download_dir)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    headers = {}
    mode = "wb"

    try:
        head = requests.head(url, allow_redirects=True)
        file_size = int(head.headers.get("Content-Length", 0))
    except Exception as e:
        logging.info(f"HEAD failed for {url}: {e}")
        return

    if os.path.exists(local_path):
        local_size = os.path.getsize(local_path)
        if file_size and local_size >= file_size:
            logging.info(f"Already downloaded {os.path.basename(local_path)}, skipping.")
            return
        headers["Range"] = f"bytes={local_size}-"
        mode = "ab"
    else:
        local_size = 0

    logging.info(f"Downloading {os.path.basename(local_path)} (total {sizeof_fmt(file_size)}) starting at {sizeof_fmt(local_size)}")

    max_retries = 5
    attempt = 0
    success = False
    bytes_downloaded = local_size
    start_time = time.time()
    while attempt < max_retries and not success:
        try:
            with requests.get(url, headers=headers, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(local_path, mode) as f:
                    for chunk in r.iter_content(chunk_size=1024*1024):
                        if chunk:
                            f.write(chunk)
                            bytes_downloaded += len(chunk)
            success = True
        except (requests.exceptions.RequestException, OSError) as e:
            attempt += 1
            logging.info(f"Connection broken while downloading {os.path.basename(local_path)} (attempt {attempt}), will retry. Error: {e}")
            time.sleep(5)
            mode = "ab"
            if os.path.exists(local_path):
                bytes_downloaded = os.path.getsize(local_path)
            headers["Range"] = f"bytes={bytes_downloaded}-"

    elapsed = time.time() - start_time
    if success:
        speed = bytes_downloaded - local_size
        if elapsed > 0:
            speed /= elapsed
        logging.info(f"Finished: {os.path.basename(local_path)} ({sizeof_fmt(bytes_downloaded)}) in {elapsed:.2f}s, avg speed {sizeof_fmt(speed)}/s")
    else:
        logging.info(f"FAILED: {os.path.basename(local_path)} after {max_retries} attempts.")

def worker(urls, download_dir):
    """
    Worker function for thread: downloads all URLs in its batch.
    """
    for url in urls:
        try:
            download_with_resume(url, download_dir)
        except Exception as e:
            logging.info(f"UNCAUGHT ERROR {url}: {e}")

def parse_args():
    """
    Parse command-line arguments for download directory, URLs file, and number of threads.
    """
    parser = argparse.ArgumentParser(description="Robust Multi-threaded Downloader for batch URL lists.")
    parser.add_argument('--download_dir', default="downloads", help="Download directory (default: ./downloads)")
    parser.add_argument('--urls_file', default="urls.txt", help="Text file with URLs (one per line)")
    parser.add_argument('--num_threads', type=int, default=10, help="Number of download threads (default: 10)")
    return parser.parse_args()

def main():
    """
    Main program flow: parse args, configure logging, spawn threads, and monitor progress.
    """
    args = parse_args()

    # Configure logging to file + console
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(message)s",
        handlers=[
            logging.FileHandler("log.txt", mode='a'),
            logging.StreamHandler()
        ]
    )

    if not os.path.exists(args.urls_file):
        print(f"URL file '{args.urls_file}' not found!")
        return

    with open(args.urls_file) as f:
        urls = [line.strip() for line in f if line.strip()]
    if not urls:
        logging.info("No URLs found to download!")
        return

    batches = [urls[i::args.num_threads] for i in range(args.num_threads)]
    threads = []
    t_start = time.time()
    for batch in batches:
        t = threading.Thread(target=worker, args=(batch, args.download_dir))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    t_total = time.time() - t_start
    logging.info(f"All downloads done. Total wall time: {t_total:.2f}s")

if __name__ == "__main__":
    main()