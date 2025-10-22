"""
IADL Models

This module defines the IADL (Industrial Asset Definition Language) data models.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime

from ..tags.models import Tag


@dataclass
class Units:
    """
    Unit system definition.
    
    Attributes:
        length: Length unit (m, cm, mm)
    """
    length: str = "m"
    
    def validate(self):
        """Validate units."""
        valid_length_units = ["m", "cm", "mm"]
        if self.length not in valid_length_units:
            raise ValueError(
                f"Invalid length unit: {self.length}. "
                f"Must be one of {valid_length_units}"
            )


@dataclass
class Transform:
    """
    Transform definition (translation, rotation, scale).
    
    Attributes:
        translation: Translation vector [x, y, z]
        rotation: Rotation vector (Euler angles in degrees) [x, y, z]
        scale: Scale vector [x, y, z]
    """
    translation: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    rotation: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    scale: List[float] = field(default_factory=lambda: [1.0, 1.0, 1.0])
    
    def validate(self, allow_scaling: bool = False, allow_non_uniform_scaling: bool = False):
        """
        Validate transform.
        
        Args:
            allow_scaling: Whether scaling is allowed
            allow_non_uniform_scaling: Whether non-uniform scaling is allowed
        """
        if len(self.translation) != 3:
            raise ValueError("translation must have 3 elements [x, y, z]")
        
        if len(self.rotation) != 3:
            raise ValueError("rotation must have 3 elements [x, y, z]")
        
        if len(self.scale) != 3:
            raise ValueError("scale must have 3 elements [x, y, z]")
        
        # Validate scaling constraints
        if not allow_scaling:
            if self.scale != [1.0, 1.0, 1.0]:
                raise ValueError(
                    f"Scaling is not allowed. scale must be [1.0, 1.0, 1.0], got {self.scale}"
                )
        
        if not allow_non_uniform_scaling:
            if not (self.scale[0] == self.scale[1] == self.scale[2]):
                raise ValueError(
                    f"Non-uniform scaling is not allowed. "
                    f"scale must be [s, s, s], got {self.scale}"
                )

    @classmethod
    def from_dict(cls, data: Dict[str, List[float]]) -> "Transform":
        return cls(
            translation=data.get("translation", [0.0, 0.0, 0.0]),
            rotation=data.get("rotation", [0.0, 0.0, 0.0]),
            scale=data.get("scale", [1.0, 1.0, 1.0]),
        )


@dataclass
class Metadata:
    """
    Asset metadata.
    
    Attributes:
        author: Author name
        version: Version number (Semantic Versioning)
        created_at: Creation timestamp (ISO 8601)
        updated_at: Last update timestamp (ISO 8601)
    """
    author: Optional[str] = None
    version: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def set_created_at_now(self):
        """Set created_at to current timestamp."""
        self.created_at = datetime.utcnow().isoformat() + "Z"
    
    def set_updated_at_now(self):
        """Set updated_at to current timestamp."""
        self.updated_at = datetime.utcnow().isoformat() + "Z"


@dataclass
class Asset:
    """
    IADL Asset definition.
    
    Attributes:
        asset_id: Asset unique identifier (UUIDv7)
        name: Asset name
        description: Asset description
        model_ref: USD model reference (path or Reference)
        units: Unit system definition
        default_xform: Default transform
        tags: List of tags
        metadata: Asset metadata
    
    Example:
        >>> from ..tags.id_generator import generate_asset_id, generate_tag_id
        >>> from ..tags.models import Tag, TagKind, AttachmentStrategy
        >>> 
        >>> asset = Asset(
        ...     asset_id=generate_asset_id(),
        ...     name="Centrifugal Pump Model A",
        ...     description="High-efficiency centrifugal pump",
        ...     model_ref="@/assets/pumps/centrifugal_pump_a.usd@</Pump>",
        ...     units=Units(length="m"),
        ...     default_xform=Transform(),
        ...     tags=[
        ...         Tag(
        ...             tag_id=generate_tag_id(),
        ...             name="Inlet Flow Sensor",
        ...             kind=TagKind.SENSOR,
        ...             eu_unit="m³/h",
        ...             attachment_strategy=AttachmentStrategy.BY_PRIM,
        ...             attach_prim_path="/Pump/Inlet"
        ...         )
        ...     ],
        ...     metadata=Metadata(author="Michael Lin", version="1.0.0")
        ... )
    """
    asset_id: str
    name: str
    model_ref: str
    units: Units = field(default_factory=Units)
    description: Optional[str] = None
    default_xform: Transform = field(default_factory=Transform)
    tags: List[Tag] = field(default_factory=list)
    metadata: Metadata = field(default_factory=Metadata)
    
    def validate(self):
        """Validate asset."""
        # Validate asset_id
        if not self.asset_id:
            raise ValueError("asset_id is required")
        
        # Validate name
        if not self.name:
            raise ValueError("name is required")
        
        # Validate model_ref
        if not self.model_ref:
            raise ValueError("model_ref is required")
        
        # Validate units
        self.units.validate()
        
        # Validate default_xform
        self.default_xform.validate(allow_scaling=True, allow_non_uniform_scaling=False)
        
        # Validate tags
        tag_ids = set()
        for tag in self.tags:
            if tag.tag_id in tag_ids:
                raise ValueError(f"Duplicate tag_id: {tag.tag_id}")
            tag_ids.add(tag.tag_id)
            tag._validate()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert asset to dictionary."""
        data = {
            "asset_id": self.asset_id,
            "name": self.name,
            "model_ref": self.model_ref,
            "units": {
                "length": self.units.length
            },
            "default_xform": {
                "translation": self.default_xform.translation,
                "rotation": self.default_xform.rotation,
                "scale": self.default_xform.scale
            },
            "tags": [tag.to_dict() for tag in self.tags]
        }
        
        if self.description:
            data["description"] = self.description
        
        if self.metadata.author or self.metadata.version or \
           self.metadata.created_at or self.metadata.updated_at:
            metadata_dict = {}
            if self.metadata.author:
                metadata_dict["author"] = self.metadata.author
            if self.metadata.version:
                metadata_dict["version"] = self.metadata.version
            if self.metadata.created_at:
                metadata_dict["created_at"] = self.metadata.created_at
            if self.metadata.updated_at:
                metadata_dict["updated_at"] = self.metadata.updated_at
            data["metadata"] = metadata_dict
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Asset":
        """Create asset from dictionary."""
        # Parse units
        units_data = data.get("units", {})
        units = Units(length=units_data.get("length", "m"))
        
        # Parse default_xform
        xform_data = data.get("default_xform", {})
        default_xform = Transform(
            translation=xform_data.get("translation", [0.0, 0.0, 0.0]),
            rotation=xform_data.get("rotation", [0.0, 0.0, 0.0]),
            scale=xform_data.get("scale", [1.0, 1.0, 1.0])
        )
        
        # Parse tags
        tags_data = data.get("tags", [])
        tags = [Tag.from_dict(tag_data) for tag_data in tags_data]
        
        # Parse metadata
        metadata_data = data.get("metadata", {})
        metadata = Metadata(
            author=metadata_data.get("author"),
            version=metadata_data.get("version"),
            created_at=metadata_data.get("created_at"),
            updated_at=metadata_data.get("updated_at")
        )
        
        return cls(
            asset_id=data["asset_id"],
            name=data["name"],
            model_ref=data["model_ref"],
            units=units,
            description=data.get("description"),
            default_xform=default_xform,
            tags=tags,
            metadata=metadata
        )


if __name__ == "__main__":
    # Demo
    from ..tags.id_generator import generate_asset_id, generate_tag_id
    from ..tags.models import TagKind, AttachmentStrategy
    
    print("=== IADL Models Demo ===\n")
    
    # Create asset
    asset = Asset(
        asset_id=generate_asset_id(),
        name="Centrifugal Pump Model A",
        description="High-efficiency centrifugal pump for water circulation",
        model_ref="@/assets/pumps/centrifugal_pump_a.usd@</Pump>",
        units=Units(length="m"),
        default_xform=Transform(),
        tags=[
            Tag(
                tag_id=generate_tag_id(),
                name="Inlet Flow Sensor",
                kind=TagKind.SENSOR,
                eu_unit="m³/h",
                attachment_strategy=AttachmentStrategy.BY_PRIM,
                attach_prim_path="/Pump/Inlet"
            ),
            Tag(
                tag_id=generate_tag_id(),
                name="Outlet Pressure Sensor",
                kind=TagKind.SENSOR,
                eu_unit="bar",
                attachment_strategy=AttachmentStrategy.BY_PRIM,
                attach_prim_path="/Pump/Outlet"
            )
        ],
        metadata=Metadata(author="Michael Lin", version="1.0.0")
    )
    
    # Set timestamps
    asset.metadata.set_created_at_now()
    asset.metadata.set_updated_at_now()
    
    # Validate
    asset.validate()
    print("Asset validated successfully!")
    print()
    
    # Print asset info
    print(f"Asset ID: {asset.asset_id}")
    print(f"Name: {asset.name}")
    print(f"Description: {asset.description}")
    print(f"Model Ref: {asset.model_ref}")
    print(f"Units: {asset.units.length}")
    print(f"Tags: {len(asset.tags)}")
    for tag in asset.tags:
        print(f"  - {tag.name} ({tag.kind.value}): {tag.attach_prim_path}")
    print()
    
    # Convert to dict
    asset_dict = asset.to_dict()
    print("Asset to Dict:")
    import json
    print(json.dumps(asset_dict, indent=2))

