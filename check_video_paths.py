#!/usr/bin/env python3

import json
import os
import glob
from pathlib import Path

# Path to the annotation JSON file
json_path = "/home/maulik/Documents/Tool/video_annotation_tool/backend/data/benchmark_annotation.json"

# Base video directory (extract from JSON paths)
video_base_dir = "/data/maulik/EXP/video_annotation/videos/"


def check_path_mismatches():
    # Load JSON data
    with open(json_path, "r", encoding="utf-8") as f:
        annotation_data = json.load(f)

    # Get all video paths from JSON
    json_video_paths = set(annotation_data.keys())
    print(f"Found {len(json_video_paths)} video paths in JSON file")

    # Get all actual video files from the filesystem
    video_extensions = ["*.mp4", "*.webm", "*.mkv", "*.avi"]
    fs_video_paths = set()

    # Check if base directory exists
    if not os.path.exists(video_base_dir):
        print(f"ERROR: Base video directory '{video_base_dir}' doesn't exist!")
        return

    # Collect video paths from filesystem
    for ext in video_extensions:
        found_files = glob.glob(os.path.join(video_base_dir, ext))
        for file_path in found_files:
            fs_video_paths.add(file_path)

    print(f"Found {len(fs_video_paths)} video files on filesystem")

    # Convert filesystem paths to match JSON format
    normalized_fs_paths = set()
    for fs_path in fs_video_paths:
        normalized_fs_paths.add(fs_path)

    # Find paths in JSON but not on filesystem
    missing_on_fs = json_video_paths - normalized_fs_paths
    if missing_on_fs:
        print("\nVideos in JSON but NOT found on filesystem:")
        for path in sorted(missing_on_fs):
            print(f"  - {path}")
    else:
        print("\nAll video paths in JSON exist on filesystem! ✓")

    # Find paths on filesystem but not in JSON
    missing_in_json = normalized_fs_paths - json_video_paths
    if missing_in_json:
        print("\nVideos on filesystem but NOT in JSON:")
        for path in sorted(missing_in_json):
            print(f"  - {path}")
        print(f"\nTotal videos missing from JSON: {len(missing_in_json)}")
    else:
        print("\nAll filesystem videos are in the JSON! ✓")

    # Check for case sensitivity or path normalization issues
    print("\nChecking for case sensitivity or path format issues...")
    potential_matches = []
    for json_path in missing_on_fs:
        json_path_lower = json_path.lower()
        for fs_path in missing_in_json:
            fs_path_lower = fs_path.lower()
            if os.path.basename(json_path_lower) == os.path.basename(fs_path_lower):
                potential_matches.append((json_path, fs_path))

    if potential_matches:
        print("\nPotential path format mismatches (same filename but different paths):")
        for json_p, fs_p in potential_matches:
            print(f"  JSON: {json_p}")
            print(f"    FS: {fs_p}")
            print()


if __name__ == "__main__":
    check_path_mismatches()
