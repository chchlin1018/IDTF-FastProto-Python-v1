"""
IADL Validator - Validate Asset against IADL v1.0 specification
"""

from typing import List, Tuple, Optional
from .models import Asset, Units, Transform
from ..tags.id_generator import is_valid_uuidv7
from ..tags.models import Tag


class ValidationError:
    """
    Represents a single validation error.
    
    Attributes:
        field: The field path where the error occurred (e.g., "asset_id", "tags[0].tag_id")
        message: A descriptive error message
    """
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
    
    def __str__(self):
        return f"{self.field}: {self.message}"
    
    def __repr__(self):
        return f"ValidationError(field=\'{self.field}\', message=\'{self.message}\')"


class IADLValidator:
    """
    IADL v1.0 Validator.
    Provides methods to validate an Asset object against predefined rules.
    """
    
    def __init__(self):
        self.errors: List[ValidationError] = []
    
    def _add_error(self, field: str, message: str):
        """Helper to add a validation error."""
        self.errors.append(ValidationError(field, message))
    
    def validate_asset(self, asset: Asset) -> bool:
        """
        Validate an Asset object against IADL v1.0 specification.
        
        Args:
            asset: The Asset object to validate.
        
        Returns:
            bool: True if the asset is valid, False otherwise.
        """
        self.errors = []  # Reset errors for each validation run
        
        # Validate asset_id (UUIDv7)
        if not asset.asset_id:
            self._add_error("asset_id", "Asset ID cannot be empty.")
        elif not is_valid_uuidv7(asset.asset_id):
            self._add_error("asset_id", f"Invalid UUIDv7 format: {asset.asset_id}")
        
        # Validate name
        if not asset.name or not asset.name.strip():
            self._add_error("name", "Asset name cannot be empty.")
        
        # Validate model_ref
        if not asset.model_ref or not asset.model_ref.strip():
            self._add_error("model_ref", "Model reference cannot be empty.")
        
        # Validate units
        self._validate_units(asset.units)
        
        # Validate default_xform
        self._validate_transform("default_xform", asset.default_xform, allow_scaling=True, allow_non_uniform_scaling=False)
        
        # Validate tags
        self._validate_tags(asset.tags)
        
        return not self.errors
    
    def _validate_units(self, units: Units):
        """Validate Units object."""
        try:
            units.validate()
        except ValueError as e:
            self._add_error("units", str(e))
    
    def _validate_transform(self, field_path: str, transform: Transform, allow_scaling: bool, allow_non_uniform_scaling: bool):
        """Validate Transform object."""
        try:
            transform.validate(allow_scaling=allow_scaling, allow_non_uniform_scaling=allow_non_uniform_scaling)
        except ValueError as e:
            self._add_error(field_path, str(e))
    
    def _validate_tags(self, tags: List[Tag]):
        """Validate list of Tag objects."""
        tag_ids = set()
        for i, tag in enumerate(tags):
            field_prefix = f"tags[{i}]"
            
            # Check tag_id uniqueness
            if tag.tag_id in tag_ids:
                self._add_error(f"{field_prefix}.tag_id", f"Duplicate tag_id: {tag.tag_id}")
            tag_ids.add(tag.tag_id)
            
            # Validate tag_id (UUIDv7)
            if not tag.tag_id:
                self._add_error(f"{field_prefix}.tag_id", "Tag ID cannot be empty.")
            elif not is_valid_uuidv7(tag.tag_id):
                self._add_error(f"{field_prefix}.tag_id", f"Invalid UUIDv7 format: {tag.tag_id}")
            
            # Validate tag attachment
            try:
                tag._validate()
            except ValueError as e:
                self._add_error(field_prefix, str(e))
    
    def get_errors(self) -> List[ValidationError]:
        """
        Get all validation errors.
        
        Returns:
            List[ValidationError]: A list of ValidationError objects.
        """
        return self.errors


if __name__ == '__main__':
    from src.core.tags.id_generator import generate_asset_id, generate_tag_id
    from src.core.tags.models import TagKind, AttachmentStrategy
    
    print("=== IADL Validator Demo ===\n")
    validator = IADLValidator()
    
    # --- Test Case 1: Valid Asset ---
    print("--- Test Case 1: Valid Asset ---")
    valid_asset = Asset(
        asset_id=generate_asset_id(),
        name="Valid Pump",
        description="A perfectly valid pump asset.",
        model_ref="@/assets/pumps/valid_pump.usd@</Pump>",
        units=Units(length="m"),
        default_xform=Transform(scale=[1.0, 1.0, 1.0]),
        tags=[
            Tag(
                tag_id=generate_tag_id(),
                name="Temp Sensor",
                kind=TagKind.SENSOR,
                eu_unit="°C",
                attachment_strategy=AttachmentStrategy.BY_POSITION,
                local_position=[0.1, 0.2, 0.3]
            ),
            Tag(
                tag_id=generate_tag_id(),
                name="Pressure Gauge",
                kind=TagKind.SENSOR,
                eu_unit="psi",
                attachment_strategy=AttachmentStrategy.BY_PRIM,
                attach_prim_path="/Pump/Gauge"
            )
        ]
    )
    
    is_valid = validator.validate_asset(valid_asset)
    print(f"Is Valid: {is_valid}")
    if not is_valid:
        for error in validator.get_errors():
            print(f"  Error: {error}")
    print()
    
    # --- Test Case 2: Invalid Asset (Missing fields, invalid UUID, duplicate tag_id) ---
    print("--- Test Case 2: Invalid Asset ---")
    invalid_asset = Asset(
        asset_id="not-a-uuid",  # Invalid UUID
        name="",  # Empty name
        description="An invalid asset for testing.",
        model_ref="",  # Empty model_ref
        units=Units(length="km"),  # Invalid unit
        default_xform=Transform(scale=[1.0, 2.0, 1.0]), # Non-uniform scaling not allowed by default
        tags=[
            Tag(
                tag_id="018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1a",
                name="Tag A",
                kind=TagKind.SENSOR,
                eu_unit="V",
                attachment_strategy=AttachmentStrategy.BY_POSITION,
                local_position=[0.0, 0.0, 0.0]
            ),
            Tag(
                tag_id="018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1a",  # Duplicate tag_id
                name="Tag B",
                kind=TagKind.SENSOR,
                eu_unit="A",
                attachment_strategy=AttachmentStrategy.BY_PRIM,
                attach_prim_path="invalid_path" # attach_prim_path must start with /
            )
        ]
    )
    
    is_valid = validator.validate_asset(invalid_asset)
    print(f"Is Valid: {is_valid}")
    if not is_valid:
        for error in validator.get_errors():
            print(f"  Error: {error}")
    print()

    # --- Test Case 3: Invalid Tag (missing localPosition for BY_POSITION) ---
    print("--- Test Case 3: Invalid Tag (missing localPosition) ---")
    invalid_tag_asset = Asset(
        asset_id=generate_asset_id(),
        name="Asset with invalid tag",
        model_ref="@/model.usd@",
        tags=[
            Tag(
                tag_id=generate_tag_id(),
                name="Bad Tag",
                kind=TagKind.SENSOR,
                attachment_strategy=AttachmentStrategy.BY_POSITION,
                # local_position is missing here
            )
        ]
    )
    is_valid = validator.validate_asset(invalid_tag_asset)
    print(f"Is Valid: {is_valid}")
    if not is_valid:
        for error in validator.get_errors():
            print(f"  Error: {error}")
    print()

    # --- Test Case 4: Invalid Tag (missing attachPrimPath for BY_PRIM) ---
    print("--- Test Case 4: Invalid Tag (missing attachPrimPath) ---")
    invalid_tag_asset_2 = Asset(
        asset_id=generate_asset_id(),
        name="Asset with invalid tag 2",
        model_ref="@/model.usd@",
        tags=[
            Tag(
                tag_id=generate_tag_id(),
                name="Bad Tag 2",
                kind=TagKind.SENSOR,
                attachment_strategy=AttachmentStrategy.BY_PRIM,
                # attach_prim_path is missing here
            )
        ]
    )
    is_valid = validator.validate_asset(invalid_tag_asset_2)
    print(f"Is Valid: {is_valid}")
    if not is_valid:
        for error in validator.get_errors():
            print(f"  Error: {error}")
    print()

    # --- Test Case 5: Valid Asset with non-uniform scaling allowed ---
    print("--- Test Case 5: Valid Asset with non-uniform scaling allowed ---")
    # Note: This test case demonstrates how to use the validator, but the Asset model's
    # default_xform.validate method currently hardcodes allow_non_uniform_scaling=False.
    # For this to pass, the Asset.validate() method or default_xform.validate() would need 
    # to be updated to accept these parameters dynamically.
    # For now, this will still fail due to the hardcoded validation in models.py.
    # This highlights a point for future refinement in the Asset model's validation logic.
    
    # To make this truly pass, the Asset.validate method would need to pass these flags
    # to default_xform.validate based on some asset-level configuration.
    # For demonstration, we'll show it failing as expected with current models.py logic.
    
    asset_with_non_uniform_scale = Asset(
        asset_id=generate_asset_id(),
        name="Scaled Asset",
        model_ref="@/scaled.usd@",
        units=Units(length="m"),
        default_xform=Transform(scale=[1.0, 2.0, 3.0]) # Non-uniform scale
    )
    is_valid = validator.validate_asset(asset_with_non_uniform_scale)
    print(f"Is Valid (non-uniform scale): {is_valid}")
    if not is_valid:
        for error in validator.get_errors():
            print(f"  Error: {error}")
    print()

