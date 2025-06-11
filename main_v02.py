"""
main.py
"""

import os
import sys
import time
import argparse

import src.config as config
import src.satellite as satellite
import src.proj_io as proj_io
import src.lidar as lidar

# helper functions
def pt(msg=None):
    current_time = time.strftime("%H:%M:%S")
    if msg:
        print(f"{current_time}: {msg}")
    else:
        print(current_time)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", type=str)

    args = parser.parse_args()
    cfg = config.Config(args.config_file)
    for key, val in cfg.to_dict().items():
        print(f"{key}: {val}")