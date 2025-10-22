#!/usr/bin/env python3
"""
FBX to USD Conversion Proxy using Blender Python API
"""

import subprocess
import argparse
from pathlib import Path


BLENDER_SCRIPT_TEMPLATE = """
import bpy
import sys

# Clear default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Import FBX
bpy.ops.import_scene.fbx(filepath="{fbx_path}")

# Set scene units to meters
bpy.context.scene.unit_settings.system = 'METRIC'
bpy.context.scene.unit_settings.length_unit = 'METERS'

# Export to USD
bpy.ops.wm.usd_export(
    filepath="{usd_path}",
    selected_objects_only=False,
    export_animation=False,
    export_hair=False,
    export_uvmaps=True,
    export_normals=True,
    export_materials=True,
    use_instancing=False,
    evaluation_mode='RENDER'
)

print("Conversion completed successfully")
"""


def convert_fbx_to_usd(
    fbx_path: str,
    usd_path: str,
    blender_exe: str = "blender"
) -> bool:
    """
    Convert FBX to USD using Blender.
    
    Args:
        fbx_path: Path to input FBX file
        usd_path: Path to output USD file
        blender_exe: Path to Blender executable (default: "blender")
    
    Returns:
        bool: True if conversion succeeded, False otherwise
    """
    fbx_path = Path(fbx_path).resolve()
    usd_path = Path(usd_path).resolve()
    
    if not fbx_path.exists():
        print(f"Error: FBX file not found: {fbx_path}")
        return False
    
    # Create output directory
    usd_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate Blender Python script
    script = BLENDER_SCRIPT_TEMPLATE.format(
        fbx_path=str(fbx_path).replace('\\', '/'),
        usd_path=str(usd_path).replace('\\', '/')
    )
    
    # Create temporary script file
    script_path = usd_path.parent / f"_convert_{usd_path.stem}.py"
    with open(script_path, 'w') as f:
        f.write(script)
    
    try:
        # Run Blender in background mode
        cmd = [
            blender_exe,
            "--background",
            "--python", str(script_path)
        ]
        
        print(f"Converting {fbx_path.name} to {usd_path.name}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Conversion completed successfully")
            return True
        else:
            print(f"Conversion failed:")
            print(result.stderr)
            return False
    
    except FileNotFoundError:
        print(f"Error: Blender executable not found: {blender_exe}")
        print("Please install Blender or specify the correct path with --blender")
        return False
    
    finally:
        # Clean up temporary script
        if script_path.exists():
            script_path.unlink()


def main():
    parser = argparse.ArgumentParser(description="Convert FBX to USD using Blender")
    parser.add_argument("fbx", help="Path to input FBX file")
    parser.add_argument("usd", help="Path to output USD file")
    parser.add_argument("--blender", default="blender", help="Path to Blender executable")
    
    args = parser.parse_args()
    
    success = convert_fbx_to_usd(args.fbx, args.usd, args.blender)
    exit(0 if success else 1)


if __name__ == '__main__':
    main()

