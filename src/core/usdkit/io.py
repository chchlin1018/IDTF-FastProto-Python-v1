"""
USD Kit - USD file I/O utilities
"""

from pathlib import Path
from typing import Union, Optional
from pxr import Usd, UsdGeom, Sdf


def create_stage(file_path: Union[str, Path], up_axis: str = "Z", meters_per_unit: float = 1.0) -> Usd.Stage:
    """
    Create a new USD stage and save it to a file.
    
    Args:
        file_path: Path to the USD file (.usd, .usda, .usdc)
        up_axis: Up axis ("Y" or "Z", default: "Z")
        meters_per_unit: Meters per unit (default: 1.0 for meters)
    
    Returns:
        Usd.Stage: The created USD stage
    
    Example:
        >>> stage = create_stage("my_scene.usda", up_axis="Z", meters_per_unit=1.0)
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    stage = Usd.Stage.CreateNew(str(file_path))
    
    # Set stage metadata
    UsdGeom.SetStageMetersPerUnit(stage, meters_per_unit)
    up_axis_token = UsdGeom.Tokens.y if up_axis == "Y" else UsdGeom.Tokens.z
    UsdGeom.SetStageUpAxis(stage, up_axis_token)
    
    stage.Save()
    return stage


def open_stage(file_path: Union[str, Path]) -> Usd.Stage:
    """
    Open an existing USD stage from a file.
    
    Args:
        file_path: Path to the USD file
    
    Returns:
        Usd.Stage: The opened USD stage
    
    Raises:
        FileNotFoundError: If the file does not exist
    
    Example:
        >>> stage = open_stage("existing_scene.usda")
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"USD file not found: {file_path}")
    
    return Usd.Stage.Open(str(file_path))


def save_stage(stage: Usd.Stage):
    """
    Save a USD stage to its associated file.
    
    Args:
        stage: USD stage to save
    
    Example:
        >>> save_stage(stage)
    """
    stage.Save()


def export_stage(stage: Usd.Stage, file_path: Union[str, Path]):
    """
    Export a USD stage to a new file.
    
    Args:
        stage: USD stage to export
        file_path: Path to the output USD file
    
    Example:
        >>> export_stage(stage, "exported_scene.usdc")
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    stage.Export(str(file_path))


def create_prim(
    stage: Usd.Stage,
    prim_path: str,
    prim_type: str = "Xform"
) -> Usd.Prim:
    """
    Create a new prim in a USD stage.
    
    Args:
        stage: USD stage
        prim_path: Path of the prim (e.g., "/World/MyPrim")
        prim_type: Type of the prim (e.g., "Xform", "Mesh", "Sphere", default: "Xform")
    
    Returns:
        Usd.Prim: The created prim
    
    Example:
        >>> prim = create_prim(stage, "/World/MyAsset", "Xform")
    """
    return stage.DefinePrim(prim_path, prim_type)


def get_prim(stage: Usd.Stage, prim_path: str) -> Optional[Usd.Prim]:
    """
    Get a prim from a USD stage by path.
    
    Args:
        stage: USD stage
        prim_path: Path of the prim
    
    Returns:
        Optional[Usd.Prim]: The prim if found, None otherwise
    
    Example:
        >>> prim = get_prim(stage, "/World/MyAsset")
    """
    prim = stage.GetPrimAtPath(prim_path)
    return prim if prim.IsValid() else None


def delete_prim(stage: Usd.Stage, prim_path: str):
    """
    Delete a prim from a USD stage.
    
    Args:
        stage: USD stage
        prim_path: Path of the prim to delete
    
    Example:
        >>> delete_prim(stage, "/World/MyAsset")
    """
    stage.RemovePrim(prim_path)


def set_default_prim(stage: Usd.Stage, prim_path: str):
    """
    Set the default prim for a USD stage.
    
    Args:
        stage: USD stage
        prim_path: Path of the prim to set as default
    
    Example:
        >>> set_default_prim(stage, "/World")
    """
    prim = stage.GetPrimAtPath(prim_path)
    if prim.IsValid():
        stage.SetDefaultPrim(prim)


def get_default_prim(stage: Usd.Stage) -> Optional[Usd.Prim]:
    """
    Get the default prim of a USD stage.
    
    Args:
        stage: USD stage
    
    Returns:
        Optional[Usd.Prim]: The default prim if set, None otherwise
    
    Example:
        >>> default_prim = get_default_prim(stage)
    """
    return stage.GetDefaultPrim()


def add_reference(
    prim: Usd.Prim,
    asset_path: str,
    prim_path: Optional[str] = None
):
    """
    Add a USD reference to a prim.
    
    Args:
        prim: USD prim to add the reference to
        asset_path: Path to the referenced USD file
        prim_path: Optional path to a specific prim in the referenced file
    
    Example:
        >>> add_reference(prim, "/assets/pump.usd", "/Pump")
    """
    references = prim.GetReferences()
    if prim_path:
        references.AddReference(asset_path, prim_path)
    else:
        references.AddReference(asset_path)


def clear_references(prim: Usd.Prim):
    """
    Clear all references from a prim.
    
    Args:
        prim: USD prim
    
    Example:
        >>> clear_references(prim)
    """
    references = prim.GetReferences()
    references.ClearReferences()


if __name__ == '__main__':
    import tempfile
    import os
    
    print("=== USD Kit I/O Utilities Demo ===\n")
    
    # Create a temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Create a new stage
        print("--- Creating a New USD Stage ---")
        stage_path = temp_dir_path / "demo_scene.usda"
        stage = create_stage(stage_path, up_axis="Z", meters_per_unit=1.0)
        print(f"Created stage: {stage_path}")
        print(f"Up Axis: {UsdGeom.GetStageUpAxis(stage)}")
        print(f"Meters Per Unit: {UsdGeom.GetStageMetersPerUnit(stage)}")
        print()
        
        # Create prims
        print("--- Creating Prims ---")
        world_prim = create_prim(stage, "/World", "Xform")
        asset_prim = create_prim(stage, "/World/MyAsset", "Xform")
        sphere_prim = create_prim(stage, "/World/MyAsset/Sphere", "Sphere")
        print(f"Created prim: {world_prim.GetPath()}")
        print(f"Created prim: {asset_prim.GetPath()}")
        print(f"Created prim: {sphere_prim.GetPath()}")
        print()
        
        # Set default prim
        print("--- Setting Default Prim ---")
        set_default_prim(stage, "/World")
        default_prim = get_default_prim(stage)
        print(f"Default prim: {default_prim.GetPath() if default_prim else 'None'}")
        print()
        
        # Save stage
        print("--- Saving Stage ---")
        save_stage(stage)
        print(f"Saved stage to: {stage_path}")
        print()
        
        # Open stage
        print("--- Opening Stage ---")
        opened_stage = open_stage(stage_path)
        print(f"Opened stage from: {stage_path}")
        print(f"Stage has {len(list(opened_stage.Traverse()))} prims")
        print()
        
        # Get prim
        print("--- Getting Prim ---")
        retrieved_prim = get_prim(opened_stage, "/World/MyAsset")
        print(f"Retrieved prim: {retrieved_prim.GetPath() if retrieved_prim else 'None'}")
        print()
        
        # Export stage
        print("--- Exporting Stage ---")
        export_path = temp_dir_path / "exported_scene.usdc"
        export_stage(opened_stage, export_path)
        print(f"Exported stage to: {export_path}")
        print()
        
        # Delete prim
        print("--- Deleting Prim ---")
        delete_prim(opened_stage, "/World/MyAsset/Sphere")
        save_stage(opened_stage)
        print(f"Deleted prim: /World/MyAsset/Sphere")
        print(f"Stage now has {len(list(opened_stage.Traverse()))} prims")
        print()
        
        print("Demo completed. Temporary files will be cleaned up automatically.")

