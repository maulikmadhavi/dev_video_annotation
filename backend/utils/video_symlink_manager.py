import os
import json
import logging
from pathlib import Path
import shutil

logger = logging.getLogger(__name__)


class VideoSymlinkManager:
    def __init__(self, annotation_file_path, videos_dir):
        self.annotation_file_path = annotation_file_path
        self.videos_dir = Path(videos_dir)

        # Ensure videos directory exists
        os.makedirs(self.videos_dir, exist_ok=True)

    def create_symlinks(self):
        """Create symbolic links for videos outside the videos directory"""
        try:
            with open(self.annotation_file_path, "r") as f:
                annotations = json.load(f)

            for video_path in annotations.keys():
                video_path = Path(video_path)

                # Skip if the video is already in the videos directory
                if self.videos_dir in Path(video_path).parents:
                    continue

                # Check if the video exists
                if not video_path.exists():
                    logger.warning(f"Video not found: {video_path}")
                    continue

                # Create symbolic link in videos directory
                symlink_path = self.videos_dir / video_path.name

                # Remove existing symlink if it exists
                if symlink_path.exists() or symlink_path.is_symlink():
                    if symlink_path.is_symlink():
                        symlink_path.unlink()
                    else:
                        # Check if it's a broken text file (from failed symlink attempt)
                        try:
                            if symlink_path.stat().st_size < 500:  # Small file, likely not a video
                                with open(symlink_path, 'r') as f:
                                    content = f.read()
                                    if content.startswith('/') and '\n' not in content:
                                        # It's a text file with a path, remove it
                                        symlink_path.unlink()
                                    else:
                                        logger.warning(f"File with same name already exists: {symlink_path}")
                                        continue
                            else:
                                logger.warning(f"File with same name already exists: {symlink_path}")
                                continue
                        except:
                            logger.warning(f"File with same name already exists: {symlink_path}")
                            continue

                # Try to create the symlink, fall back to copy if it fails
                try:
                    os.symlink(video_path, symlink_path)
                    logger.info(f"Created symlink: {symlink_path} -> {video_path}")
                except OSError as e:
                    # Symlink failed (common on Windows/WSL), try copying instead
                    logger.warning(f"Symlink failed, copying file instead: {e}")
                    try:
                        shutil.copy2(video_path, symlink_path)
                        logger.info(f"Copied file: {video_path} -> {symlink_path}")
                    except Exception as copy_error:
                        logger.error(f"Failed to copy file: {copy_error}")

            return True
        except Exception as e:
            logger.error(f"Error creating symlinks: {e}")
            return False
