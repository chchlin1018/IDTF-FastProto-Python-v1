"""
Runtime - Tag Mapping Service for managing tag instances and external data source mappings
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import threading

from ..tags.models import TagInstance
from ..tags.attachment import resolve_tag_world_position


@dataclass
class TagMapping:
    """
    Mapping between a tag instance and an external data source.
    """
    tag_instance_id: str
    external_source: str  # e.g., "OPC_UA", "AVEVA_PI", "Modbus"
    external_tag_name: str  # Tag name in external system
    read_only: bool = True
    polling_interval_ms: int = 1000  # Polling interval in milliseconds


class MappingService:
    """
    Service for managing tag instances and their mappings to external data sources.
    
    Provides functionality to:
    - Create tag instances from IADL assets and FDL instances
    - Map tag instances to external data sources
    - Query tag instances by ID or asset instance
    - Resolve tag world positions
    """
    
    def __init__(self):
        """Initialize the Mapping Service."""
        self.tag_instances: Dict[str, TagInstance] = {}  # tag_instance_id -> TagInstance
        self.mappings: Dict[str, TagMapping] = {}  # tag_instance_id -> TagMapping
        self.lock = threading.Lock()
    
    def create_tag_instance(
        self,
        tag_instance: TagInstance
    ) -> bool:
        """
        Create a tag instance.
        
        Args:
            tag_instance: Tag instance to create
        
        Returns:
            bool: True if created successfully, False otherwise
        """
        with self.lock:
            if tag_instance.tag_instance_id in self.tag_instances:
                print(f"Tag instance already exists: {tag_instance.tag_instance_id}")
                return False
            
            self.tag_instances[tag_instance.tag_instance_id] = tag_instance
            return True
    
    def get_tag_instance(self, tag_instance_id: str) -> Optional[TagInstance]:
        """
        Get a tag instance by ID.
        
        Args:
            tag_instance_id: Tag instance identifier
        
        Returns:
            Optional[TagInstance]: Tag instance if found, None otherwise
        """
        with self.lock:
            return self.tag_instances.get(tag_instance_id)
    
    def list_tag_instances(
        self,
        asset_instance_id: Optional[str] = None
    ) -> List[TagInstance]:
        """
        List tag instances, optionally filtered by asset instance.
        
        Args:
            asset_instance_id: Optional asset instance ID to filter by
        
        Returns:
            List[TagInstance]: List of tag instances
        """
        with self.lock:
            if asset_instance_id is None:
                return list(self.tag_instances.values())
            
            return [
                tag_inst for tag_inst in self.tag_instances.values()
                if tag_inst.asset_instance_id == asset_instance_id
            ]
    
    def remove_tag_instance(self, tag_instance_id: str) -> bool:
        """
        Remove a tag instance.
        
        Args:
            tag_instance_id: Tag instance identifier
        
        Returns:
            bool: True if removed, False if not found
        """
        with self.lock:
            if tag_instance_id in self.tag_instances:
                del self.tag_instances[tag_instance_id]
                
                # Also remove mapping if exists
                if tag_instance_id in self.mappings:
                    del self.mappings[tag_instance_id]
                
                return True
        return False
    
    def create_mapping(self, mapping: TagMapping) -> bool:
        """
        Create a mapping between a tag instance and an external data source.
        
        Args:
            mapping: Tag mapping to create
        
        Returns:
            bool: True if created successfully, False otherwise
        """
        with self.lock:
            if mapping.tag_instance_id not in self.tag_instances:
                print(f"Tag instance not found: {mapping.tag_instance_id}")
                return False
            
            self.mappings[mapping.tag_instance_id] = mapping
            return True
    
    def get_mapping(self, tag_instance_id: str) -> Optional[TagMapping]:
        """
        Get a tag mapping by tag instance ID.
        
        Args:
            tag_instance_id: Tag instance identifier
        
        Returns:
            Optional[TagMapping]: Tag mapping if found, None otherwise
        """
        with self.lock:
            return self.mappings.get(tag_instance_id)
    
    def list_mappings(
        self,
        external_source: Optional[str] = None
    ) -> List[TagMapping]:
        """
        List tag mappings, optionally filtered by external source.
        
        Args:
            external_source: Optional external source to filter by
        
        Returns:
            List[TagMapping]: List of tag mappings
        """
        with self.lock:
            if external_source is None:
                return list(self.mappings.values())
            
            return [
                mapping for mapping in self.mappings.values()
                if mapping.external_source == external_source
            ]
    
    def remove_mapping(self, tag_instance_id: str) -> bool:
        """
        Remove a tag mapping.
        
        Args:
            tag_instance_id: Tag instance identifier
        
        Returns:
            bool: True if removed, False if not found
        """
        with self.lock:
            if tag_instance_id in self.mappings:
                del self.mappings[tag_instance_id]
                return True
        return False
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get mapping service statistics.
        
        Returns:
            Dict[str, int]: Statistics
        """
        with self.lock:
            return {
                "total_tag_instances": len(self.tag_instances),
                "total_mappings": len(self.mappings),
                "unmapped_tags": len(self.tag_instances) - len(self.mappings)
            }


if __name__ == '__main__':
    from ..tags.id_generator import generate_uuidv7
    
    print("=== Mapping Service Demo ===\n")
    
    # Create service
    service = MappingService()
    
    # Create sample tag instances
    print("--- Creating Tag Instances ---")
    
    tag_inst1 = TagInstance(
        tag_instance_id=generate_uuidv7(),
        tag_id=generate_uuidv7(),
        asset_instance_id="inst_001",
        name="Temperature",
        kind="analog",
        eu_unit="°C",
        world_position=[10.0, 5.0, 2.0]
    )
    
    tag_inst2 = TagInstance(
        tag_instance_id=generate_uuidv7(),
        tag_id=generate_uuidv7(),
        asset_instance_id="inst_001",
        name="Pressure",
        kind="analog",
        eu_unit="bar",
        world_position=[10.0, 5.0, 2.5]
    )
    
    service.create_tag_instance(tag_inst1)
    service.create_tag_instance(tag_inst2)
    print(f"Created 2 tag instances")
    print()
    
    # List tag instances
    print("--- Listing Tag Instances ---")
    tag_instances = service.list_tag_instances()
    print(f"Total tag instances: {len(tag_instances)}")
    for tag_inst in tag_instances:
        print(f"  - {tag_inst.name} ({tag_inst.tag_instance_id})")
    print()
    
    # Create mappings
    print("--- Creating Mappings ---")
    
    mapping1 = TagMapping(
        tag_instance_id=tag_inst1.tag_instance_id,
        external_source="OPC_UA",
        external_tag_name="PLC1.Temperature",
        read_only=True,
        polling_interval_ms=1000
    )
    
    mapping2 = TagMapping(
        tag_instance_id=tag_inst2.tag_instance_id,
        external_source="OPC_UA",
        external_tag_name="PLC1.Pressure",
        read_only=True,
        polling_interval_ms=1000
    )
    
    service.create_mapping(mapping1)
    service.create_mapping(mapping2)
    print(f"Created 2 mappings")
    print()
    
    # List mappings
    print("--- Listing Mappings ---")
    mappings = service.list_mappings()
    print(f"Total mappings: {len(mappings)}")
    for mapping in mappings:
        print(f"  - {mapping.external_tag_name} -> {mapping.tag_instance_id}")
    print()
    
    # Get statistics
    print("--- Mapping Service Statistics ---")
    stats = service.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Remove mapping
    print("--- Removing Mapping ---")
    removed = service.remove_mapping(tag_inst2.tag_instance_id)
    print(f"Removed: {removed}")
    print(f"Remaining mappings: {len(service.list_mappings())}")
    print()

