"""
FDL Validator - Validate FDL against FDL v0.1 specification
"""

from typing import List, Tuple, Dict, Any
from .models import FDL, Site, Area, AssetInstance, Connection, GlobalConstraints, ScalingConstraints, CollisionDetection, BatchLayout
from ..tags.id_generator import is_valid_uuidv7
from ..iadl.models import Transform


class ValidationError:
    """
    Represents a single validation error.
    
    Attributes:
        field: The field path where the error occurred (e.g., "site.areas[0].instances[1].instance_id")
        message: A descriptive error message
    """
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
    
    def __str__(self):
        return f"{self.field}: {self.message}"
    
    def __repr__(self):
        return f"ValidationError(field=\\'{self.field}\\, message=\\'{self.message}\\'")"


class FDLValidator:
    """
    FDL v0.1 Validator.
    Provides methods to validate an FDL object against predefined rules.
    """
    
    def __init__(self):
        self.errors: List[ValidationError] = []
    
    def _add_error(self, field: str, message: str):
        """Helper to add a validation error."""
        self.errors.append(ValidationError(field, message))
    
    def validate_fdl(self, fdl: FDL) -> bool:
        """
        Validate an FDL object against FDL v0.1 specification.
        
        Args:
            fdl: The FDL object to validate.
        
        Returns:
            bool: True if the FDL is valid, False otherwise.
        """
        self.errors = []  # Reset errors for each validation run
        
        # Validate fdl_version
        if fdl.fdl_version != "0.1":
            self._add_error("fdl_version", f"Unsupported FDL version: {fdl.fdl_version}. Expected 0.1")
        
        # Validate units (basic check, more detailed in models)
        try:
            fdl.units.to_dict() # Trigger validation in from_dict if any enum value is invalid
        except ValueError as e:
            self._add_error("units", str(e))

        # Validate global constraints
        self._validate_global_constraints(fdl.global_constraints)

        # Validate site
        if fdl.site:
            self._validate_site(fdl.site, fdl.global_constraints.scaling_constraints)
        else:
            self._add_error("site", "FDL must contain a site definition.")

        # Validate batch layouts (basic structure)
        self._validate_batch_layouts(fdl.batch_layouts)

        return not self.errors

    def _validate_global_constraints(self, constraints: GlobalConstraints):
        """Validate global constraints."""
        if constraints.collision_detection.enabled and constraints.collision_detection.clearance_distance < 0:
            self._add_error("global_constraints.collision_detection.clearance_distance", "Clearance distance cannot be negative.")

    def _validate_site(self, site: Site, global_scaling_constraints: ScalingConstraints):
        """
        Validate Site object.
        """
        if not site.name or not site.name.strip():
            self._add_error("site.name", "Site name cannot be empty.")
        
        if not is_valid_uuidv7(site.site_id):
            self._add_error("site.site_id", f"Invalid UUIDv7 format: {site.site_id}")

        area_ids = set()
        for i, area in enumerate(site.areas):
            self._validate_area(area, i, global_scaling_constraints)
            if area.area_id in area_ids:
                self._add_error(f"site.areas[{i}].area_id", f"Duplicate area_id: {area.area_id}")
            area_ids.add(area.area_id)

    def _validate_area(self, area: Area, index: int, global_scaling_constraints: ScalingConstraints):
        """
        Validate Area object.
        """
        field_prefix = f"site.areas[{index}]"
        if not area.name or not area.name.strip():
            self._add_error(f"{field_prefix}.name", "Area name cannot be empty.")

        if not is_valid_uuidv7(area.area_id):
            self._add_error(f"{field_prefix}.area_id", f"Invalid UUIDv7 format: {area.area_id}")

        instance_ids = set()
        for i, instance in enumerate(area.instances):
            self._validate_asset_instance(instance, f"{field_prefix}.instances[{i}]", global_scaling_constraints)
            if instance.instance_id in instance_ids:
                self._add_error(f"{field_prefix}.instances[{i}].instance_id", f"Duplicate instance_id: {instance.instance_id}")
            instance_ids.add(instance.instance_id)

        connection_ids = set()
        for i, connection in enumerate(area.connections):
            self._validate_connection(connection, f"{field_prefix}.connections[{i}]", instance_ids)
            if connection.connection_id in connection_ids:
                self._add_error(f"{field_prefix}.connections[{i}].connection_id", f"Duplicate connection_id: {connection.connection_id}")
            connection_ids.add(connection.connection_id)

    def _validate_asset_instance(self, instance: AssetInstance, field_path: str, global_scaling_constraints: ScalingConstraints):
        """
        Validate AssetInstance object.
        """
        if not instance.instance_id or not instance.instance_id.strip():
            self._add_error(f"{field_path}.instance_id", "Instance ID cannot be empty.")

        if not instance.ref_asset or not instance.ref_asset.strip():
            self._add_error(f"{field_path}.ref_asset", "Reference asset ID cannot be empty.")

        # Validate transform based on global scaling constraints
        try:
            instance.transform.validate(
                allow_scaling=global_scaling_constraints.allow_scaling,
                allow_non_uniform_scaling=global_scaling_constraints.allow_non_uniform_scaling
            )
            # Further check min/max scale if applicable
            if global_scaling_constraints.min_scale is not None and any(s < global_scaling_constraints.min_scale for s in instance.transform.scale):
                self._add_error(f"{field_path}.transform.scale", f"Scale factors must be >= {global_scaling_constraints.min_scale}")
            if global_scaling_constraints.max_scale is not None and any(s > global_scaling_constraints.max_scale for s in instance.transform.scale):
                self._add_error(f"{field_path}.transform.scale", f"Scale factors must be <= {global_scaling_constraints.max_scale}")

        except ValueError as e:
            self._add_error(f"{field_path}.transform", str(e))

        # tag_overrides validation (basic check)
        for i, override in enumerate(instance.tag_overrides):
            if "tag_id" not in override:
                self._add_error(f"{field_path}.tag_overrides[{i}]", "Tag override must specify a tag_id.")
            if not is_valid_uuidv7(override.get("tag_id", "")):
                self._add_error(f"{field_path}.tag_overrides[{i}].tag_id", f"Invalid UUIDv7 format for tag_id: {override.get("tag_id")}")

    def _validate_connection(self, connection: Connection, field_path: str, instance_ids: set):
        """
        Validate Connection object.
        """
        if not connection.connection_id or not connection.connection_id.strip():
            self._add_error(f"{field_path}.connection_id", "Connection ID cannot be empty.")
        
        if not connection.type or not connection.type.strip():
            self._add_error(f"{field_path}.type", "Connection type cannot be empty.")
        
        if not connection.from_instance or connection.from_instance not in instance_ids:
            self._add_error(f"{field_path}.from_instance", f"from_instance '{connection.from_instance}' not found in area instances.")
        
        if not connection.to_instance or connection.to_instance not in instance_ids:
            self._add_error(f"{field_path}.to_instance", f"to_instance '{connection.to_instance}' not found in area instances.")

        # Basic path validation (e.g. check for 'points' if type is 'line')
        if connection.path and connection.path.get("type") == "line":
            if not connection.path.get("points") or not isinstance(connection.path["points"], list) or len(connection.path["points"]) < 2:
                self._add_error(f"{field_path}.path.points", "Line path must have at least 2 points.")

    def _validate_batch_layouts(self, batch_layouts: List[BatchLayout]):
        """
        Validate batch layout definitions.
        """
        layout_ids = set()
        for i, layout in enumerate(batch_layouts):
            field_prefix = f"batch_layouts[{i}]"
            if layout.layout_id in layout_ids:
                self._add_error(f"{field_prefix}.layout_id", f"Duplicate layout_id: {layout.layout_id}")
            layout_ids.add(layout.layout_id)

            if not layout.type or layout.type not in ["grid", "line", "circle"]:
                self._add_error(f"{field_prefix}.type", f"Invalid batch layout type: {layout.type}. Must be one of [grid, line, circle]")
            
            if not layout.ref_asset or not layout.ref_asset.strip():
                self._add_error(f"{field_prefix}.ref_asset", "Reference asset ID for batch layout cannot be empty.")
            
            # Basic params validation for each type
            if layout.type == "grid":
                required_params = ["rows", "columns", "spacing_x", "spacing_y", "origin"]
                for param in required_params:
                    if param not in layout.params:
                        self._add_error(f"{field_prefix}.params.{param}", f"Missing required parameter for grid layout: {param}")
            elif layout.type == "line":
                required_params = ["count", "start", "end"]
                for param in required_params:
                    if param not in layout.params:
                        self._add_error(f"{field_prefix}.params.{param}", f"Missing required parameter for line layout: {param}")
            elif layout.type == "circle":
                required_params = ["count", "center", "radius"]
                for param in required_params:
                    if param not in layout.params:
                        self._add_error(f"{field_prefix}.params.{param}", f"Missing required parameter for circle layout: {param}")

    def get_errors(self) -> List[ValidationError]:
        """
        Get all validation errors.
        
        Returns:
            List[ValidationError]: A list of ValidationError objects.
        """
        return self.errors


if __name__ == '__main__':
    from src.core.tags.id_generator import generate_uuidv7
    from src.core.iadl.models import Transform
    from src.core.fdl.parser import parse_fdl_file
    from pathlib import Path

    print("=== FDL Validator Demo ===\n")
    validator = FDLValidator()

    # --- Test Case 1: Valid FDL from test file ---
    print("--- Test Case 1: Valid FDL (semiconductor_fab.yaml) ---")
    valid_fdl_path = Path("testfiles/FDL/semiconductor_fab.yaml")
    if valid_fdl_path.exists():
        valid_fdl = parse_fdl_file(valid_fdl_path)
        is_valid = validator.validate_fdl(valid_fdl)
        print(f"Is Valid: {is_valid}")
        if not is_valid:
            for error in validator.get_errors():
                print(f"  Error: {error}")
    else:
        print(f"Test file not found: {valid_fdl_path}")
    print()

    # --- Test Case 2: Invalid FDL (missing site, invalid UUID, duplicate instance_id, invalid transform) ---
    print("--- Test Case 2: Invalid FDL ---")
    invalid_fdl_data = {
        "fdl_version": "0.1",
        "units": {"length": "m", "angle": "deg", "up_axis": "Z", "handedness": "right"},
        # "site": missing
        "global_constraints": {
            "scaling_constraints": {"allow_scaling": False, "allow_non_uniform_scaling": False, "min_scale": 0.1, "max_scale": 1.5},
            "collision_detection": {"enabled": True, "clearance_distance": -0.5}
        },
        "batch_layouts": [
            {
                "layout_id": "test_grid_001",
                "type": "grid",
                "ref_asset": "invalid-uuid", # Invalid UUID
                "params": {"rows": 2, "columns": 2, "spacing_x": 1.0, "spacing_y": 1.0}
            }
        ]
    }
    try:
        invalid_fdl = FDL.from_dict(invalid_fdl_data)
        is_valid = validator.validate_fdl(invalid_fdl)
        print(f"Is Valid: {is_valid}")
        if not is_valid:
            for error in validator.get_errors():
                print(f"  Error: {error}")
    except Exception as e:
        print(f"Error creating FDL from dict: {e}")
    print()

    # --- Test Case 3: Invalid FDL (duplicate area_id, instance_id, connection_id) ---
    print("--- Test Case 3: Invalid FDL (duplicates) ---")
    duplicate_id_fdl = FDL(
        site=Site(
            name="Duplicate ID Site",
            site_id=generate_uuidv7(),
            areas=[
                Area(
                    name="Area A",
                    area_id="018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e21",
                    instances=[
                        AssetInstance(
                            instance_id="pump_001",
                            ref_asset=generate_uuidv7(),
                            transform=Transform()
                        ),
                        AssetInstance(
                            instance_id="pump_001", # Duplicate instance_id
                            ref_asset=generate_uuidv7(),
                            transform=Transform()
                        )
                    ],
                    connections=[
                        Connection(
                            connection_id="pipe_001",
                            type="pipe",
                            from_instance="pump_001",
                            to_instance="pump_001"
                        ),
                        Connection(
                            connection_id="pipe_001", # Duplicate connection_id
                            type="pipe",
                            from_instance="pump_001",
                            to_instance="pump_001"
                        )
                    ]
                ),
                Area(
                    name="Area B",
                    area_id="018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e21", # Duplicate area_id
                    instances=[],
                    connections=[]
                )
            ]
        )
    )
    is_valid = validator.validate_fdl(duplicate_id_fdl)
    print(f"Is Valid: {is_valid}")
    if not is_valid:
        for error in validator.get_errors():
            print(f"  Error: {error}")
    print()

    # --- Test Case 4: Invalid Transform in Instance (violates global_constraints) ---
    print("--- Test Case 4: Invalid Transform in Instance ---")
    constrained_fdl = FDL(
        site=Site(
            name="Constrained Site",
            site_id=generate_uuidv7(),
            areas=[
                Area(
                    name="Area C",
                    area_id=generate_uuidv7(),
                    instances=[
                        AssetInstance(
                            instance_id="scaled_asset",
                            ref_asset=generate_uuidv7(),
                            transform=Transform(scale=[2.0, 2.0, 2.0]) # Violates max_scale=1.5
                        )
                    ]
                )
            ]
        ),
        global_constraints=GlobalConstraints(
            scaling_constraints=ScalingConstraints(allow_scaling=True, allow_non_uniform_scaling=False, min_scale=0.5, max_scale=1.5)
        )
    )
    is_valid = validator.validate_fdl(constrained_fdl)
    print(f"Is Valid: {is_valid}")
    if not is_valid:
        for error in validator.get_errors():
            print(f"  Error: {error}")
    print()

    # --- Test Case 5: Invalid Batch Layout --- 
    print("--- Test Case 5: Invalid Batch Layout ---")
    invalid_batch_fdl = FDL(
        site=Site(
            name="Site with bad layout",
            site_id=generate_uuidv7(),
            areas=[]
        ),
        batch_layouts=[
            BatchLayout(
                layout_id="bad_grid",
                type="grid",
                ref_asset=generate_uuidv7(),
                params={"rows": 2, "columns": 2, "spacing_x": 1.0} # Missing spacing_y and origin
            ),
            BatchLayout(
                layout_id="bad_type",
                type="unknown", # Invalid type
                ref_asset=generate_uuidv7(),
                params={}
            )
        ]
    )
    is_valid = validator.validate_fdl(invalid_batch_fdl)
    print(f"Is Valid: {is_valid}")
    if not is_valid:
        for error in validator.get_errors():
            print(f"  Error: {error}")
    print()

