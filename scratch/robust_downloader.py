import logging
import os
import time
import requests
import threading

DOWNLOAD_DIR = "orders/81ce00904539eeebe5aaaa727b279567/LiDAR_Forest_Inventory_Brazil/data"
URLS_FILE = "urls.txt"
NUM_THREADS = 10

# Configure logging to both file and console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    handlers=[
        logging.FileHandler("log.txt", mode='a'),
        logging.StreamHandler()
    ]
)

def sizeof_fmt(num, suffix='B'):
    for unit in ['','K','M','G','T']:
        if abs(num) < 1024.0:
            return f"{num:.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}P{suffix}"

def get_local_path(url):
    fname = url.split("/")[-1]
    return os.path.join(DOWNLOAD_DIR, fname)

def download_with_resume(url):
    local_path = get_local_path(url)
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    headers = {}
    mode = "wb"

    # Determine file size, local size
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

    # Download with retry for broken connections
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
            mode = "ab"  # Always append after first partial
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

def worker(urls):
    for url in urls:
        try:
            download_with_resume(url)
        except Exception as e:
            logging.info(f"UNCAUGHT ERROR {url}: {e}")

def main():
    with open(URLS_FILE) as f:
        urls = [line.strip() for line in f if line.strip()]
    batches = [urls[i::NUM_THREADS] for i in range(NUM_THREADS)]
    threads = []
    t_start = time.time()
    for batch in batches:
        t = threading.Thread(target=worker, args=(batch,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    t_total = time.time() - t_start
    logging.info(f"All downloads done. Total wall time: {t_total:.2f}s")

if __name__ == "__main__":
    main()