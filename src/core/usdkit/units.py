"""
USD Kit - Unit conversion utilities
"""

from typing import List
from pxr import Usd, UsdGeom


# Unit conversion factors (to meters)
UNIT_TO_METERS = {
    "m": 1.0,
    "cm": 0.01,
    "mm": 0.001,
    "km": 1000.0,
    "in": 0.0254,
    "ft": 0.3048,
    "yd": 0.9144,
    "mi": 1609.34,
}


def convert_length(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert a length value from one unit to another.
    
    Args:
        value: The value to convert
        from_unit: Source unit (e.g., "m", "cm", "mm", "ft", "in")
        to_unit: Target unit
    
    Returns:
        float: Converted value
    
    Raises:
        ValueError: If unit is not supported
    
    Example:
        >>> convert_length(100.0, "cm", "m")
        1.0
        >>> convert_length(1.0, "m", "ft")
        3.280839895013123
    """
    if from_unit not in UNIT_TO_METERS:
        raise ValueError(f"Unsupported unit: {from_unit}")
    if to_unit not in UNIT_TO_METERS:
        raise ValueError(f"Unsupported unit: {to_unit}")
    
    # Convert to meters first, then to target unit
    meters = value * UNIT_TO_METERS[from_unit]
    return meters / UNIT_TO_METERS[to_unit]


def convert_point(point: List[float], from_unit: str, to_unit: str) -> List[float]:
    """
    Convert a 3D point from one unit to another.
    
    Args:
        point: [x, y, z] point
        from_unit: Source unit
        to_unit: Target unit
    
    Returns:
        List[float]: Converted [x, y, z] point
    
    Example:
        >>> convert_point([100.0, 200.0, 300.0], "cm", "m")
        [1.0, 2.0, 3.0]
    """
    return [convert_length(coord, from_unit, to_unit) for coord in point]


def set_stage_meters_per_unit(stage: Usd.Stage, meters_per_unit: float):
    """
    Set the metersPerUnit metadata for a USD stage.
    
    Args:
        stage: USD stage
        meters_per_unit: Meters per unit value
    
    Example:
        >>> # Assuming 'stage' is a valid Usd.Stage
        >>> set_stage_meters_per_unit(stage, 0.01)  # Set to centimeters
    """
    UsdGeom.SetStageMetersPerUnit(stage, meters_per_unit)


def get_stage_meters_per_unit(stage: Usd.Stage) -> float:
    """
    Get the metersPerUnit metadata from a USD stage.
    
    Args:
        stage: USD stage
    
    Returns:
        float: Meters per unit value (default: 1.0 if not set)
    
    Example:
        >>> # Assuming 'stage' is a valid Usd.Stage
        >>> meters_per_unit = get_stage_meters_per_unit(stage)
    """
    return UsdGeom.GetStageMetersPerUnit(stage)


def set_stage_up_axis(stage: Usd.Stage, up_axis: str):
    """
    Set the upAxis metadata for a USD stage.
    
    Args:
        stage: USD stage
        up_axis: Up axis ("Y" or "Z")
    
    Raises:
        ValueError: If up_axis is not "Y" or "Z"
    
    Example:
        >>> # Assuming 'stage' is a valid Usd.Stage
        >>> set_stage_up_axis(stage, "Z")
    """
    if up_axis not in ["Y", "Z"]:
        raise ValueError(f"Invalid up_axis: {up_axis}. Must be 'Y' or 'Z'.")
    
    up_axis_token = UsdGeom.Tokens.y if up_axis == "Y" else UsdGeom.Tokens.z
    UsdGeom.SetStageUpAxis(stage, up_axis_token)


def get_stage_up_axis(stage: Usd.Stage) -> str:
    """
    Get the upAxis metadata from a USD stage.
    
    Args:
        stage: USD stage
    
    Returns:
        str: Up axis ("Y" or "Z", default: "Y" if not set)
    
    Example:
        >>> # Assuming 'stage' is a valid Usd.Stage
        >>> up_axis = get_stage_up_axis(stage)
    """
    up_axis_token = UsdGeom.GetStageUpAxis(stage)
    return "Y" if up_axis_token == UsdGeom.Tokens.y else "Z"


def convert_stage_units(
    stage: Usd.Stage,
    from_unit: str,
    to_unit: str,
    update_metadata: bool = True
):
    """
    Convert all geometry in a USD stage from one unit to another.
    
    This function scales all xformable prims in the stage.
    
    Args:
        stage: USD stage
        from_unit: Source unit
        to_unit: Target unit
        update_metadata: Whether to update the stage's metersPerUnit metadata
    
    Example:
        >>> # Assuming 'stage' is a valid Usd.Stage with geometry in centimeters
        >>> convert_stage_units(stage, "cm", "m")
    """
    scale_factor = convert_length(1.0, from_unit, to_unit)
    
    # Iterate through all prims and scale xformable ones
    for prim in stage.Traverse():
        if prim.IsA(UsdGeom.Xformable):
            xformable = UsdGeom.Xformable(prim)
            
            # Get existing scale op or create new one
            scale_ops = [op for op in xformable.GetOrderedXformOps() if op.GetOpType() == UsdGeom.XformOp.TypeScale]
            
            if scale_ops:
                # Update existing scale op
                scale_op = scale_ops[0]
                current_scale = scale_op.Get()
                new_scale = [s * scale_factor for s in current_scale]
                scale_op.Set(new_scale)
            else:
                # Add new scale op
                scale_op = xformable.AddScaleOp()
                scale_op.Set([scale_factor, scale_factor, scale_factor])
    
    if update_metadata:
        new_meters_per_unit = UNIT_TO_METERS[to_unit]
        set_stage_meters_per_unit(stage, new_meters_per_unit)


if __name__ == '__main__':
    print("=== USD Kit Unit Conversion Utilities Demo ===\n")
    
    # Length conversion
    print("--- Length Conversion ---")
    print(f"100 cm to m: {convert_length(100.0, 'cm', 'm')}")
    print(f"1 m to ft: {convert_length(1.0, 'm', 'ft')}")
    print(f"12 in to cm: {convert_length(12.0, 'in', 'cm')}")
    print()
    
    # Point conversion
    print("--- Point Conversion ---")
    point_cm = [100.0, 200.0, 300.0]
    point_m = convert_point(point_cm, "cm", "m")
    print(f"Point in cm: {point_cm}")
    print(f"Point in m: {point_m}")
    print()
    
    # Supported units
    print("--- Supported Units ---")
    print(f"Supported units: {list(UNIT_TO_METERS.keys())}")
    print()
    
    print("Note: For full USD stage unit operations, you need a valid USD stage.")
    print("The set_stage_meters_per_unit, get_stage_meters_per_unit, set_stage_up_axis,")
    print("get_stage_up_axis, and convert_stage_units functions require a USD stage context,")
    print("which is not demonstrated in this standalone script.")

