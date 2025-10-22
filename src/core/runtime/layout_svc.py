"""
Runtime - Layout Service for managing FDL layouts and asset instances
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import threading

from ..fdl.models import FDL, AssetInstance, BatchLayout
from ..fdl.parser import parse_fdl_file
from ..fdl.validator import FDLValidator
from ..fdl.batch_layout import generate_batch_instances
from ..geom.bbox import AABB
from ..geom.collision import CollisionChecker


class LayoutService:
    """
    Service for managing FDL layouts and asset instances.
    
    Provides functionality to:
    - Load FDL layouts from files
    - Manage asset instances
    - Generate batch layouts
    - Detect collisions
    - Query instances by ID or area
    """
    
    def __init__(self, auto_validate: bool = True):
        """
        Initialize the Layout Service.
        
        Args:
            auto_validate: Whether to automatically validate FDL when loading (default: True)
        """
        self.fdl: Optional[FDL] = None
        self.instances: Dict[str, AssetInstance] = {}  # instance_id -> AssetInstance
        self.auto_validate = auto_validate
        self.validator = FDLValidator() if auto_validate else None
        self.collision_checker: Optional[CollisionChecker] = None
        self.lock = threading.Lock()
    
    def load_fdl(self, file_path: Path) -> bool:
        """
        Load an FDL layout from a file.
        
        Args:
            file_path: Path to the FDL file
        
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        try:
            fdl = parse_fdl_file(file_path)
            
            if self.auto_validate:
                is_valid, errors = self.validator.validate(fdl)
                if not is_valid:
                    print(f"FDL validation failed: {errors}")
                    return False
            
            with self.lock:
                self.fdl = fdl
                self._rebuild_instance_index()
                
                # Initialize collision checker if configured
                if fdl.global_constraints and fdl.global_constraints.collision_detection:
                    clearance = fdl.global_constraints.collision_detection.min_clearance_distance
                    self.collision_checker = CollisionChecker(clearance_distance=clearance)
            
            return True
        
        except Exception as e:
            print(f"Error loading FDL from {file_path}: {e}")
            return False
    
    def _rebuild_instance_index(self):
        """Rebuild the instance index from FDL."""
        self.instances.clear()
        
        if not self.fdl or not self.fdl.site:
            return
        
        for area in self.fdl.site.areas:
            for instance in area.instances:
                self.instances[instance.instance_id] = instance
    
    def get_instance(self, instance_id: str) -> Optional[AssetInstance]:
        """
        Get an asset instance by ID.
        
        Args:
            instance_id: Instance identifier
        
        Returns:
            Optional[AssetInstance]: Instance if found, None otherwise
        """
        with self.lock:
            return self.instances.get(instance_id)
    
    def list_instances(self, area_id: Optional[str] = None) -> List[AssetInstance]:
        """
        List asset instances, optionally filtered by area.
        
        Args:
            area_id: Optional area ID to filter by
        
        Returns:
            List[AssetInstance]: List of instances
        """
        with self.lock:
            if area_id is None:
                return list(self.instances.values())
            
            if not self.fdl or not self.fdl.site:
                return []
            
            for area in self.fdl.site.areas:
                if area.area_id == area_id:
                    return area.instances.copy()
            
            return []
    
    def add_instance(self, area_id: str, instance: AssetInstance) -> bool:
        """
        Add an asset instance to an area.
        
        Args:
            area_id: Area identifier
            instance: Asset instance to add
        
        Returns:
            bool: True if added successfully, False otherwise
        """
        with self.lock:
            if not self.fdl or not self.fdl.site:
                print("No FDL loaded")
                return False
            
            for area in self.fdl.site.areas:
                if area.area_id == area_id:
                    area.instances.append(instance)
                    self.instances[instance.instance_id] = instance
                    return True
            
            print(f"Area not found: {area_id}")
            return False
    
    def remove_instance(self, instance_id: str) -> bool:
        """
        Remove an asset instance.
        
        Args:
            instance_id: Instance identifier
        
        Returns:
            bool: True if removed, False if not found
        """
        with self.lock:
            if instance_id not in self.instances:
                return False
            
            if not self.fdl or not self.fdl.site:
                return False
            
            for area in self.fdl.site.areas:
                area.instances = [inst for inst in area.instances if inst.instance_id != instance_id]
            
            del self.instances[instance_id]
            return True
    
    def generate_batch_layout(
        self,
        area_id: str,
        batch_layout: BatchLayout
    ) -> List[AssetInstance]:
        """
        Generate instances from a batch layout definition.
        
        Args:
            area_id: Area identifier
            batch_layout: Batch layout definition
        
        Returns:
            List[AssetInstance]: Generated instances
        """
        existing_ids = set(self.instances.keys())
        instances = generate_batch_instances(batch_layout, existing_ids)
        
        # Add instances to area
        for instance in instances:
            self.add_instance(area_id, instance)
        
        return instances
    
    def detect_collisions(self, instance_aabbs: Dict[str, AABB]) -> List[Tuple[str, str]]:
        """
        Detect collisions among asset instances.
        
        Args:
            instance_aabbs: Dictionary mapping instance IDs to AABBs
        
        Returns:
            List[Tuple[str, str]]: List of colliding instance ID pairs
        """
        if not self.collision_checker:
            print("Collision checker not initialized")
            return []
        
        return self.collision_checker.find_collisions(instance_aabbs)
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get layout statistics.
        
        Returns:
            Dict[str, int]: Statistics
        """
        with self.lock:
            if not self.fdl or not self.fdl.site:
                return {"total_instances": 0, "total_areas": 0}
            
            return {
                "total_instances": len(self.instances),
                "total_areas": len(self.fdl.site.areas),
                "total_connections": sum(len(area.connections) for area in self.fdl.site.areas)
            }


if __name__ == '__main__':
    from ..fdl.models import FDLUnits, Site, Area, Transform
    from ..tags.id_generator import generate_uuidv7
    
    print("=== Layout Service Demo ===\n")
    
    # Create service
    service = LayoutService(auto_validate=False)  # Disable validation for demo
    
    # Create sample FDL
    print("--- Creating Sample FDL ---")
    fdl = FDL(
        fdl_version="0.1.0",
        units=FDLUnits(length="m"),
        site=Site(
            site_id="site_001",
            name="Demo Site",
            areas=[
                Area(
                    area_id="area_001",
                    name="Production Area",
                    instances=[
                        AssetInstance(
                            instance_id="inst_001",
                            ref_asset=generate_uuidv7(),
                            transform=Transform(
                                translation=[10.0, 5.0, 0.0],
                                rotation=[0.0, 0.0, 0.0],
                                scale=[1.0, 1.0, 1.0]
                            )
                        )
                    ],
                    connections=[]
                )
            ]
        )
    )
    
    service.fdl = fdl
    service._rebuild_instance_index()
    print(f"Created FDL with {len(service.instances)} instances")
    print()
    
    # List instances
    print("--- Listing Instances ---")
    instances = service.list_instances()
    print(f"Total instances: {len(instances)}")
    for inst in instances:
        print(f"  - {inst.instance_id}: {inst.transform.translation}")
    print()
    
    # Add instance
    print("--- Adding Instance ---")
    new_instance = AssetInstance(
        instance_id="inst_002",
        ref_asset=generate_uuidv7(),
        transform=Transform(
            translation=[20.0, 10.0, 0.0],
            rotation=[0.0, 0.0, 0.0],
            scale=[1.0, 1.0, 1.0]
        )
    )
    service.add_instance("area_001", new_instance)
    print(f"Added instance: {new_instance.instance_id}")
    print(f"Total instances: {len(service.list_instances())}")
    print()
    
    # Get statistics
    print("--- Layout Statistics ---")
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Remove instance
    print("--- Removing Instance ---")
    removed = service.remove_instance("inst_002")
    print(f"Removed: {removed}")
    print(f"Remaining instances: {len(service.list_instances())}")
    print()

