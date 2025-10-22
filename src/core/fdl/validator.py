from typing import List, Tuple, Optional, Any, Dict
from dataclasses import dataclass, field

from .models import FDL, Site, Area, AssetInstance, Connection, BatchLayout, ScalingConstraints, GlobalConstraints
from ..tags.id_generator import is_valid_uuidv7


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
        return f"ValidationError(field=\\'{self.field}\\' , message=\\'{self.message}\\' )"


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
    
    def validate_site(self, site: Site) -> bool:
        """
        Validate a Site object against FDL v0.1 specification.
        
        Args:
            site: The Site object to validate.
        
        Returns:
            bool: True if the Site is valid, False otherwise.
        """
        self.errors = []  # Reset errors for each validation run
        
        # Validate site_id
        if not is_valid_uuidv7(site.site_id):
            self._add_error("site_id", f"Invalid UUIDv7 format for site_id: {site.site_id}")

        # Validate site name
        if not site.name or not site.name.strip():
            self._add_error("name", "Site name cannot be empty.")

        # Validate areas
        area_ids = set()
        for i, area in enumerate(site.areas):
            self._validate_area(area, i)
            if area.area_id in area_ids:
                self._add_error(f"areas[{i}].area_id", f"Duplicate area_id: {area.area_id}")
            area_ids.add(area.area_id)

        return not self.errors

    def _validate_area(self, area: Area, index: int):
        """
        Validate Area object.
        """
        field_prefix = f"areas[{index}]"
        if not area.name or not area.name.strip():
            self._add_error(f"{field_prefix}.name", "Area name cannot be empty.")

        if not is_valid_uuidv7(area.area_id):
            self._add_error(f"{field_prefix}.area_id", f"Invalid UUIDv7 format for area_id: {area.area_id}")

        instance_ids = set()
        for i, instance in enumerate(area.instances):
            self._validate_asset_instance(instance, f"{field_prefix}.instances[{i}]")
            if instance.instance_id in instance_ids:
                self._add_error(f"{field_prefix}.instances[{i}].instance_id", f"Duplicate instance_id: {instance.instance_id}")
            instance_ids.add(instance.instance_id)

        connection_ids = set()
        for i, connection in enumerate(area.connections):
            self._validate_connection(connection, f"{field_prefix}.connections[{i}]", instance_ids)
            if connection.connection_id in connection_ids:
                self._add_error(f"{field_prefix}.connections[{i}].connection_id", f"Duplicate connection_id: {connection.connection_id}")
            connection_ids.add(connection.connection_id)

    def _validate_asset_instance(self, instance: AssetInstance, field_path: str):
        """
        Validate AssetInstance object.
        """
        if not instance.instance_id or not instance.instance_id.strip():
            self._add_error(f"{field_path}.instance_id", "Instance ID cannot be empty.")

        if not instance.ref_asset or not instance.ref_asset.strip():
            self._add_error(f"{field_path}.ref_asset", "Reference asset ID cannot be empty.")

        # Transform validation (basic check for now, more detailed in IADL Validator)
        if not instance.transform:
            self._add_error(f"{field_path}.transform", "Transform cannot be empty.")

        # tag_overrides validation (basic check)
        for i, override in enumerate(instance.tag_overrides):
            if "tag_id" not in override:
                self._add_error(f"{field_path}.tag_overrides[{i}]", "Tag override must specify a tag_id.")
            if not is_valid_uuidv7(override.get("tag_id", "")):
                self._add_error(f"{field_path}.tag_overrides[{i}].tag_id", f"Invalid UUIDv7 format for tag_id: {override.get('tag_id')}")

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
        is_valid = validator.validate_site(valid_fdl.site) # Validate site object from FDL
        print(f"Is Valid: {is_valid}")
        if not is_valid:
            for error in validator.get_errors():
                print(f"  Error: {error}")
    else:
        print(f"Test file not found: {valid_fdl_path}")
    print()

    # --- Test Case 2: Invalid FDL (missing site, invalid UUID, duplicate instance_id, invalid transform) ---
    print("--- Test Case 2: Invalid FDL ---")
    invalid_site_data = {
        "site_id": "invalid-uuid", # Invalid UUID
        "name": "Invalid Site",
        "units": {"length": "m", "angle": "deg", "up_axis": "Z", "handedness": "right"},
        "areas": [
            {
                "area_id": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e01",
                "name": "Area 1",
                "instances": [
                    {
                        "instance_id": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e02",
                        "ref_asset": "asset_a",
                        "transform": {"translation": [0,0,0], "rotation": [0,0,0], "scale": [0.5, 1.0, 1.0]} # Invalid scale
                    },
                    {
                        "instance_id": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e02", # Duplicate
                        "ref_asset": "asset_b",
                        "transform": {"translation": [1,1,1], "rotation": [0,0,0], "scale": [1,1,1]}
                    }
                ],
                "connections": [],
                "batch_layouts": []
            }
        ]
    }
    try:
        invalid_site = Site.from_dict(invalid_site_data)
        is_valid = validator.validate_site(invalid_site)
        print(f"Is Valid: {is_valid}")
        if not is_valid:
            for error in validator.get_errors():
                print(f"  Error: {error}")
    except Exception as e:
        print(f"Error creating Site from dict: {e}")
    print()

    # --- Test Case 3: Invalid FDL (duplicate area_id, instance_id, connection_id) ---
    print("--- Test Case 3: Invalid FDL (duplicate area_id, instance_id, connection_id) ---")
    duplicate_id_site_data = {
        "site_id": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e00",
        "name": "Duplicate ID Site",
        "units": {"length": "m", "angle": "deg", "up_axis": "Z", "handedness": "right"},
        "areas": [
            {
                "area_id": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e01",
                "name": "Area 1",
                "instances": [
                    {
                        "instance_id": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e02",
                        "ref_asset": "asset_a",
                        "transform": {"translation": [0,0,0], "rotation": [0,0,0], "scale": [1,1,1]}
                    }
                ],
                "connections": [
                    {
                        "connection_id": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e03",
                        "type": "pipe",
                        "from_instance": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e02",
                        "to_instance": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e04" # Non-existent
                    }
                ],
                "batch_layouts": []
            },
            {
                "area_id": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e01", # Duplicate
                "name": "Area 2",
                "instances": [],
                "connections": [],
                "batch_layouts": []
            }
        ]
    }
    try:
        duplicate_id_site = Site.from_dict(duplicate_id_site_data)
        is_valid = validator.validate_site(duplicate_id_site)
        print(f"Is Valid: {is_valid}")
        if not is_valid:
            for error in validator.get_errors():
                print(f"  Error: {error}")
    except Exception as e:
        print(f"Error creating Site from dict: {e}")
    print()

    # --- Test Case 4: Invalid Batch Layout --- 
    print("--- Test Case 4: Invalid Batch Layout ---")
    invalid_batch_layout_site_data = {
        "site_id": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e00",
        "name": "Batch Layout Test Site",
        "units": {"length": "m", "angle": "deg", "up_axis": "Z", "handedness": "right"},
        "areas": [
            {
                "area_id": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e01",
                "name": "Area 1",
                "instances": [],
                "connections": [],
                "batch_layouts": [
                    {
                        "layout_id": "batch_grid_1",
                        "type": "grid",
                        "ref_asset": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e02",
                        "params": {"rows": 2, "columns": 2} # Missing spacing_x, spacing_y, origin
                    },
                    {
                        "layout_id": "batch_line_1",
                        "type": "line",
                        "ref_asset": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e03",
                        "params": {"count": 5, "start": [0,0,0]} # Missing end
                    }
                ]
            }
        ]
    }
    try:
        invalid_batch_layout_site = Site.from_dict(invalid_batch_layout_site_data)
        is_valid = validator.validate_site(invalid_batch_layout_site)
        print(f"Is Valid: {is_valid}")
        if not is_valid:
            for error in validator.get_errors():
                print(f"  Error: {error}")
    except Exception as e:
        print(f"Error creating Site from dict: {e}")
    print()

    # --- Test Case 5: Valid Batch Layout (Grid) ---
    print("--- Test Case 5: Valid Batch Layout (Grid) ---")
    valid_batch_layout_site_data = {
        "site_id": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e00",
        "name": "Valid Batch Layout Site",
        "units": {"length": "m", "angle": "deg", "up_axis": "Z", "handedness": "right"},
        "areas": [
            {
                "area_id": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e01",
                "name": "Area 1",
                "instances": [],
                "connections": [],
                "batch_layouts": [
                    {
                        "layout_id": "batch_grid_1",
                        "type": "grid",
                        "ref_asset": "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e02",
                        "params": {"rows": 2, "columns": 2, "spacing_x": 1.0, "spacing_y": 1.0, "origin": [0,0,0]}
                    }
                ]
            }
        ]
    }
    try:
        valid_batch_layout_site = Site.from_dict(valid_batch_layout_site_data)
        is_valid = validator.validate_site(valid_batch_layout_site)
        print(f"Is Valid: {is_valid}")
        if not is_valid:
            for error in validator.get_errors():
                print(f"  Error: {error}")
    except Exception as e:
        print(f"Error creating Site from dict: {e}")
    print()




