"""
Tag Models

This module defines the Tag data model and related classes.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum


class TagKind(Enum):
    """Tag type enumeration."""
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    INDICATOR = "indicator"
    CONTROL_POINT = "control_point"
    ALARM = "alarm"
    SETPOINT = "setpoint"
    STATUS = "status"


class AttachmentStrategy(Enum):
    """Tag attachment strategy enumeration."""
    BY_POSITION = "by_position"  # localPosition
    BY_PRIM = "by_prim"  # attachPrimPath


@dataclass
class Tag:
    """
    Tag data model.
    
    Attributes:
        tag_id: Tag unique identifier (UUIDv7)
        name: Tag name
        kind: Tag type (sensor, actuator, indicator, etc.)
        eu_unit: Engineering unit (e.g., "m³/h", "°C", "bar")
        world_space: Whether to use world coordinate system (default False)
        attachment_strategy: Tag attachment strategy (by_position or by_prim)
        local_position: Local position relative to asset origin (for by_position)
        attach_prim_path: USD Prim path (for by_prim)
        properties: Additional properties
        mappings: Mappings to external systems
    
    Example:
        >>> # By-position tag
        >>> tag1 = Tag(
        ...     tag_id="018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1b",
        ...     name="Pressure Sensor",
        ...     kind=TagKind.SENSOR,
        ...     eu_unit="bar",
        ...     attachment_strategy=AttachmentStrategy.BY_POSITION,
        ...     local_position=[1.0, 0.0, 0.5]
        ... )
        
        >>> # By-prim tag
        >>> tag2 = Tag(
        ...     tag_id="018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1a",
        ...     name="Flow Sensor",
        ...     kind=TagKind.SENSOR,
        ...     eu_unit="m³/h",
        ...     attachment_strategy=AttachmentStrategy.BY_PRIM,
        ...     attach_prim_path="/Pump/Outlet"
        ... )
    """
    tag_id: str
    name: str
    kind: TagKind
    eu_unit: Optional[str] = None
    world_space: bool = False
    attachment_strategy: AttachmentStrategy = AttachmentStrategy.BY_POSITION
    local_position: Optional[List[float]] = None
    attach_prim_path: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    mappings: Dict[str, str] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate tag after initialization."""
        self._validate()
    
    def _validate(self):
        """Validate tag data."""
        # Validate attachment strategy
        if self.attachment_strategy == AttachmentStrategy.BY_POSITION:
            if self.local_position is None:
                raise ValueError(
                    f"Tag {self.tag_id}: local_position is required for by_position attachment"
                )
            if len(self.local_position) != 3:
                raise ValueError(
                    f"Tag {self.tag_id}: local_position must have 3 elements [x, y, z]"
                )
        elif self.attachment_strategy == AttachmentStrategy.BY_PRIM:
            if self.attach_prim_path is None:
                raise ValueError(
                    f"Tag {self.tag_id}: attach_prim_path is required for by_prim attachment"
                )
            if not self.attach_prim_path.startswith("/"):
                raise ValueError(
                    f"Tag {self.tag_id}: attach_prim_path must start with '/'"
                )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert tag to dictionary.
        
        Returns:
            Dict[str, Any]: Tag data as dictionary
        """
        data = {
            "tag_id": self.tag_id,
            "name": self.name,
            "kind": self.kind.value,
            "world_space": self.world_space,
        }
        
        if self.eu_unit:
            data["eu_unit"] = self.eu_unit
        
        if self.attachment_strategy == AttachmentStrategy.BY_POSITION:
            data["localPosition"] = self.local_position
        elif self.attachment_strategy == AttachmentStrategy.BY_PRIM:
            data["attachPrimPath"] = self.attach_prim_path
        
        if self.properties:
            data["properties"] = self.properties
        
        if self.mappings:
            data["mappings"] = self.mappings
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tag":
        """
        Create tag from dictionary.
        
        Args:
            data: Tag data as dictionary
        
        Returns:
            Tag: Tag instance
        """
        # Determine attachment strategy
        if "localPosition" in data:
            attachment_strategy = AttachmentStrategy.BY_POSITION
            local_position = data["localPosition"]
            attach_prim_path = None
        elif "attachPrimPath" in data:
            attachment_strategy = AttachmentStrategy.BY_PRIM
            local_position = None
            attach_prim_path = data["attachPrimPath"]
        else:
            raise ValueError("Either localPosition or attachPrimPath must be specified")
        
        return cls(
            tag_id=data["tag_id"],
            name=data["name"],
            kind=TagKind(data["kind"]),
            eu_unit=data.get("eu_unit"),
            world_space=data.get("world_space", False),
            attachment_strategy=attachment_strategy,
            local_position=local_position,
            attach_prim_path=attach_prim_path,
            properties=data.get("properties", {}),
            mappings=data.get("mappings", {}),
        )


@dataclass
class TagInstance:
    """
    Tag instance in a specific asset instance.
    
    Attributes:
        tag: Tag definition
        asset_instance_id: Asset instance ID that this tag belongs to
        world_position: Computed world position (if applicable)
        current_value: Current tag value
        timestamp: Timestamp of current value
    """
    tag: Tag
    asset_instance_id: str
    world_position: Optional[List[float]] = None
    current_value: Optional[Any] = None
    timestamp: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert tag instance to dictionary."""
        data = {
            "tag": self.tag.to_dict(),
            "asset_instance_id": self.asset_instance_id,
        }
        
        if self.world_position:
            data["world_position"] = self.world_position
        
        if self.current_value is not None:
            data["current_value"] = self.current_value
        
        if self.timestamp is not None:
            data["timestamp"] = self.timestamp
        
        return data


if __name__ == "__main__":
    # Demo
    from .id_generator import generate_tag_id
    
    print("=== Tag Models Demo ===\n")
    
    # Create by-position tag
    print("By-Position Tag:")
    tag1 = Tag(
        tag_id=generate_tag_id(),
        name="Pressure Sensor",
        kind=TagKind.SENSOR,
        eu_unit="bar",
        attachment_strategy=AttachmentStrategy.BY_POSITION,
        local_position=[1.0, 0.0, 0.5],
        properties={"alarm_high": 10.0, "alarm_low": 0.5},
        mappings={"scada_tag": "PLC1.DB10.DBD0"}
    )
    print(f"  Tag ID: {tag1.tag_id}")
    print(f"  Name: {tag1.name}")
    print(f"  Kind: {tag1.kind.value}")
    print(f"  EU Unit: {tag1.eu_unit}")
    print(f"  Local Position: {tag1.local_position}")
    print(f"  Properties: {tag1.properties}")
    print()
    
    # Create by-prim tag
    print("By-Prim Tag:")
    tag2 = Tag(
        tag_id=generate_tag_id(),
        name="Flow Sensor",
        kind=TagKind.SENSOR,
        eu_unit="m³/h",
        attachment_strategy=AttachmentStrategy.BY_PRIM,
        attach_prim_path="/Pump/Outlet"
    )
    print(f"  Tag ID: {tag2.tag_id}")
    print(f"  Name: {tag2.name}")
    print(f"  Kind: {tag2.kind.value}")
    print(f"  EU Unit: {tag2.eu_unit}")
    print(f"  Attach Prim Path: {tag2.attach_prim_path}")
    print()
    
    # Convert to dict
    print("Tag to Dict:")
    tag_dict = tag1.to_dict()
    print(f"  {tag_dict}")
    print()
    
    # Create from dict
    print("Tag from Dict:")
    tag3 = Tag.from_dict(tag_dict)
    print(f"  Tag ID: {tag3.tag_id}")
    print(f"  Name: {tag3.name}")
    print()
    
    # Create tag instance
    print("Tag Instance:")
    tag_instance = TagInstance(
        tag=tag1,
        asset_instance_id="pump_001",
        world_position=[10.0, 5.0, 0.5],
        current_value=5.2,
        timestamp=1698765432000
    )
    print(f"  Asset Instance ID: {tag_instance.asset_instance_id}")
    print(f"  World Position: {tag_instance.world_position}")
    print(f"  Current Value: {tag_instance.current_value} {tag_instance.tag.eu_unit}")

