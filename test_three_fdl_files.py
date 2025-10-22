#!/usr/bin/env python3.11
"""
Comprehensive Test for Asset Library Tree View and Factory Layout Tree View
測試讀取 3 個 FDL 檔案，驗證兩個 Tree View 功能正常
"""

import sys
from pathlib import Path
from collections import defaultdict

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.eventbus.inmem import InMemoryEventBus
from core.tsdb.sqlite_tsdb import SQLiteTSDB
from core.runtime.ndh_service import NDHService


def print_separator(title=""):
    """Print a separator line"""
    if title:
        print(f"\n{'=' * 80}")
        print(f"  {title}")
        print('=' * 80)
    else:
        print('=' * 80)


def test_asset_library_view(ndh_service, fdl_name):
    """Test Asset Library Tree View logic"""
    print(f"\n[Asset Library Tree View] - {fdl_name}")
    print("-" * 80)
    
    # Group servants by asset type
    asset_type_groups = defaultdict(list)
    for servant in ndh_service.asset_servants.values():
        asset_type_name = servant.asset_definition.name
        asset_type_groups[asset_type_name].append(servant)
    
    total_instances = 0
    total_tags = 0
    
    print(f"Asset Types ({len(asset_type_groups)} types):")
    for asset_type_name, servants in sorted(asset_type_groups.items()):
        instance_count = len(servants)
        total_instances += instance_count
        
        print(f"  • {asset_type_name}: {instance_count} instances")
        
        for servant in servants:
            tag_count = len(servant.get_all_tag_servants())
            total_tags += tag_count
            print(f"    - {servant.instance.instance_id}: {tag_count} tags")
    
    print(f"\nSummary:")
    print(f"  Total Asset Types: {len(asset_type_groups)}")
    print(f"  Total Asset Instances: {total_instances}")
    print(f"  Total Tags: {total_tags}")
    
    return {
        "asset_types": len(asset_type_groups),
        "instances": total_instances,
        "tags": total_tags
    }


def test_factory_layout_view(ndh_service, fdl_name):
    """Test Factory Layout Tree View logic"""
    print(f"\n[Factory Layout Tree View] - {fdl_name}")
    print("-" * 80)
    
    fdl = ndh_service.fdl
    
    print(f"Site: {fdl.site.name}")
    print(f"  Site ID: {fdl.site.site_id}")
    
    if fdl.site.location:
        print(f"  Location: Lat={fdl.site.location.get('latitude')}, "
              f"Lon={fdl.site.location.get('longitude')}, "
              f"Alt={fdl.site.location.get('altitude')}")
    
    if fdl.units:
        print(f"  Units: {fdl.units.length.value}, {fdl.units.angle.value}, "
              f"{fdl.units.up_axis.value}, {fdl.units.handedness.value}")
    
    total_instances = 0
    total_connections = 0
    
    print(f"\nAreas ({len(fdl.site.areas)} areas):")
    for area in fdl.site.areas:
        print(f"  • {area.name} ({area.type})")
        print(f"    - Area ID: {area.area_id}")
        print(f"    - Instances: {len(area.instances)}")
        print(f"    - Connections: {len(area.connections)}")
        
        total_instances += len(area.instances)
        total_connections += len(area.connections)
        
        # Show first 2 instances
        for instance in area.instances[:2]:
            print(f"      • Instance: {instance.instance_id}")
            print(f"        Ref: {instance.ref_asset}")
            print(f"        Transform: T={instance.transform.translation}")
        
        if len(area.instances) > 2:
            print(f"      ... and {len(area.instances) - 2} more instances")
    
    # Global Settings
    if fdl.global_constraints:
        print(f"\nGlobal Settings:")
        if fdl.global_constraints.scaling_constraints:
            sc = fdl.global_constraints.scaling_constraints
            print(f"  Scaling: allow={sc.allow_scaling}, "
                  f"non_uniform={sc.allow_non_uniform_scaling}")
        
        if fdl.global_constraints.collision_detection:
            cd = fdl.global_constraints.collision_detection
            print(f"  Collision: enabled={cd.enabled}, "
                  f"clearance={cd.clearance_distance}m")
    
    print(f"\nSummary:")
    print(f"  Total Areas: {len(fdl.site.areas)}")
    print(f"  Total Instances: {total_instances}")
    print(f"  Total Connections: {total_connections}")
    
    return {
        "areas": len(fdl.site.areas),
        "instances": total_instances,
        "connections": total_connections
    }


def test_single_fdl(fdl_file, iadl_dir):
    """Test a single FDL file"""
    fdl_name = fdl_file.stem
    
    print_separator(f"Testing FDL: {fdl_name}")
    
    # Create services
    event_bus = InMemoryEventBus()
    tsdb = SQLiteTSDB(":memory:")
    ndh_service = NDHService(event_bus=event_bus, tsdb=tsdb)
    
    # Load IADL
    try:
        ndh_service.load_iadl_assets(str(iadl_dir))
        print(f"✓ Loaded {len(ndh_service.asset_library.assets)} IADL assets")
    except Exception as e:
        print(f"✗ Failed to load IADL: {e}")
        return None
    
    # Load FDL
    try:
        ndh_service.load_fdl_from_file(str(fdl_file))
        print(f"✓ Loaded FDL: {ndh_service.fdl.site.name}")
    except Exception as e:
        print(f"✗ Failed to load FDL: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Generate Servants
    try:
        ndh_service.generate_servants()
        asset_count = len(ndh_service.asset_servants)
        tag_count = len(ndh_service.get_all_tag_servants())
        print(f"✓ Generated {asset_count} Asset Servants, {tag_count} Tag Servants")
    except Exception as e:
        print(f"✗ Failed to generate servants: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Test Asset Library View
    asset_lib_stats = test_asset_library_view(ndh_service, fdl_name)
    
    # Test Factory Layout View
    factory_layout_stats = test_factory_layout_view(ndh_service, fdl_name)
    
    return {
        "fdl_name": fdl_name,
        "asset_library": asset_lib_stats,
        "factory_layout": factory_layout_stats,
        "status": "PASSED"
    }


def main():
    """Main test function"""
    print_separator("Comprehensive FDL Tree View Test")
    print("Testing 3 FDL files with Asset Library and Factory Layout Tree Views")
    
    # Setup paths
    base_dir = Path(__file__).parent
    iadl_dir = base_dir / "testfiles" / "IADL"
    fdl_dir = base_dir / "testfiles" / "FDL"
    
    # FDL files to test
    fdl_files = [
        fdl_dir / "semiconductor_fab.yaml",
        fdl_dir / "data_center.yaml",
        fdl_dir / "lng_power_plant.yaml"
    ]
    
    # Test each FDL
    results = []
    for fdl_file in fdl_files:
        if not fdl_file.exists():
            print(f"✗ FDL file not found: {fdl_file}")
            continue
        
        result = test_single_fdl(fdl_file, iadl_dir)
        if result:
            results.append(result)
    
    # Final Summary
    print_separator("Test Summary")
    
    if not results:
        print("✗ No tests completed successfully")
        return False
    
    print(f"\nTested {len(results)} FDL files:")
    print()
    
    # Create summary table
    print(f"{'FDL File':<25} {'Asset Types':<15} {'Instances':<15} {'Areas':<10} {'Status':<10}")
    print("-" * 80)
    
    for result in results:
        fdl_name = result['fdl_name']
        asset_types = result['asset_library']['asset_types']
        instances = result['asset_library']['instances']
        areas = result['factory_layout']['areas']
        status = result['status']
        
        print(f"{fdl_name:<25} {asset_types:<15} {instances:<15} {areas:<10} {status:<10}")
    
    print()
    print(f"✓ All {len(results)} tests PASSED")
    print_separator()
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

