"""
USD Kit - USD Reference and Variant utilities
"""

from typing import Optional, List, Dict
from pxr import Usd, Sdf


def add_reference(
    prim: Usd.Prim,
    asset_path: str,
    prim_path: Optional[str] = None,
    layer_offset: Optional[float] = None
):
    """
    Add a USD reference to a prim.
    
    Args:
        prim: USD prim to add the reference to
        asset_path: Path to the referenced USD file
        prim_path: Optional path to a specific prim in the referenced file
        layer_offset: Optional time offset for the reference
    
    Example:
        >>> add_reference(prim, "@/assets/pump.usd@", "/Pump")
    """
    references = prim.GetReferences()
    if layer_offset is not None:
        layer_offset_obj = Sdf.LayerOffset(layer_offset)
        references.AddReference(asset_path, prim_path, layer_offset_obj)
    else:
        if prim_path:
            references.AddReference(asset_path, prim_path)
        else:
            references.AddReference(asset_path)


def add_internal_reference(
    prim: Usd.Prim,
    target_prim_path: str
):
    """
    Add an internal reference (reference to another prim in the same stage).
    
    Args:
        prim: USD prim to add the reference to
        target_prim_path: Path to the target prim in the same stage
    
    Example:
        >>> add_internal_reference(prim, "/World/PrototypePump")
    """
    references = prim.GetReferences()
    references.AddInternalReference(target_prim_path)


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


def list_references(prim: Usd.Prim) -> List[str]:
    """
    List all references on a prim.
    
    Args:
        prim: USD prim
    
    Returns:
        List[str]: List of reference asset paths
    
    Example:
        >>> refs = list_references(prim)
    """
    prim_stack = prim.GetPrimStack()
    references = []
    for prim_spec in prim_stack:
        if prim_spec.hasReferences:
            ref_list = prim_spec.referenceList
            for ref in ref_list.prependedItems:
                references.append(ref.assetPath)
    return references


def create_variant_set(
    prim: Usd.Prim,
    variant_set_name: str
) -> Usd.VariantSet:
    """
    Create a variant set on a prim.
    
    Args:
        prim: USD prim
        variant_set_name: Name of the variant set
    
    Returns:
        Usd.VariantSet: The created variant set
    
    Example:
        >>> variant_set = create_variant_set(prim, "modelVariant")
    """
    variant_sets = prim.GetVariantSets()
    return variant_sets.AddVariantSet(variant_set_name)


def add_variant(
    prim: Usd.Prim,
    variant_set_name: str,
    variant_name: str
):
    """
    Add a variant to a variant set.
    
    Args:
        prim: USD prim
        variant_set_name: Name of the variant set
        variant_name: Name of the variant to add
    
    Example:
        >>> add_variant(prim, "modelVariant", "highDetail")
    """
    variant_set = prim.GetVariantSet(variant_set_name)
    if not variant_set:
        variant_set = create_variant_set(prim, variant_set_name)
    
    variant_set.AddVariant(variant_name)


def set_variant_selection(
    prim: Usd.Prim,
    variant_set_name: str,
    variant_name: str
):
    """
    Set the active variant in a variant set.
    
    Args:
        prim: USD prim
        variant_set_name: Name of the variant set
        variant_name: Name of the variant to select
    
    Example:
        >>> set_variant_selection(prim, "modelVariant", "highDetail")
    """
    variant_set = prim.GetVariantSet(variant_set_name)
    if variant_set:
        variant_set.SetVariantSelection(variant_name)


def get_variant_selection(
    prim: Usd.Prim,
    variant_set_name: str
) -> Optional[str]:
    """
    Get the currently selected variant in a variant set.
    
    Args:
        prim: USD prim
        variant_set_name: Name of the variant set
    
    Returns:
        Optional[str]: The selected variant name, or None if not set
    
    Example:
        >>> selected_variant = get_variant_selection(prim, "modelVariant")
    """
    variant_set = prim.GetVariantSet(variant_set_name)
    if variant_set:
        return variant_set.GetVariantSelection()
    return None


def list_variant_sets(prim: Usd.Prim) -> List[str]:
    """
    List all variant sets on a prim.
    
    Args:
        prim: USD prim
    
    Returns:
        List[str]: List of variant set names
    
    Example:
        >>> variant_sets = list_variant_sets(prim)
    """
    variant_sets = prim.GetVariantSets()
    return variant_sets.GetNames()


def list_variants(prim: Usd.Prim, variant_set_name: str) -> List[str]:
    """
    List all variants in a variant set.
    
    Args:
        prim: USD prim
        variant_set_name: Name of the variant set
    
    Returns:
        List[str]: List of variant names
    
    Example:
        >>> variants = list_variants(prim, "modelVariant")
    """
    variant_set = prim.GetVariantSet(variant_set_name)
    if variant_set:
        return variant_set.GetVariantNames()
    return []


def edit_variant(
    prim: Usd.Prim,
    variant_set_name: str,
    variant_name: str
) -> Usd.EditContext:
    """
    Create an edit context for authoring content within a variant.
    
    This is a context manager that allows you to edit the content of a specific variant.
    
    Args:
        prim: USD prim
        variant_set_name: Name of the variant set
        variant_name: Name of the variant to edit
    
    Returns:
        Usd.EditContext: Edit context for the variant
    
    Example:
        >>> with edit_variant(prim, "modelVariant", "highDetail"):
        >>>     # Author content for the "highDetail" variant
        >>>     child_prim = stage.DefinePrim(prim.GetPath().AppendChild("DetailedMesh"), "Mesh")
    """
    variant_set = prim.GetVariantSet(variant_set_name)
    if not variant_set:
        variant_set = create_variant_set(prim, variant_set_name)
    
    variant_set.SetVariantSelection(variant_name)
    return variant_set.GetVariantEditContext()


if __name__ == '__main__':
    import tempfile
    from pathlib import Path
    from pxr import UsdGeom
    
    print("=== USD Kit Reference and Variant Utilities Demo ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Create a reference asset
        print("--- Creating Reference Asset ---")
        ref_asset_path = temp_dir_path / "pump_asset.usda"
        ref_stage = Usd.Stage.CreateNew(str(ref_asset_path))
        ref_prim = ref_stage.DefinePrim("/Pump", "Xform")
        ref_sphere = UsdGeom.Sphere.Define(ref_stage, "/Pump/Body")
        ref_stage.SetDefaultPrim(ref_prim)
        ref_stage.Save()
        print(f"Created reference asset: {ref_asset_path}")
        print()
        
        # Create main stage
        print("--- Creating Main Stage ---")
        main_stage_path = temp_dir_path / "main_scene.usda"
        main_stage = Usd.Stage.CreateNew(str(main_stage_path))
        world_prim = main_stage.DefinePrim("/World", "Xform")
        main_stage.SetDefaultPrim(world_prim)
        print(f"Created main stage: {main_stage_path}")
        print()
        
        # Add reference
        print("--- Adding Reference ---")
        pump_instance_prim = main_stage.DefinePrim("/World/Pump_001", "Xform")
        add_reference(pump_instance_prim, str(ref_asset_path))
        main_stage.Save()
        print(f"Added reference to {pump_instance_prim.GetPath()}")
        print(f"References: {list_references(pump_instance_prim)}")
        print()
        
        # Create variant set
        print("--- Creating Variant Set ---")
        variant_prim = main_stage.DefinePrim("/World/VariantAsset", "Xform")
        variant_set = create_variant_set(variant_prim, "modelVariant")
        print(f"Created variant set 'modelVariant' on {variant_prim.GetPath()}")
        print()
        
        # Add variants
        print("--- Adding Variants ---")
        add_variant(variant_prim, "modelVariant", "lowDetail")
        add_variant(variant_prim, "modelVariant", "highDetail")
        print(f"Added variants: {list_variants(variant_prim, 'modelVariant')}")
        print()
        
        # Edit variant content
        print("--- Editing Variant Content ---")
        with edit_variant(variant_prim, "modelVariant", "lowDetail"):
            low_detail_mesh = main_stage.DefinePrim(variant_prim.GetPath().AppendChild("LowMesh"), "Sphere")
            print(f"Authored content in 'lowDetail' variant: {low_detail_mesh.GetPath()}")
        
        with edit_variant(variant_prim, "modelVariant", "highDetail"):
            high_detail_mesh = main_stage.DefinePrim(variant_prim.GetPath().AppendChild("HighMesh"), "Cube")
            print(f"Authored content in 'highDetail' variant: {high_detail_mesh.GetPath()}")
        print()
        
        # Set variant selection
        print("--- Setting Variant Selection ---")
        set_variant_selection(variant_prim, "modelVariant", "highDetail")
        selected_variant = get_variant_selection(variant_prim, "modelVariant")
        print(f"Selected variant: {selected_variant}")
        print()
        
        # List variant sets
        print("--- Listing Variant Sets ---")
        variant_sets = list_variant_sets(variant_prim)
        print(f"Variant sets on {variant_prim.GetPath()}: {variant_sets}")
        print()
        
        main_stage.Save()
        print(f"Saved main stage to: {main_stage_path}")
        print()
        
        print("Demo completed. Temporary files will be cleaned up automatically.")

