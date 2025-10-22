"""
Runtime - Asset Library Service for managing IADL assets
"""

from typing import Dict, List, Optional
from pathlib import Path
import threading

from ..iadl.models import Asset
from ..iadl.parser import parse_iadl_file
from ..iadl.validator import IADLValidator


class AssetLibraryService:
    """
    Service for managing a library of IADL assets.
    
    Provides functionality to:
    - Load assets from files
    - Store assets in memory
    - Query assets by ID or name
    - Validate assets
    - List all available assets
    """
    
    def __init__(self, auto_validate: bool = True):
        """
        Initialize the Asset Library Service.
        
        Args:
            auto_validate: Whether to automatically validate assets when loading (default: True)
        """
        self.assets: Dict[str, Asset] = {}  # asset_id -> Asset
        self.asset_paths: Dict[str, Path] = {}  # asset_id -> file path
        self.auto_validate = auto_validate
        self.validator = IADLValidator() if auto_validate else None
        self.lock = threading.Lock()
    
    def load_asset(self, file_path: Path) -> Optional[Asset]:
        """
        Load an asset from an IADL file.
        
        Args:
            file_path: Path to the IADL file
        
        Returns:
            Optional[Asset]: Loaded asset, or None if loading failed
        """
        try:
            asset = parse_iadl_file(file_path)
            
            if self.auto_validate:
                is_valid = self.validator.validate_asset(asset)
                errors = self.validator.get_errors()
                if not is_valid:
                    print(f"Asset validation failed: {errors}")
                    return None
            
            with self.lock:
                self.assets[asset.asset_id] = asset
                self.asset_paths[asset.asset_id] = file_path
            
            return asset
        
        except Exception as e:
            print(f"Error loading asset from {file_path}: {e}")
            return None
    
    def load_assets_from_directory(self, directory: Path, pattern: str = "*.yaml") -> int:
        """
        Load all assets from a directory.
        
        Args:
            directory: Directory containing IADL files
            pattern: File pattern to match (default: "*.yaml")
        
        Returns:
            int: Number of assets loaded successfully
        """
        directory = Path(directory)
        if not directory.exists():
            print(f"Directory not found: {directory}")
            return 0
        
        count = 0
        for file_path in directory.glob(pattern):
            if self.load_asset(file_path):
                count += 1
        
        return count
    
    def add_asset(self, asset: Asset) -> bool:
        """
        Add an asset to the library.
        
        Args:
            asset: Asset to add
        
        Returns:
            bool: True if added successfully, False otherwise
        """
        if self.auto_validate:
            is_valid = self.validator.validate_asset(asset)
            errors = self.validator.get_errors()
            if not is_valid:
                print(f"Asset validation failed: {errors}")
                return False
        
        with self.lock:
            self.assets[asset.asset_id] = asset
        
        return True
    
    def get_asset(self, asset_id: str) -> Optional[Asset]:
        """
        Get an asset by ID.
        
        Args:
            asset_id: Asset identifier
        
        Returns:
            Optional[Asset]: Asset if found, None otherwise
        """
        with self.lock:
            return self.assets.get(asset_id)
    
    def get_asset_by_name(self, name: str) -> Optional[Asset]:
        """
        Get an asset by name.
        
        Args:
            name: Asset name
        
        Returns:
            Optional[Asset]: First asset with matching name, or None if not found
        """
        with self.lock:
            for asset in self.assets.values():
                if asset.name == name:
                    return asset
        return None
    
    def list_assets(self) -> List[Asset]:
        """
        List all assets in the library.
        
        Returns:
            List[Asset]: List of all assets
        """
        with self.lock:
            return list(self.assets.values())
    
    def list_asset_ids(self) -> List[str]:
        """
        List all asset IDs in the library.
        
        Returns:
            List[str]: List of asset IDs
        """
        with self.lock:
            return list(self.assets.keys())
    
    def remove_asset(self, asset_id: str) -> bool:
        """
        Remove an asset from the library.
        
        Args:
            asset_id: Asset identifier
        
        Returns:
            bool: True if removed, False if not found
        """
        with self.lock:
            if asset_id in self.assets:
                del self.assets[asset_id]
                if asset_id in self.asset_paths:
                    del self.asset_paths[asset_id]
                return True
        return False
    
    def clear(self):
        """Clear all assets from the library."""
        with self.lock:
            self.assets.clear()
            self.asset_paths.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get library statistics.
        
        Returns:
            Dict[str, int]: Statistics (total_assets, etc.)
        """
        with self.lock:
            return {
                "total_assets": len(self.assets),
                "total_tags": sum(len(asset.tags) for asset in self.assets.values())
            }


if __name__ == '__main__':
    from ..tags.id_generator import generate_uuidv7
    from ..iadl.models import Transform, Units, Tag, Metadata
    from datetime import datetime
    
    print("=== Asset Library Service Demo ===\n")
    
    # Create service
    service = AssetLibraryService(auto_validate=True)
    
    # Create sample assets
    print("--- Creating Sample Assets ---")
    
    asset1 = Asset(
        asset_id=generate_uuidv7(),
        name="Centrifugal Pump",
        model_ref="@/models/pump.usd@",
        units=Units(length="m"),
        default_xform=Transform(
            translation=[0.0, 0.0, 0.0],
            rotation=[0.0, 0.0, 0.0],
            scale=[1.0, 1.0, 1.0]
        ),
        tags=[
            Tag(
                tag_id=generate_uuidv7(),
                name="FlowRate",
                kind="analog",
                eu_unit="m3/h",
                local_position=[1.0, 0.0, 0.5]
            )
        ],
        metadata=Metadata(
            author="John Doe",
            version="1.0.0",
            created_at=datetime.utcnow().isoformat() + "Z"
        )
    )
    
    asset2 = Asset(
        asset_id=generate_uuidv7(),
        name="Heat Exchanger",
        model_ref="@/models/heat_exchanger.usd@",
        units=Units(length="m"),
        default_xform=Transform(
            translation=[0.0, 0.0, 0.0],
            rotation=[0.0, 0.0, 0.0],
            scale=[1.0, 1.0, 1.0]
        ),
        tags=[],
        metadata=Metadata(
            author="Jane Smith",
            version="1.0.0",
            created_at=datetime.utcnow().isoformat() + "Z"
        )
    )
    
    # Add assets
    print("--- Adding Assets ---")
    service.add_asset(asset1)
    service.add_asset(asset2)
    print(f"Added 2 assets")
    print()
    
    # List assets
    print("--- Listing Assets ---")
    assets = service.list_assets()
    print(f"Total assets: {len(assets)}")
    for asset in assets:
        print(f"  - {asset.name} ({asset.asset_id})")
    print()
    
    # Get asset by ID
    print("--- Getting Asset by ID ---")
    retrieved_asset = service.get_asset(asset1.asset_id)
    if retrieved_asset:
        print(f"Retrieved: {retrieved_asset.name}")
    print()
    
    # Get asset by name
    print("--- Getting Asset by Name ---")
    found_asset = service.get_asset_by_name("Heat Exchanger")
    if found_asset:
        print(f"Found: {found_asset.name} ({found_asset.asset_id})")
    print()
    
    # Get statistics
    print("--- Library Statistics ---")
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Remove asset
    print("--- Removing Asset ---")
    removed = service.remove_asset(asset2.asset_id)
    print(f"Removed: {removed}")
    print(f"Remaining assets: {len(service.list_assets())}")
    print()
    
    # Clear library
    print("--- Clearing Library ---")
    service.clear()
    print(f"Assets after clear: {len(service.list_assets())}")
    print()

