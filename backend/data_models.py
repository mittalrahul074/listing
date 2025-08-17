"""
Data Models for Multi-Platform Product Listing
==============================================

Defines the core data structures for products and platform-specific requirements.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class Platform(Enum):
    """Supported e-commerce platforms."""
    MEESHO = "meesho"
    FLIPKART = "flipkart"
    MYNTRA = "myntra"


class ProductType(Enum):
    """Types of jewelry products."""
    NECKLACE = "necklace"
    BANGLE = "bangle"
    CHAIN = "chain"
    EARRING = "earring"
    RING = "ring"
    BRACELET = "bracelet"


class Material(Enum):
    """Base materials for jewelry."""
    GOLD = "gold"
    SILVER = "silver"
    BRASS = "brass"
    ALLOY = "alloy"
    COPPER = "copper"
    STAINLESS_STEEL = "stainless_steel"


@dataclass
class ProductVariant:
    """Represents a product variant (e.g., different sizes of bangles)."""
    sku: str
    size: str
    inventory: int = 0
    additional_attributes: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.sku:
            raise ValueError("SKU is required for product variant")


@dataclass
class Product:
    """Main product data model containing all platform requirements."""

    # Basic Information
    product_name: str
    brand: str
    sku: str
    product_type: ProductType
    description: str = ""

    # Pricing
    mrp: float = 0.0
    selling_price: float = 0.0

    # Physical Properties
    material: Material = Material.ALLOY
    color: str = ""
    plating: str = ""
    base_metal: str = ""
    stone_type: str = ""
    net_weight: float = 0.0
    gross_weight: float = 0.0

    # Dimensions
    size: str = ""
    length: str = ""
    width: str = ""
    height: str = ""

    # Classification
    gender: str = "Women"
    article_type: str = ""
    category: str = "Jewelry"
    subcategory: str = ""

    # Business Details
    hsn_code: str = ""
    gst_applicable: bool = True
    inventory: int = 0

    # Marketing
    search_tags: List[str] = field(default_factory=list)
    occasion: str = ""
    trend: str = ""
    collection: str = ""
    season: str = ""
    year: str = str(datetime.now().year)

    # Packaging & Origin
    country_of_origin: str = "India"
    manufacturer: str = ""
    packer: str = ""
    importer: str = ""

    # Fulfillment
    fulfillment_by: str = "seller"
    procurement_type: str = "regular"
    shipping_provider: str = ""

    # Additional attributes
    warranty: str = ""
    certification: str = ""
    care_instructions: str = ""

    # Variants (for products like bangles with multiple sizes)
    variants: List[ProductVariant] = field(default_factory=list)

    # Images
    image_folder: str = ""  # SKU-based folder name

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """Validate product data after initialization."""
        if not self.product_name:
            raise ValueError("Product name is required")
        if not self.brand:
            raise ValueError("Brand is required")
        if not self.sku:
            raise ValueError("SKU is required")

        # Set image folder to SKU if not provided
        if not self.image_folder:
            self.image_folder = self.sku

        # Auto-generate variants for bangles if not provided
        if self.product_type == ProductType.BANGLE and not self.variants:
            self.generate_bangle_variants()

    def generate_bangle_variants(self, sizes: List[str] = None):
        """Generate standard bangle size variants."""
        if sizes is None:
            sizes = ["2.4", "2.6", "2.8"]

        self.variants = []
        for size in sizes:
            variant_sku = f"{self.sku}-{size.replace('.', '')}"
            self.variants.append(ProductVariant(
                sku=variant_sku,
                size=f"{size} inches",
                inventory=self.inventory
            ))

    def add_variant(self, size: str, inventory: int = 0, **kwargs):
        """Add a custom variant to the product."""
        variant_sku = f"{self.sku}-{size.replace(' ', '').replace('.', '')}"
        variant = ProductVariant(
            sku=variant_sku,
            size=size,
            inventory=inventory,
            additional_attributes=kwargs
        )
        self.variants.append(variant)

    def get_all_skus(self) -> List[str]:
        """Get all SKUs including variants."""
        skus = [self.sku]
        skus.extend([variant.sku for variant in self.variants])
        return skus

    def to_dict(self) -> Dict[str, Any]:
        """Convert product to dictionary for JSON serialization."""
        return {
            'product_name': self.product_name,
            'brand': self.brand,
            'sku': self.sku,
            'product_type': self.product_type.value,
            'description': self.description,
            'mrp': self.mrp,
            'selling_price': self.selling_price,
            'material': self.material.value,
            'color': self.color,
            'plating': self.plating,
            'base_metal': self.base_metal,
            'stone_type': self.stone_type,
            'net_weight': self.net_weight,
            'gross_weight': self.gross_weight,
            'size': self.size,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'gender': self.gender,
            'article_type': self.article_type,
            'category': self.category,
            'subcategory': self.subcategory,
            'hsn_code': self.hsn_code,
            'gst_applicable': self.gst_applicable,
            'inventory': self.inventory,
            'search_tags': self.search_tags,
            'occasion': self.occasion,
            'trend': self.trend,
            'collection': self.collection,
            'season': self.season,
            'year': self.year,
            'country_of_origin': self.country_of_origin,
            'manufacturer': self.manufacturer,
            'packer': self.packer,
            'importer': self.importer,
            'fulfillment_by': self.fulfillment_by,
            'procurement_type': self.procurement_type,
            'shipping_provider': self.shipping_provider,
            'warranty': self.warranty,
            'certification': self.certification,
            'care_instructions': self.care_instructions,
            'variants': [{'sku': v.sku, 'size': v.size, 'inventory': v.inventory} for v in self.variants],
            'image_folder': self.image_folder,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def validate_for_platform(self, platform: Platform) -> List[str]:
        """Validate product data for specific platform requirements."""
        errors = []

        # Common validations
        if not self.product_name:
            errors.append("Product name is required")
        if not self.brand:
            errors.append("Brand is required")
        if not self.sku:
            errors.append("SKU is required")
        if self.mrp <= 0:
            errors.append("MRP must be greater than 0")
        if self.selling_price <= 0:
            errors.append("Selling price must be greater than 0")

        # Platform-specific validations
        if platform == Platform.FLIPKART:
            if not self.hsn_code:
                errors.append("HSN code is required for Flipkart")
            if len(self.hsn_code) not in [4, 6, 8]:
                errors.append("HSN code must be 4, 6, or 8 digits")

        elif platform == Platform.MYNTRA:
            if not self.material:
                errors.append("Material is required for Myntra")
            if not self.color:
                errors.append("Color is required for Myntra")
            if not self.article_type:
                errors.append("Article type is required for Myntra")

        elif platform == Platform.MEESHO:
            if not self.category:
                errors.append("Category is required for Meesho")

        return errors


@dataclass
class PlatformMapping:
    """Maps product fields to platform-specific field names."""

    # Field mappings for each platform
    MEESHO_FIELDS = {
        'product_name': 'Product Name',
        'brand': 'Brand',
        'sku': 'SKU',
        'mrp': 'MRP',
        'selling_price': 'Selling Price',
        'description': 'Description',
        'category': 'Category',
        'material': 'Material',
        'color': 'Color',
        'inventory': 'Inventory'
    }

    FLIPKART_FIELDS = {
        'product_name': 'product_name',
        'brand': 'brand',
        'sku': 'fsn_sku',
        'mrp': 'mrp',
        'selling_price': 'selling_price',
        'description': 'description',
        'hsn_code': 'hsn',
        'material': 'material',
        'color': 'color',
        'inventory': 'inventory',
        'length': 'length',
        'width': 'width',
        'height': 'height'
    }

    MYNTRA_FIELDS = {
        'product_name': 'Product Name',
        'brand': 'Brand Name',
        'sku': 'Style ID',
        'mrp': 'MRP',
        'selling_price': 'Best Price',
        'description': 'Product Details',
        'material': 'Primary Material',
        'color': 'Brand Color',
        'article_type': 'Article Type',
        'season': 'Season',
        'year': 'Year',
        'collection': 'Collection',
        'inventory': 'Inventory',
        'net_weight': 'Net Weight',
        'gross_weight': 'Gross Weight'
    }

    @staticmethod
    def get_platform_fields(platform: Platform) -> Dict[str, str]:
        """Get field mapping for specific platform."""
        mappings = {
            Platform.MEESHO: PlatformMapping.MEESHO_FIELDS,
            Platform.FLIPKART: PlatformMapping.FLIPKART_FIELDS,
            Platform.MYNTRA: PlatformMapping.MYNTRA_FIELDS
        }
        return mappings.get(platform, {})


# Sample data for testing
def create_sample_necklace() -> Product:
    """Create a sample necklace product for testing."""
    return Product(
        product_name="Elegant Gold-Plated Statement Necklace",
        brand="ABC Jewels",
        sku="NKL1234",
        product_type=ProductType.NECKLACE,
        description="Traditional gold-plated necklace with intricate detailing, perfect for festive occasions",
        mrp=1499.0,
        selling_price=799.0,
        material=Material.BRASS,
        color="Gold",
        plating="Gold Plated",
        base_metal="Brass",
        size="16 inches",
        gender="Women",
        article_type="Necklace",
        hsn_code="71171900",
        inventory=20,
        search_tags=["gold", "necklace", "festive", "traditional"],
        occasion="Wedding",
        care_instructions="Keep away from water and perfume"
    )


def create_sample_bangle() -> Product:
    """Create a sample bangle product with variants for testing."""
    return Product(
        product_name="Ethnic Gold-Finish Bangle Set",
        brand="ABC Jewels",
        sku="BGL1000",
        product_type=ProductType.BANGLE,
        description="Classic Indian design bangles, lightweight and perfect for daily wear",
        mrp=899.0,
        selling_price=499.0,
        material=Material.ALLOY,
        color="Gold",
        plating="Gold Plated",
        base_metal="Alloy",
        gender="Women",
        article_type="Bangle",
        hsn_code="71171900",
        inventory=15,
        search_tags=["bangle", "ethnic", "gold", "traditional"],
        occasion="Daily Wear"
    )


if __name__ == "__main__":
    # Test the models
    necklace = create_sample_necklace()
    bangle = create_sample_bangle()

    print("Sample Necklace:", necklace.product_name)
    print("Sample Bangle:", bangle.product_name)
    print("Bangle Variants:", [v.sku for v in bangle.variants])

    # Test validation
    errors = necklace.validate_for_platform(Platform.FLIPKART)
    print("Flipkart validation errors:", errors)
