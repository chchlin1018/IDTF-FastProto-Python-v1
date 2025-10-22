"""
Test script for loading FDL test files
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent / "IDTF-FastProto-Python-v1"
sys.path.insert(0, str(project_root))

from src.core.fdl.parser import parse_fdl_file
from src.core.fdl.validator import FDLValidator


def test_load_fdl_file(file_path: Path):
    """Test loading a single FDL file."""
    print("=" * 80)
    print(f"Testing: {file_path.name}")
    print("=" * 80)
    
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        return False
    
    try:
        # Parse FDL file
        fdl_obj = parse_fdl_file(file_path)
        print(f"✅ Successfully loaded FDL file")
        
        # Display Site information
        print(f"\nSite Information:")
        if fdl_obj.site:
            print(f"  - Name: {fdl_obj.site.name}")
            print(f"  - Site ID: {fdl_obj.site.site_id}")
        else:
            print("  - Site: N/A (No site defined)")
        print(f"  - Units: {fdl_obj.units.length.value} (Length), {fdl_obj.units.angle.value} (Angle)")
        print(f"  - Up Axis: {fdl_obj.units.up_axis.value}")
        print(f"  - Handedness: {fdl_obj.units.handedness.value}")
        
        # Display Global Constraints
        if fdl_obj.global_constraints:
            print(f"\nGlobal Constraints:")
            if fdl_obj.global_constraints.scaling_constraints:
                sc = fdl_obj.global_constraints.scaling_constraints
                print(f"  - Allow Scaling: {sc.allow_scaling}")
                print(f"  - Allow Non-Uniform Scaling: {sc.allow_non_uniform_scaling}")
                if sc.min_scale:
                    print(f"  - Min Scale: {sc.min_scale}")
                if sc.max_scale:
                    print(f"  - Max Scale: {sc.max_scale}")
            if fdl_obj.global_constraints.collision_detection:
                cd = fdl_obj.global_constraints.collision_detection
                print(f"  - Collision Detection Enabled: {cd.enabled}")

        
        # Display Areas
        print(f"\nAreas: {len(fdl_obj.site.areas) if fdl_obj.site else 0} total")
        if fdl_obj.site:
            for i, area in enumerate(fdl_obj.site.areas, 1):
                print(f"  Area {i}:")
                print(f"    - Name: {area.name}")
                print(f"    - Instances: {len(area.instances)}")
            
                # Display first 3 instances
                for j, instance in enumerate(area.instances[:3], 1):
                    print(f"      Instance {j}:")
                    print(f"        - ID: {instance.instance_id}")
                    print(f"        - Name: {instance.name}")
                    print(f"        - Ref Asset: {instance.ref_asset}")
                    print(f"        - Translation: {instance.transform.translation}")
                    print(f"        - Rotation: {instance.transform.rotation}")
                    print(f"        - Scale: {instance.transform.scale}")
                
                if len(area.instances) > 3:
                    print(f"      ... and {len(area.instances) - 3} more instances")
        
        # Display Batch Layouts if any
        if fdl_obj.batch_layouts:
            print(f"\nBatch Layouts: {len(fdl_obj.batch_layouts)} total")
            for k, layout in enumerate(fdl_obj.batch_layouts, 1):
                print(f"  Batch Layout {k}:")
                print(f"    - Type: {layout.type}")
                print(f"    - Params: {layout.params}")
                print(f"    - Ref Asset: {layout.ref_asset}")
            

        
        # Validate
        print(f"\nValidation:")
        validator = FDLValidator()
        is_valid = validator.validate_site(fdl_obj.site)
        errors = validator.errors
        
        if is_valid:
            print(f"  ✅ Site is valid")
        else:
            print(f"  ❌ Site has validation errors:")
            for error in errors:
                print(f"    - {error}")
        
        return is_valid
        
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    test_files = [
        "semiconductor_fab.yaml",
        "data_center.yaml",
        "lng_power_plant.yaml"
    ]
    
    testfiles_dir = Path(__file__).parent / "IDTF-FastProto-Python-v1" / "testfiles" / "FDL"
    
    print("=" * 80)
    print("FDL Test Files Loading Test")
    print("=" * 80)
    
    results = {}
    for filename in test_files:
        file_path = testfiles_dir / filename
        results[filename] = test_load_fdl_file(file_path)
        print()
    
    # Summary
    print("=" * 80)
    print("Test Summary")
    print("=" * 80)
    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed
    print(f"Total Files: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print("Results:")
    for filename, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {filename}")
    print("=" * 80)


if __name__ == '__main__':
    main()

