# This script generates:
# 1. chunk_annotation.json - chunk-level annotations with labels per chunk
# 2. ground_truth.json - binary sequences (0/1) for each label per video
# Chunk duration is set as 10 seconds.

import json
import math
import os
from pathlib import Path

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    print("Warning: opencv-python not installed. Will estimate duration from annotations.")

CHUNK_DURATION = 10  # seconds
VIDEO_FOLDER = "videos"
IN_JSON = 'backend/data/annotation.json'
OUT_CHUNK_JSON = 'backend/data/chunk_annotation.json'
OUT_GROUND_TRUTH_JSON = 'backend/data/ground_truth.json'


def get_video_duration_cv2(video_path):
    """Get video duration using OpenCV."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return None
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return frame_count / fps if fps > 0 else None

def get_video_duration(video_path, annotations):
    """Get video duration from file, or estimate from annotations."""
    if HAS_CV2 and os.path.exists(video_path):
        duration = get_video_duration_cv2(video_path)
        if duration is not None:
            return duration
    else:
        print(f"Warning: Cannot access video file {video_path}. Estimating duration from annotations.")
        breakpoint()
    
    return max(ann['end_time'] for ann in annotations) if annotations else 0

def get_all_labels(annotation_data):
    """Get all unique labels across all videos."""
    labels = set()
    for annotations in annotation_data.values():
        for ann in annotations:
            labels.add(ann['label'])
    return sorted(list(labels))

def label_overlaps_chunk(annotations, label, chunk_start, chunk_end):
    """Check if a specific label overlaps with the given chunk."""
    for ann in annotations:
        if ann['label'] == label:
            if ann['start_time'] <= chunk_end and ann['end_time'] >= chunk_start:
                return True
    return False

def get_labels_for_chunk(annotations, chunk_start, chunk_end):
    """Get all labels that overlap with the given chunk time range."""
    labels = set()
    for ann in annotations:
        if ann['start_time'] <= chunk_end and ann['end_time'] >= chunk_start:
            labels.add(ann['label'])
    return sorted(list(labels))

def convert_to_chunk_annotations(annotation_data):
    """Convert time-stamp level annotations to chunk-level annotations."""
    chunk_annotations = {}
    
    for video_path, annotations in annotation_data.items():
        filename = os.path.basename(video_path)
        local_video_path = os.path.join(VIDEO_FOLDER, filename)
        duration = get_video_duration(local_video_path, annotations)
        num_chunks = math.ceil(duration / CHUNK_DURATION)
        
        video_chunks = []
        for i in range(num_chunks):
            chunk_start = i * CHUNK_DURATION
            chunk_end = (i + 1) * CHUNK_DURATION
            labels = get_labels_for_chunk(annotations, chunk_start, chunk_end)
            
            video_chunks.append({
                'chunk_index': i,
                'start_time': chunk_start,
                'end_time': chunk_end,
                'labels': labels
            })
        
        chunk_annotations[video_path] = video_chunks
    
    return chunk_annotations

def generate_ground_truth(annotation_data):
    """Generate ground truth with binary sequences for each label."""
    ground_truth = {}
    all_labels = get_all_labels(annotation_data)

    for video_path, annotations in annotation_data.items():
        filename = os.path.basename(video_path)
        local_video_path = os.path.join(VIDEO_FOLDER, filename)
        duration = get_video_duration(local_video_path, annotations)
        num_chunks = math.ceil(duration / CHUNK_DURATION)

        video_labels = {ann['label'] for ann in annotations}

        ground_truth[filename] = {
            'duration': duration,
            'total_num_chunks': num_chunks
        }

        for label in video_labels:
            binary_sequence = []
            for i in range(num_chunks):
                chunk_start = i * CHUNK_DURATION
                chunk_end = (i + 1) * CHUNK_DURATION

                if label_overlaps_chunk(annotations, label, chunk_start, chunk_end):
                    binary_sequence.append(1)
                else:
                    binary_sequence.append(0)

            ground_truth[filename][label] = binary_sequence

    return ground_truth


if __name__ == "__main__":
    # Read annotation file
    with open(IN_JSON, 'r') as f:
        annotation = json.load(f)

    # Generate chunk annotations
    chunk_annotations = convert_to_chunk_annotations(annotation)
    with open(OUT_CHUNK_JSON, 'w') as f:
        json.dump(chunk_annotations, f, indent=4)
    print(f"Chunk annotations saved to {OUT_CHUNK_JSON}")

    # Generate ground truth
    ground_truth = generate_ground_truth(annotation)
    with open(OUT_GROUND_TRUTH_JSON, 'w') as f:
        json.dump(ground_truth, f, indent=4)
    print(f"Ground truth saved to {OUT_GROUND_TRUTH_JSON}")

    print(f"\nProcessed {len(ground_truth)} videos")

    # Print summary
    for filename, data in ground_truth.items():
        print(f"\n{filename}:")
        print(f"  duration: {data['duration']}s, total_num_chunks: {data['total_num_chunks']}")
        for label, seq in data.items():
            if label not in ('duration', 'total_num_chunks'):
                print(f"  {label}: {seq} ({sum(seq)}/{len(seq)} chunks)")
