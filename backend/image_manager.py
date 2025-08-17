"""
Image Management System for SKU-based Product Images
===================================================

Handles automatic image retrieval from SKU folders and archiving
after successful product listing.
"""

import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os
import json


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default paths - can be overridden
IMAGES_ROOT = Path("images")
ARCHIVE_ROOT = Path("listing_done")
TEMP_ROOT = Path("temp")

# Supported image formats
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}

# Image naming conventions for different platforms
IMAGE_NAMING_CONVENTIONS = {
    'front': ['front', 'main', '1', 'primary'],
    'side': ['side', 'profile', '2'],
    'back': ['back', 'rear', '3'],
    'closeup': ['closeup', 'detail', 'zoom', '4'],
    'model': ['model', 'worn', 'lifestyle', '5'],
    'packaging': ['packaging', 'box', 'pack', '6']
}


class ImageManager:
    """Manages product images based on SKU folder structure."""

    def __init__(self, images_root: Path = None, archive_root: Path = None):
        """Initialize ImageManager with custom paths if provided."""
        self.images_root = Path(images_root) if images_root else IMAGES_ROOT
        self.archive_root = Path(archive_root) if archive_root else ARCHIVE_ROOT

        # Ensure directories exist
        self.images_root.mkdir(exist_ok=True)
        self.archive_root.mkdir(exist_ok=True)

        logger.info(f"ImageManager initialized - Images: {self.images_root}, Archive: {self.archive_root}")

    def validate_image_folder(self, sku: str) -> Dict[str, any]:
        """
        Validate that the image folder exists and contains valid images.

        Returns:
            Dict with validation results and metadata
        """
        folder = self.images_root / sku
        result = {
            'sku': sku,
            'folder_exists': False,
            'image_count': 0,
            'valid_images': [],
            'invalid_files': [],
            'missing_types': [],
            'folder_path': str(folder),
            'status': 'invalid'
        }

        if not folder.exists():
            result['error'] = f"Image folder not found for SKU: {sku}"
            logger.warning(f"Image folder missing: {folder}")
            return result

        result['folder_exists'] = True

        # Get all files in the folder
        all_files = list(folder.iterdir())

        for file_path in all_files:
            if file_path.is_file():
                if file_path.suffix.lower() in SUPPORTED_FORMATS:
                    result['valid_images'].append({
                        'name': file_path.name,
                        'path': str(file_path),
                        'size': file_path.stat().st_size,
                        'type': self._classify_image_type(file_path.name)
                    })
                else:
                    result['invalid_files'].append(file_path.name)

        result['image_count'] = len(result['valid_images'])

        # Check for required image types
        found_types = {img['type'] for img in result['valid_images']}
        required_types = {'front'}  # At minimum, front image is required
        result['missing_types'] = list(required_types - found_types)

        # Determine overall status
        if result['image_count'] >= 1 and not result['missing_types']:
            result['status'] = 'valid'
        elif result['image_count'] >= 1:
            result['status'] = 'warning'  # Has images but missing some types
        else:
            result['status'] = 'invalid'

        return result

    def fetch_images(self, sku: str, sort_by_type: bool = True) -> List[Path]:
        """
        Get all image paths for the given SKU, sorted by importance.

        Args:
            sku: Product SKU
            sort_by_type: If True, sort images by type (front, side, etc.)

        Returns:
            List of Path objects for valid images

        Raises:
            FileNotFoundError: If folder doesn't exist
            ValueError: If no valid images found
        """
        folder = self.images_root / sku

        if not folder.exists():
            raise FileNotFoundError(f"Image folder not found for SKU: {sku}")

        # Get all valid image files
        image_files = []
        for file_path in folder.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_FORMATS:
                image_files.append(file_path)

        if not image_files:
            raise ValueError(f"No valid images found in folder for SKU: {sku}")

        if sort_by_type:
            image_files = self._sort_images_by_type(image_files)
        else:
            image_files.sort()  # Sort alphabetically

        logger.info(f"Found {len(image_files)} images for SKU: {sku}")
        return image_files

    def fetch_images_by_type(self, sku: str) -> Dict[str, Path]:
        """
        Get images organized by type (front, side, back, etc.).

        Returns:
            Dictionary mapping image types to file paths
        """
        images = self.fetch_images(sku)
        result = {}

        for image_path in images:
            image_type = self._classify_image_type(image_path.name)
            if image_type not in result:  # Only keep the first image of each type
                result[image_type] = image_path

        return result

    def archive_images(self, sku: str) -> bool:
        """
        Move the entire SKU folder from images/ to listing_done/.

        Args:
            sku: Product SKU

        Returns:
            True if successful, False otherwise
        """
        src_folder = self.images_root / sku
        dst_folder = self.archive_root / sku

        if not src_folder.exists():
            logger.error(f"Source folder does not exist: {src_folder}")
            return False

        try:
            # Create destination parent directory if it doesn't exist
            dst_folder.parent.mkdir(parents=True, exist_ok=True)

            # If destination already exists, add timestamp
            if dst_folder.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dst_folder = self.archive_root / f"{sku}_{timestamp}"

            # Move the folder
            shutil.move(str(src_folder), str(dst_folder))

            # Create a metadata file
            metadata = {
                'sku': sku,
                'archived_at': datetime.now().isoformat(),
                'original_path': str(src_folder),
                'archived_path': str(dst_folder)
            }

            metadata_file = dst_folder / '.metadata.json'
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Successfully archived images for SKU: {sku} to {dst_folder}")
            return True

        except Exception as e:
            logger.error(f"Failed to archive images for SKU {sku}: {str(e)}")
            return False

    def restore_images(self, sku: str) -> bool:
        """
        Restore images from listing_done/ back to images/ folder.
        Useful for re-listing failed products.

        Args:
            sku: Product SKU

        Returns:
            True if successful, False otherwise
        """
        archived_folder = self.archive_root / sku
        restore_folder = self.images_root / sku

        if not archived_folder.exists():
            logger.error(f"Archived folder does not exist: {archived_folder}")
            return False

        if restore_folder.exists():
            logger.warning(f"Destination folder already exists: {restore_folder}")
            return False

        try:
            shutil.move(str(archived_folder), str(restore_folder))
            logger.info(f"Successfully restored images for SKU: {sku}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore images for SKU {sku}: {str(e)}")
            return False

    def copy_images_to_temp(self, sku: str, platform: str = None) -> Path:
        """
        Copy images to a temporary folder for processing.
        Useful for platform-specific image processing.

        Args:
            sku: Product SKU
            platform: Optional platform name for subfolder

        Returns:
            Path to temporary folder containing copied images
        """
        images = self.fetch_images(sku)

        # Create temp subfolder
        temp_folder = TEMP_ROOT / platform / sku if platform else TEMP_ROOT / sku
        temp_folder.mkdir(parents=True, exist_ok=True)

        # Copy images
        for image_path in images:
            dst_path = temp_folder / image_path.name
            shutil.copy2(image_path, dst_path)

        logger.info(f"Copied {len(images)} images to temp folder: {temp_folder}")
        return temp_folder

    def get_folder_status(self, sku: str) -> str:
        """
        Get the current status of a SKU's image folder.

        Returns:
            'active', 'archived', or 'missing'
        """
        if (self.images_root / sku).exists():
            return 'active'
        elif (self.archive_root / sku).exists():
            return 'archived'
        else:
            return 'missing'

    def list_all_skus(self) -> Dict[str, str]:
        """
        List all SKUs and their current status.

        Returns:
            Dictionary mapping SKU to status ('active' or 'archived')
        """
        skus = {}

        # Check active folders
        if self.images_root.exists():
            for folder in self.images_root.iterdir():
                if folder.is_dir():
                    skus[folder.name] = 'active'

        # Check archived folders
        if self.archive_root.exists():
            for folder in self.archive_root.iterdir():
                if folder.is_dir() and folder.name not in skus:
                    skus[folder.name] = 'archived'

        return skus

    def cleanup_temp_folders(self, older_than_hours: int = 24):
        """
        Clean up temporary folders older than specified hours.

        Args:
            older_than_hours: Remove temp folders older than this many hours
        """
        if not TEMP_ROOT.exists():
            return

        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)

        for item in TEMP_ROOT.iterdir():
            if item.is_dir():
                if item.stat().st_mtime < cutoff_time:
                    try:
                        shutil.rmtree(item)
                        logger.info(f"Cleaned up temp folder: {item}")
                    except Exception as e:
                        logger.error(f"Failed to clean up {item}: {str(e)}")

    def _classify_image_type(self, filename: str) -> str:
        """
        Classify image type based on filename.

        Args:
            filename: Name of the image file

        Returns:
            Image type ('front', 'side', 'back', etc.)
        """
        filename_lower = filename.lower()

        for image_type, keywords in IMAGE_NAMING_CONVENTIONS.items():
            for keyword in keywords:
                if keyword in filename_lower:
                    return image_type

        return 'other'  # Default type

    def _sort_images_by_type(self, image_paths: List[Path]) -> List[Path]:
        """
        Sort images by importance (front first, then side, back, etc.).

        Args:
            image_paths: List of image file paths

        Returns:
            Sorted list of image paths
        """
        type_priority = ['front', 'side', 'back', 'closeup', 'model', 'packaging', 'other']

        def get_priority(image_path):
            image_type = self._classify_image_type(image_path.name)
            try:
                return type_priority.index(image_type)
            except ValueError:
                return len(type_priority)  # Put unknown types at the end

        return sorted(image_paths, key=get_priority)


# Convenience functions for backward compatibility
def fetch_images(sku: str) -> List[Path]:
    """Fetch images for SKU using default ImageManager."""
    manager = ImageManager()
    return manager.fetch_images(sku)


def archive_images(sku: str) -> bool:
    """Archive images for SKU using default ImageManager."""
    manager = ImageManager()
    return manager.archive_images(sku)


def validate_image_folder(sku: str) -> Dict[str, any]:
    """Validate image folder for SKU using default ImageManager."""
    manager = ImageManager()
    return manager.validate_image_folder(sku)


# For testing and demonstration
if __name__ == "__main__":
    # Create sample folder structure for testing
    sample_sku = "TEST123"
    sample_folder = IMAGES_ROOT / sample_sku
    sample_folder.mkdir(parents=True, exist_ok=True)

    # Create dummy image files for testing
    dummy_files = ["front.jpg", "side.jpg", "back.png", "model.jpeg"]
    for filename in dummy_files:
        dummy_file = sample_folder / filename
        dummy_file.write_text("dummy image content")

    # Test the ImageManager
    manager = ImageManager()

    print(f"Testing with SKU: {sample_sku}")

    # Test validation
    validation = manager.validate_image_folder(sample_sku)
    print(f"Validation result: {validation}")

    # Test fetching images
    try:
        images = manager.fetch_images(sample_sku)
        print(f"Found images: {[img.name for img in images]}")

        # Test fetching by type
        images_by_type = manager.fetch_images_by_type(sample_sku)
        print(f"Images by type: {images_by_type}")

        # Test archiving
        success = manager.archive_images(sample_sku)
        print(f"Archiving successful: {success}")

    except Exception as e:
        print(f"Error: {e}")

    # List all SKUs
    all_skus = manager.list_all_skus()
    print(f"All SKUs: {all_skus}")
