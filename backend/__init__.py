"""
Multi-Platform E-commerce Product Listing Automation
===================================================

A comprehensive automation system for streamlining product listings
across Meesho, Flipkart, and Myntra platforms.

Key Features:
- Unified data entry form for all platforms
- SKU-based image management
- Automatic variant generation for bangles
- Excel export for Myntra
- Browser automation for Flipkart/Meesho
- Image folder archiving after successful listing

Author: E-commerce Automation Team
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "E-commerce Automation Team"

# Import core modules
from .data_models import Product, ProductVariant, Platform
from .image_manager import fetch_images, archive_images, validate_image_folder
from .myntra_export import generate_myntra_excel, upload_myntra_bulk

# Platform constants
SUPPORTED_PLATFORMS = ["meesho", "flipkart", "myntra"]
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"]
MAX_IMAGES_PER_PRODUCT = 10

# Default configuration
DEFAULT_CONFIG = {
    "images_root": "images/",
    "archive_root": "listing_done/",
    "temp_root": "temp/",
    "exports_root": "exports/",
    "max_variants": 10,
    "bangle_sizes": ["2.4", "2.6", "2.8"],
    "required_fields": {
        "meesho": ["product_name", "brand", "sku", "mrp", "selling_price"],
        "flipkart": ["product_name", "brand", "sku", "mrp", "selling_price", "hsn_code"],
        "myntra": ["product_name", "brand", "sku", "mrp", "selling_price", "material", "color"]
    }
}

def get_version():
    """Return the current version of the automation system."""
    return __version__

def get_supported_platforms():
    """Return list of supported e-commerce platforms."""
    return SUPPORTED_PLATFORMS.copy()

def validate_environment():
    """Validate that the environment is properly set up."""
    import os
    from pathlib import Path

    # Check required directories
    required_dirs = ["images", "listing_done", "temp", "exports"]
    for dir_name in required_dirs:
        Path(dir_name).mkdir(exist_ok=True)

    # Check Python version
    import sys
    if sys.version_info < (3, 7):
        raise RuntimeError("Python 3.7 or higher is required")

    return True

# Initialize on import
validate_environment()
