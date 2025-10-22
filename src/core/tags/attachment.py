"""
Tag Attachment Strategy

This module provides utilities for handling tag attachment strategies.
"""

from typing import List, Optional, Tuple
from .models import Tag, AttachmentStrategy


def compute_tag_world_position(
    tag: Tag,
    asset_world_transform: List[List[float]],
    prim_local_transform: Optional[List[List[float]]] = None
) -> List[float]:
    """
    Compute tag's world position based on attachment strategy.
    
    Args:
        tag: Tag instance
        asset_world_transform: Asset's world transform matrix (4x4)
        prim_local_transform: Prim's local transform matrix (4x4), required for by_prim
    
    Returns:
        List[float]: Tag's world position [x, y, z]
    
    Example:
        >>> # By-position tag
        >>> tag = Tag(
        ...     tag_id="...",
        ...     name="Pressure Sensor",
        ...     kind=TagKind.SENSOR,
        ...     attachment_strategy=AttachmentStrategy.BY_POSITION,
        ...     local_position=[1.0, 0.0, 0.5]
        ... )
        >>> asset_transform = [
        ...     [1, 0, 0, 10],
        ...     [0, 1, 0, 5],
        ...     [0, 0, 1, 0],
        ...     [0, 0, 0, 1]
        ... ]
        >>> world_pos = compute_tag_world_position(tag, asset_transform)
        >>> print(world_pos)
        [11.0, 5.0, 0.5]
    """
    if tag.attachment_strategy == AttachmentStrategy.BY_POSITION:
        # By-position: Apply asset world transform to local position
        local_pos = tag.local_position
        if local_pos is None:
            raise ValueError(f"Tag {tag.tag_id}: local_position is None")
        
        world_pos = _transform_point(local_pos, asset_world_transform)
        return world_pos
    
    elif tag.attachment_strategy == AttachmentStrategy.BY_PRIM:
        # By-prim: Apply asset world transform and prim local transform
        if prim_local_transform is None:
            raise ValueError(
                f"Tag {tag.tag_id}: prim_local_transform is required for by_prim attachment"
            )
        
        # Get prim's world position (asset_transform * prim_transform * origin)
        prim_origin = [0.0, 0.0, 0.0]
        prim_world_pos = _transform_point(prim_origin, prim_local_transform)
        world_pos = _transform_point(prim_world_pos, asset_world_transform)
        return world_pos
    
    else:
        raise ValueError(f"Unknown attachment strategy: {tag.attachment_strategy}")


def _transform_point(point: List[float], transform: List[List[float]]) -> List[float]:
    """
    Transform a 3D point by a 4x4 transformation matrix.
    
    Args:
        point: 3D point [x, y, z]
        transform: 4x4 transformation matrix
    
    Returns:
        List[float]: Transformed point [x, y, z]
    """
    x, y, z = point
    
    # Homogeneous coordinates
    new_x = transform[0][0] * x + transform[0][1] * y + transform[0][2] * z + transform[0][3]
    new_y = transform[1][0] * x + transform[1][1] * y + transform[1][2] * z + transform[1][3]
    new_z = transform[2][0] * x + transform[2][1] * y + transform[2][2] * z + transform[2][3]
    
    return [new_x, new_y, new_z]


def validate_tag_attachment(tag: Tag) -> Tuple[bool, Optional[str]]:
    """
    Validate tag attachment configuration.
    
    Args:
        tag: Tag instance
    
    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    
    Example:
        >>> tag = Tag(...)
        >>> is_valid, error_msg = validate_tag_attachment(tag)
        >>> if not is_valid:
        ...     print(f"Error: {error_msg}")
    """
    try:
        tag._validate()
        return True, None
    except ValueError as e:
        return False, str(e)


if __name__ == "__main__":
    # Demo
    from .models import Tag, TagKind
    from .id_generator import generate_tag_id
    
    print("=== Tag Attachment Demo ===\n")
    
    # Create by-position tag
    tag1 = Tag(
        tag_id=generate_tag_id(),
        name="Pressure Sensor",
        kind=TagKind.SENSOR,
        eu_unit="bar",
        attachment_strategy=AttachmentStrategy.BY_POSITION,
        local_position=[1.0, 0.0, 0.5]
    )
    
    # Asset world transform (translation: [10, 5, 0])
    asset_transform = [
        [1, 0, 0, 10],
        [0, 1, 0, 5],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ]
    
    # Compute world position
    world_pos = compute_tag_world_position(tag1, asset_transform)
    print(f"By-Position Tag:")
    print(f"  Local Position: {tag1.local_position}")
    print(f"  Asset Transform: Translation [10, 5, 0]")
    print(f"  World Position: {world_pos}")
    print()
    
    # Create by-prim tag
    tag2 = Tag(
        tag_id=generate_tag_id(),
        name="Flow Sensor",
        kind=TagKind.SENSOR,
        eu_unit="m³/h",
        attachment_strategy=AttachmentStrategy.BY_PRIM,
        attach_prim_path="/Pump/Outlet"
    )
    
    # Prim local transform (translation: [2, 0, 1])
    prim_transform = [
        [1, 0, 0, 2],
        [0, 1, 0, 0],
        [0, 0, 1, 1],
        [0, 0, 0, 1]
    ]
    
    # Compute world position
    world_pos2 = compute_tag_world_position(tag2, asset_transform, prim_transform)
    print(f"By-Prim Tag:")
    print(f"  Attach Prim Path: {tag2.attach_prim_path}")
    print(f"  Prim Local Transform: Translation [2, 0, 1]")
    print(f"  Asset Transform: Translation [10, 5, 0]")
    print(f"  World Position: {world_pos2}")
    print()
    
    # Validate tags
    print("Validation:")
    is_valid1, error1 = validate_tag_attachment(tag1)
    print(f"  Tag 1: {'Valid' if is_valid1 else f'Invalid - {error1}'}")
    
    is_valid2, error2 = validate_tag_attachment(tag2)
    print(f"  Tag 2: {'Valid' if is_valid2 else f'Invalid - {error2}'}")

