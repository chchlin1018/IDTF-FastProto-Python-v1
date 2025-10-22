#!/usr/bin/env python3
"""
USD CLI - Inspect USD files
"""

import argparse
from pathlib import Path
from pxr import Usd, UsdGeom


def inspect_usd(file_path: str, verbose: bool = False):
    """
    Inspect a USD file and print its structure.
    
    Args:
        file_path: Path to the USD file
        verbose: Whether to print detailed information
    """
    stage = Usd.Stage.Open(file_path)
    
    if not stage:
        print(f"Error: Could not open USD file: {file_path}")
        return
    
    print(f"=== USD File: {file_path} ===\n")
    
    # Stage metadata
    print("--- Stage Metadata ---")
    print(f"Up Axis: {UsdGeom.GetStageUpAxis(stage)}")
    print(f"Meters Per Unit: {UsdGeom.GetStageMetersPerUnit(stage)}")
    
    default_prim = stage.GetDefaultPrim()
    if default_prim:
        print(f"Default Prim: {default_prim.GetPath()}")
    print()
    
    # Prim hierarchy
    print("--- Prim Hierarchy ---")
    for prim in stage.Traverse():
        indent = "  " * (len(prim.GetPath().pathString.split('/')) - 2)
        type_name = prim.GetTypeName()
        
        if verbose:
            print(f"{indent}{prim.GetName()} ({type_name}) - {prim.GetPath()}")
        else:
            print(f"{indent}{prim.GetName()} ({type_name})")
    
    print()
    
    # Statistics
    print("--- Statistics ---")
    prim_count = len(list(stage.Traverse()))
    print(f"Total Prims: {prim_count}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Inspect USD files")
    parser.add_argument("file", help="Path to USD file")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    inspect_usd(args.file, args.verbose)


if __name__ == '__main__':
    main()

