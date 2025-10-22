"""
USD Kit - Transform utilities for USD operations
"""

import numpy as np
from typing import List, Tuple, Optional
from pxr import Usd, UsdGeom, Gf


def create_transform_matrix(
    translation: List[float] = None,
    rotation: List[float] = None,
    scale: List[float] = None
) -> Gf.Matrix4d:
    """
    Create a 4x4 transformation matrix from translation, rotation (Euler angles in degrees), and scale.
    
    Args:
        translation: [x, y, z] translation vector (default: [0, 0, 0])
        rotation: [rx, ry, rz] Euler angles in degrees (default: [0, 0, 0])
        scale: [sx, sy, sz] scale factors (default: [1, 1, 1])
    
    Returns:
        Gf.Matrix4d: 4x4 transformation matrix
    
    Example:
        >>> matrix = create_transform_matrix([1.0, 2.0, 3.0], [0.0, 0.0, 90.0], [1.0, 1.0, 1.0])
    """
    if translation is None:
        translation = [0.0, 0.0, 0.0]
    if rotation is None:
        rotation = [0.0, 0.0, 0.0]
    if scale is None:
        scale = [1.0, 1.0, 1.0]
    
    # Create translation matrix
    translate_matrix = Gf.Matrix4d(1.0)
    translate_matrix.SetTranslateOnly(Gf.Vec3d(*translation))
    
    # Create rotation matrix (XYZ Euler angles)
    rotation_x = Gf.Rotation(Gf.Vec3d(1, 0, 0), rotation[0])
    rotation_y = Gf.Rotation(Gf.Vec3d(0, 1, 0), rotation[1])
    rotation_z = Gf.Rotation(Gf.Vec3d(0, 0, 1), rotation[2])
    
    rotate_matrix = Gf.Matrix4d(1.0)
    rotate_matrix.SetRotateOnly(rotation_z * rotation_y * rotation_x)
    
    # Create scale matrix
    scale_matrix = Gf.Matrix4d(1.0)
    scale_matrix.SetScale(Gf.Vec3d(*scale))
    
    # Combine: T * R * S
    return translate_matrix * rotate_matrix * scale_matrix


def decompose_transform_matrix(matrix: Gf.Matrix4d) -> Tuple[List[float], List[float], List[float]]:
    """
    Decompose a 4x4 transformation matrix into translation, rotation (Euler angles), and scale.
    
    Args:
        matrix: 4x4 transformation matrix
    
    Returns:
        Tuple[List[float], List[float], List[float]]: (translation, rotation_degrees, scale)
    
    Example:
        >>> matrix = create_transform_matrix([1.0, 2.0, 3.0], [0.0, 0.0, 90.0], [2.0, 2.0, 2.0])
        >>> translation, rotation, scale = decompose_transform_matrix(matrix)
    """
    # Extract translation
    translation_vec = matrix.ExtractTranslation()
    translation = [translation_vec[0], translation_vec[1], translation_vec[2]]
    
    # Extract rotation (as quaternion, then convert to Euler)
    rotation_quat = matrix.ExtractRotationQuat()
    rotation_matrix = rotation_quat.GetMatrix()
    
    # Convert rotation matrix to Euler angles (XYZ order)
    # This is a simplified extraction; for production, use proper Euler extraction
    # For now, we'll use a basic approach
    rotation_gf = Gf.Rotation()
    rotation_gf.SetQuat(rotation_quat)
    axis = rotation_gf.GetAxis()
    angle = rotation_gf.GetAngle()
    
    # Simplified: assume single-axis rotation for demo
    # In production, use proper XYZ Euler decomposition
    if abs(axis[0]) > 0.9:
        rotation = [angle, 0.0, 0.0]
    elif abs(axis[1]) > 0.9:
        rotation = [0.0, angle, 0.0]
    elif abs(axis[2]) > 0.9:
        rotation = [0.0, 0.0, angle]
    else:
        # For complex rotations, this is a placeholder
        rotation = [0.0, 0.0, 0.0]
    
    # Extract scale
    scale_vec = Gf.Vec3d(
        Gf.Vec3d(matrix[0][0], matrix[0][1], matrix[0][2]).GetLength(),
        Gf.Vec3d(matrix[1][0], matrix[1][1], matrix[1][2]).GetLength(),
        Gf.Vec3d(matrix[2][0], matrix[2][1], matrix[2][2]).GetLength()
    )
    scale = [scale_vec[0], scale_vec[1], scale_vec[2]]
    
    return translation, rotation, scale


def set_prim_transform(
    prim: Usd.Prim,
    translation: List[float] = None,
    rotation: List[float] = None,
    scale: List[float] = None,
    time: Usd.TimeCode = Usd.TimeCode.Default()
):
    """
    Set the transform of a USD prim.
    
    Args:
        prim: USD prim to transform
        translation: [x, y, z] translation vector
        rotation: [rx, ry, rz] Euler angles in degrees
        scale: [sx, sy, sz] scale factors
        time: USD time code (default: Usd.TimeCode.Default())
    
    Example:
        >>> # Assuming 'prim' is a valid Usd.Prim
        >>> set_prim_transform(prim, [10.0, 5.0, 0.0], [0.0, 0.0, 45.0], [1.0, 1.0, 1.0])
    """
    xformable = UsdGeom.Xformable(prim)
    if not xformable:
        raise ValueError(f"Prim {prim.GetPath()} is not xformable.")
    
    xformable.ClearXformOpOrder()
    
    if translation:
        translate_op = xformable.AddTranslateOp()
        translate_op.Set(Gf.Vec3d(*translation), time)
    
    if rotation:
        # Apply rotations in XYZ order
        if rotation[0] != 0.0:
            rotate_x_op = xformable.AddRotateXOp()
            rotate_x_op.Set(rotation[0], time)
        if rotation[1] != 0.0:
            rotate_y_op = xformable.AddRotateYOp()
            rotate_y_op.Set(rotation[1], time)
        if rotation[2] != 0.0:
            rotate_z_op = xformable.AddRotateZOp()
            rotate_z_op.Set(rotation[2], time)
    
    if scale:
        scale_op = xformable.AddScaleOp()
        scale_op.Set(Gf.Vec3f(*scale), time)


def get_prim_transform(
    prim: Usd.Prim,
    time: Usd.TimeCode = Usd.TimeCode.Default()
) -> Gf.Matrix4d:
    """
    Get the local transformation matrix of a USD prim.
    
    Args:
        prim: USD prim
        time: USD time code (default: Usd.TimeCode.Default())
    
    Returns:
        Gf.Matrix4d: Local transformation matrix
    
    Example:
        >>> # Assuming 'prim' is a valid Usd.Prim
        >>> matrix = get_prim_transform(prim)
    """
    xformable = UsdGeom.Xformable(prim)
    if not xformable:
        return Gf.Matrix4d(1.0)  # Identity matrix
    
    return xformable.GetLocalTransformation(time)


def get_prim_world_transform(
    prim: Usd.Prim,
    time: Usd.TimeCode = Usd.TimeCode.Default()
) -> Gf.Matrix4d:
    """
    Get the world transformation matrix of a USD prim (including parent transforms).
    
    Args:
        prim: USD prim
        time: USD time code (default: Usd.TimeCode.Default())
    
    Returns:
        Gf.Matrix4d: World transformation matrix
    
    Example:
        >>> # Assuming 'prim' is a valid Usd.Prim
        >>> world_matrix = get_prim_world_transform(prim)
    """
    xformable = UsdGeom.Xformable(prim)
    if not xformable:
        return Gf.Matrix4d(1.0)  # Identity matrix
    
    xform_cache = UsdGeom.XformCache(time)
    return xform_cache.GetLocalToWorldTransform(prim)


def transform_point(point: List[float], matrix: Gf.Matrix4d) -> List[float]:
    """
    Transform a 3D point by a 4x4 matrix.
    
    Args:
        point: [x, y, z] point
        matrix: 4x4 transformation matrix
    
    Returns:
        List[float]: Transformed [x, y, z] point
    
    Example:
        >>> matrix = create_transform_matrix([10.0, 0.0, 0.0])
        >>> transformed_point = transform_point([1.0, 2.0, 3.0], matrix)
        >>> print(transformed_point)
        [11.0, 2.0, 3.0]
    """
    gf_point = Gf.Vec3d(*point)
    transformed = matrix.Transform(gf_point)
    return [transformed[0], transformed[1], transformed[2]]


if __name__ == '__main__':
    print("=== USD Kit Transform Utilities Demo ===\n")
    
    # Create a transformation matrix
    print("--- Creating Transform Matrix ---")
    translation = [10.0, 5.0, 2.0]
    rotation = [0.0, 0.0, 45.0]  # 45 degrees around Z-axis
    scale = [1.0, 1.0, 1.0]
    
    matrix = create_transform_matrix(translation, rotation, scale)
    print(f"Transform Matrix:\n{matrix}")
    print()
    
    # Decompose the matrix
    print("--- Decomposing Transform Matrix ---")
    decomposed_translation, decomposed_rotation, decomposed_scale = decompose_transform_matrix(matrix)
    print(f"Translation: {decomposed_translation}")
    print(f"Rotation: {decomposed_rotation}")
    print(f"Scale: {decomposed_scale}")
    print()
    
    # Transform a point
    print("--- Transforming a Point ---")
    point = [1.0, 0.0, 0.0]
    transformed_point = transform_point(point, matrix)
    print(f"Original Point: {point}")
    print(f"Transformed Point: {transformed_point}")
    print()
    
    print("Note: For full USD prim transform operations, you need a valid USD stage and prim.")
    print("The set_prim_transform, get_prim_transform, and get_prim_world_transform functions")
    print("require a USD stage context, which is not demonstrated in this standalone script.")

