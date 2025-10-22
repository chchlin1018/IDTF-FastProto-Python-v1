"""
FDL Batch Layout Generator - Generate AssetInstances from batch layout definitions
"""

from typing import List, Dict, Any, Tuple
import math
from dataclasses import replace

from .models import BatchLayout, AssetInstance, Transform
from ..tags.id_generator import generate_uuidv7


def generate_batch_instances(
    batch_layout: BatchLayout,
    existing_instances: List[AssetInstance] = None
) -> List[AssetInstance]:
    """
    Generates a list of AssetInstance objects based on a BatchLayout definition.
    
    Args:
        batch_layout: The BatchLayout object defining the layout.
        existing_instances: Optional list of existing instances to check for ID conflicts.
    
    Returns:
        List[AssetInstance]: A list of newly generated AssetInstance objects.
    
    Raises:
        ValueError: If the batch_layout type is unsupported or parameters are invalid.
    """
    if existing_instances is None:
        existing_instances = []
    existing_ids = {inst.instance_id for inst in existing_instances}

    generated_instances: List[AssetInstance] = []
    
    if batch_layout.type == "grid":
        generated_instances = _generate_grid_layout(batch_layout, existing_ids)
    elif batch_layout.type == "line":
        generated_instances = _generate_line_layout(batch_layout, existing_ids)
    elif batch_layout.type == "circle":
        generated_instances = _generate_circle_layout(batch_layout, existing_ids)
    else:
        raise ValueError(f"Unsupported batch layout type: {batch_layout.type}")
        
    return generated_instances


def _generate_grid_layout(batch_layout: BatchLayout, existing_ids: set) -> List[AssetInstance]:
    """
    Generates instances for a grid layout.
    """
    params = batch_layout.params
    rows = params.get("rows")
    columns = params.get("columns")
    spacing_x = params.get("spacing_x")
    spacing_y = params.get("spacing_y")
    origin = params.get("origin", [0.0, 0.0, 0.0])

    if not all(isinstance(p, (int, float)) and p >= 0 for p in [rows, columns, spacing_x, spacing_y]):
        raise ValueError("Grid layout parameters (rows, columns, spacing_x, spacing_y) must be non-negative numbers.")
    if not isinstance(origin, list) or len(origin) != 3:
        raise ValueError("Grid layout origin must be a list of 3 numbers.")

    instances: List[AssetInstance] = []
    for r in range(rows):
        for c in range(columns):
            instance_id = f"{batch_layout.naming_prefix}_{r+1}_{c+1}"
            if instance_id in existing_ids:
                # If ID exists, append a UUID to ensure uniqueness
                instance_id = f"{instance_id}_{generate_uuidv7()[:8]}"
            
            x = origin[0] + c * spacing_x
            y = origin[1] + r * spacing_y
            z = origin[2]

            transform = replace(Transform(), translation=[x, y, z]) # Use replace to create a new Transform object
            
            instances.append(AssetInstance(
                instance_id=instance_id,
                ref_asset=batch_layout.ref_asset,
                name=instance_id,
                transform=transform
            ))
    return instances


def _generate_line_layout(batch_layout: BatchLayout, existing_ids: set) -> List[AssetInstance]:
    """
    Generates instances for a line layout.
    """
    params = batch_layout.params
    count = params.get("count")
    start = params.get("start")
    end = params.get("end")

    if not isinstance(count, int) or count <= 0:
        raise ValueError("Line layout count must be a positive integer.")
    if not isinstance(start, list) or len(start) != 3:
        raise ValueError("Line layout start must be a list of 3 numbers.")
    if not isinstance(end, list) or len(end) != 3:
        raise ValueError("Line layout end must be a list of 3 numbers.")

    instances: List[AssetInstance] = []
    for i in range(count):
        instance_id = f"{batch_layout.naming_prefix}_{i+1}"
        if instance_id in existing_ids:
            instance_id = f"{instance_id}_{generate_uuidv7()[:8]}"

        # Linear interpolation
        t = i / (count - 1) if count > 1 else 0.0
        x = start[0] * (1 - t) + end[0] * t
        y = start[1] * (1 - t) + end[1] * t
        z = start[2] * (1 - t) + end[2] * t

        transform = replace(Transform(), translation=[x, y, z])

        instances.append(AssetInstance(
            instance_id=instance_id,
            ref_asset=batch_layout.ref_asset,
            name=instance_id,
            transform=transform
        ))
    return instances


def _generate_circle_layout(batch_layout: BatchLayout, existing_ids: set) -> List[AssetInstance]:
    """
    Generates instances for a circle layout.
    """
    params = batch_layout.params
    count = params.get("count")
    center = params.get("center")
    radius = params.get("radius")
    start_angle_deg = params.get("start_angle", 0.0) # in degrees

    if not isinstance(count, int) or count <= 0:
        raise ValueError("Circle layout count must be a positive integer.")
    if not isinstance(center, list) or len(center) != 3:
        raise ValueError("Circle layout center must be a list of 3 numbers.")
    if not isinstance(radius, (int, float)) or radius <= 0:
        raise ValueError("Circle layout radius must be a positive number.")

    instances: List[AssetInstance] = []
    for i in range(count):
        instance_id = f"{batch_layout.naming_prefix}_{i+1}"
        if instance_id in existing_ids:
            instance_id = f"{instance_id}_{generate_uuidv7()[:8]}"

        angle_rad = math.radians(start_angle_deg + (360.0 / count) * i)
        
        x = center[0] + radius * math.cos(angle_rad)
        y = center[1] + radius * math.sin(angle_rad)
        z = center[2]

        # Optional: Orient asset to face outwards from center
        # rotation_z = math.degrees(angle_rad) + 90 # Rotate 90 degrees for outward facing if asset is X-forward
        # transform = replace(Transform(), translation=[x, y, z], rotation=[0.0, 0.0, rotation_z])
        transform = replace(Transform(), translation=[x, y, z])

        instances.append(AssetInstance(
            instance_id=instance_id,
            ref_asset=batch_layout.ref_asset,
            name=instance_id,
            transform=transform
        ))
    return instances


if __name__ == '__main__':
    print("=== FDL Batch Layout Generator Demo ===\n")

    # Dummy existing instances for ID conflict check
    existing_instances = [AssetInstance(instance_id="Existing_1", ref_asset="dummy_ref")]

    # --- Grid Layout Demo ---
    print("--- Grid Layout ---")
    grid_layout = BatchLayout(
        layout_id="test_grid",
        type="grid",
        ref_asset="018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e12", # Rockwell PLC
        params={
            "rows": 2,
            "columns": 3,
            "spacing_x": 2.0,
            "spacing_y": 1.5,
            "origin": [10.0, 10.0, 0.0]
        },
        naming_prefix="GridPLC"
    )
    grid_instances = generate_batch_instances(grid_layout, existing_instances)
    for inst in grid_instances:
        print(f"Grid Instance: {inst.instance_id}, Pos: {inst.transform.translation}")
    print(f"Generated {len(grid_instances)} grid instances.\n")

    # --- Line Layout Demo ---
    print("--- Line Layout ---")
    line_layout = BatchLayout(
        layout_id="test_line",
        type="line",
        ref_asset="018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e11", # Generic PLC
        params={
            "count": 5,
            "start": [0.0, 0.0, 0.0],
            "end": [10.0, 0.0, 0.0]
        },
        naming_prefix="LineAsset"
    )
    line_instances = generate_batch_instances(line_layout, existing_instances)
    for inst in line_instances:
        print(f"Line Instance: {inst.instance_id}, Pos: {inst.transform.translation}")
    print(f"Generated {len(line_instances)} line instances.\n")

    # --- Circle Layout Demo ---
    print("--- Circle Layout ---")
    circle_layout = BatchLayout(
        layout_id="test_circle",
        type="circle",
        ref_asset="018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e13", # Chiller
        params={
            "count": 4,
            "center": [5.0, 5.0, 0.0],
            "radius": 3.0,
            "start_angle": 45.0 # Start at 45 degrees
        },
        naming_prefix="CircleChiller"
    )
    circle_instances = generate_batch_instances(circle_layout, existing_instances)
    for inst in circle_instances:
        print(f"Circle Instance: {inst.instance_id}, Pos: {inst.transform.translation}")
    print(f"Generated {len(circle_instances)} circle instances.\n")

    # --- Test with ID conflict ---
    print("--- ID Conflict Test ---")
    conflict_layout = BatchLayout(
        layout_id="test_conflict",
        type="line",
        ref_asset="dummy_ref",
        params={
            "count": 2,
            "start": [0.0, 0.0, 0.0],
            "end": [2.0, 0.0, 0.0]
        },
        naming_prefix="Existing"
    )
    conflict_instances = generate_batch_instances(conflict_layout, existing_instances)
    for inst in conflict_instances:
        print(f"Conflict Instance: {inst.instance_id}, Pos: {inst.transform.translation}")
    print(f"Generated {len(conflict_instances)} conflict instances.\n")

