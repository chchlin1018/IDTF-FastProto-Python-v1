"""
FDL Models - Factory Description Language data models
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum

from ..iadl.models import Transform


class LengthUnit(Enum):
    METER = "m"
    CENTIMETER = "cm"
    MILLIMETER = "mm"


class AngleUnit(Enum):
    DEGREE = "deg"
    RADIAN = "rad"


class UpAxis(Enum):
    X = "X"
    Y = "Y"
    Z = "Z"


class Handedness(Enum):
    RIGHT = "right"
    LEFT = "left"


@dataclass
class FDLUnits:
    """
    FDL-specific unit system definition.
    
    Attributes:
        length: Length unit (m, cm, mm)
        angle: Angle unit (deg, rad)
        up_axis: Up axis (X, Y, Z)
        handedness: Coordinate system handedness (right, left)
    """
    length: LengthUnit = LengthUnit.METER
    angle: AngleUnit = AngleUnit.DEGREE
    up_axis: UpAxis = UpAxis.Z
    handedness: Handedness = Handedness.RIGHT

    def to_dict(self) -> Dict[str, str]:
        return {
            "length": self.length.value,
            "angle": self.angle.value,
            "up_axis": self.up_axis.value,
            "handedness": self.handedness.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "FDLUnits":
        return cls(
            length=LengthUnit(data.get("length", "m")),
            angle=AngleUnit(data.get("angle", "deg")),
            up_axis=UpAxis(data.get("up_axis", "Z")),
            handedness=Handedness(data.get("handedness", "right")),
        )


@dataclass
class Site:
    """
    Site definition.
    
    Attributes:
        name: Site name
        site_id: Site unique identifier (UUIDv7)
        location: Geographical location (latitude, longitude, altitude)
        areas: List of areas within the site
    """
    name: str
    site_id: str
    location: Optional[Dict[str, float]] = None  # latitude, longitude, altitude
    areas: List["Area"] = field(default_factory=list)


@dataclass
class Area:
    """
    Area definition within a site.
    
    Attributes:
        name: Area name
        area_id: Area unique identifier (UUIDv7)
        type: Type of area (e.g., production, storage, control, utility)
        instances: List of asset instances within this area
        connections: List of connections within this area
    """
    name: str
    area_id: str
    type: str = "production"
    instances: List["AssetInstance"] = field(default_factory=list)
    connections: List["Connection"] = field(default_factory=list)


@dataclass
class AssetInstance:
    """
    Asset instance definition.
    
    Attributes:
        instance_id: Unique identifier for this instance
        ref_asset: Reference to IADL asset_id
        name: Optional name for this instance
        transform: Transform of this instance
        tag_overrides: List of tag property overrides for this instance
        collision_bounds: Computed collision bounds (e.g., AABB, OBB)
        constraints: Instance-specific constraints
        metadata: Instance metadata
    """
    instance_id: str
    ref_asset: str  # Reference to IADL asset_id
    name: Optional[str] = None
    transform: Transform = field(default_factory=Transform)
    tag_overrides: List[Dict[str, Any]] = field(default_factory=list)
    collision_bounds: Optional[Dict[str, Any]] = None # e.g., {"type": "AABB", "min": [...], "max": [...]} 
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Connection:
    """
    Connection definition between asset instances.
    
    Attributes:
        connection_id: Unique identifier for this connection
        type: Type of connection (e.g., pipe, cable, duct)
        name: Optional name for this connection
        from_instance: ID of the source asset instance
        from_port: Optional port on the source instance
        to_instance: ID of the target asset instance
        to_port: Optional port on the target instance
        path: Geometric path of the connection
        properties: Additional properties for the connection
    """
    connection_id: str
    type: str
    name: Optional[str] = None
    from_instance: str
    from_port: Optional[str] = None
    to_instance: str
    to_port: Optional[str] = None
    path: Optional[Dict[str, Any]] = None # e.g., {"type": "line", "points": [[x,y,z], ...]}
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScalingConstraints:
    """
    Global scaling constraints.
    """
    allow_scaling: bool = True
    allow_non_uniform_scaling: bool = True
    min_scale: Optional[float] = None
    max_scale: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allow_scaling": self.allow_scaling,
            "allow_non_uniform_scaling": self.allow_non_uniform_scaling,
            "min_scale": self.min_scale,
            "max_scale": self.max_scale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScalingConstraints":
        return cls(
            allow_scaling=data.get("allow_scaling", True),
            allow_non_uniform_scaling=data.get("allow_non_uniform_scaling", True),
            min_scale=data.get("min_scale"),
            max_scale=data.get("max_scale"),
        )


@dataclass
class CollisionDetection:
    """
    Global collision detection settings.
    """
    enabled: bool = False
    clearance_distance: float = 0.0 # meters

    def to_dict(self) -> Dict[str, Any]:
        return {
            "enabled": self.enabled,
            "clearance_distance": self.clearance_distance,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CollisionDetection":
        return cls(
            enabled=data.get("enabled", False),
            clearance_distance=data.get("clearance_distance", 0.0),
        )


@dataclass
class GlobalConstraints:
    """
    Global FDL constraints.
    """
    scaling_constraints: ScalingConstraints = field(default_factory=ScalingConstraints)
    collision_detection: CollisionDetection = field(default_factory=CollisionDetection)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scaling_constraints": self.scaling_constraints.to_dict(),
            "collision_detection": self.collision_detection.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GlobalConstraints":
        return cls(
            scaling_constraints=ScalingConstraints.from_dict(data.get("scaling_constraints", {})),
            collision_detection=CollisionDetection.from_dict(data.get("collision_detection", {})),
        )


@dataclass
class BatchLayout:
    """
    Batch layout definition.
    """
    layout_id: str
    type: str # grid, line, circle
    ref_asset: str
    # Specific layout parameters will be in a 'params' dict
    params: Dict[str, Any] = field(default_factory=dict)
    naming_prefix: str = "Asset"


@dataclass
class FDL:
    """
    FDL (Factory Description Language) definition.
    
    Attributes:
        fdl_version: FDL specification version
        units: Global unit system for the FDL document
        site: The main site containing areas, instances, and connections
        global_constraints: Global constraints applied to the FDL document
        batch_layouts: List of batch layout definitions
    """
    fdl_version: str = "0.1"
    units: FDLUnits = field(default_factory=FDLUnits)
    site: Optional[Site] = None
    global_constraints: GlobalConstraints = field(default_factory=GlobalConstraints)
    batch_layouts: List[BatchLayout] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "fdl_version": self.fdl_version,
            "units": self.units.to_dict(),
            "global_constraints": self.global_constraints.to_dict(),
            "batch_layouts": [layout.__dict__ for layout in self.batch_layouts] # Simplified for now
        }
        if self.site:
            site_dict = self.site.__dict__.copy()
            site_dict["areas"] = []
            for area in self.site.areas:
                area_dict = area.__dict__.copy()
                area_dict["instances"] = [inst.__dict__ for inst in area.instances]
                area_dict["connections"] = [conn.__dict__ for conn in area.connections]
                site_dict["areas"].append(area_dict)
            data["site"] = site_dict
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FDL":
        fdl_units = FDLUnits.from_dict(data.get("units", {}))
        global_constraints = GlobalConstraints.from_dict(data.get("global_constraints", {}))
        
        site_data = data.get("site")
        site = None
        if site_data:
            areas = []
            for area_data in site_data.get("areas", []):
                instances = [AssetInstance(**inst_data) for inst_data in area_data.get("instances", [])]
                connections = [Connection(**conn_data) for conn_data in area_data.get("connections", [])]
                areas.append(Area(
                    name=area_data["name"],
                    area_id=area_data["area_id"],
                    type=area_data.get("type", "production"),
                    instances=instances,
                    connections=connections
                ))
            site = Site(
                name=site_data["name"],
                site_id=site_data["site_id"],
                location=site_data.get("location"),
                areas=areas
            )
        
        batch_layouts = [BatchLayout(**layout_data) for layout_data in data.get("batch_layouts", [])]

        return cls(
            fdl_version=data.get("fdl_version", "0.1"),
            units=fdl_units,
            site=site,
            global_constraints=global_constraints,
            batch_layouts=batch_layouts
        )


if __name__ == "__main__":
    from ..tags.id_generator import generate_uuidv7
    
    print("=== FDL Models Demo ===\n")
    
    # Create a simple FDL object
    fdl_obj = FDL(
        site=Site(
            name="Demo Site",
            site_id=generate_uuidv7(),
            location={"latitude": 34.0, "longitude": -118.0, "altitude": 10.0},
            areas=[
                Area(
                    name="Production Area",
                    area_id=generate_uuidv7(),
                    type="production",
                    instances=[
                        AssetInstance(
                            instance_id="pump_001",
                            ref_asset=generate_uuidv7(),
                            transform=Transform(translation=[10.0, 5.0, 0.0])
                        ),
                        AssetInstance(
                            instance_id="valve_001",
                            ref_asset=generate_uuidv7(),
                            transform=Transform(translation=[12.0, 5.0, 0.0])
                        )
                    ],
                    connections=[
                        Connection(
                            connection_id="pipe_001",
                            type="pipe",
                            from_instance="pump_001",
                            to_instance="valve_001"
                        )
                    ]
                )
            ]
        ),
        global_constraints=GlobalConstraints(
            scaling_constraints=ScalingConstraints(allow_scaling=False),
            collision_detection=CollisionDetection(enabled=True, clearance_distance=0.1)
        ),
        batch_layouts=[
            BatchLayout(
                layout_id="grid_layout_001",
                type="grid",
                ref_asset=generate_uuidv7(),
                params={
                    "rows": 2,
                    "columns": 2,
                    "spacing_x": 5.0,
                    "spacing_y": 5.0,
                    "origin": [0.0, 0.0, 0.0]
                }
            )
        ]
    )
    
    # Convert to dict and print
    fdl_dict = fdl_obj.to_dict()
    import json
    print(json.dumps(fdl_dict, indent=2))

    # Create from dict
    print("\nCreating FDL from dict...")
    fdl_from_dict = FDL.from_dict(fdl_dict)
    print(f"FDL Version: {fdl_from_dict.fdl_version}")
    print(f"Site Name: {fdl_from_dict.site.name}")
    print(f"First Area: {fdl_from_dict.site.areas[0].name}")
    print(f"First Instance: {fdl_from_dict.site.areas[0].instances[0].instance_id}")
    print(f"Global Scaling Allowed: {fdl_from_dict.global_constraints.scaling_constraints.allow_scaling}")
    print(f"Batch Layouts: {len(fdl_from_dict.batch_layouts)}")

