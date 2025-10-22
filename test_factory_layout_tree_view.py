#!/usr/bin/env python3.11
"""
Factory Layout Tree View Integration Test
測試 Factory Layout Tree View 功能
"""

import sys
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.eventbus.inmem import InMemoryEventBus
from core.tsdb.sqlite_tsdb import SQLiteTSDB
from core.runtime.ndh_service import NDHService


def print_tree_structure(fdl, indent=0):
    """Print FDL structure in tree format"""
    prefix = "  " * indent
    
    # Site
    print(f"{prefix}FDL: {fdl.site.name}")
    
    # Site Properties
    print(f"{prefix}  Site Properties:")
    print(f"{prefix}    Site ID: {fdl.site.site_id}")
    if fdl.site.location:
        print(f"{prefix}    Location: {fdl.site.location}")
    if fdl.units:
        print(f"{prefix}    Units: Length={fdl.units.length.value}, "
              f"Angle={fdl.units.angle.value}, "
              f"Up={fdl.units.up_axis.value}, "
              f"Hand={fdl.units.handedness.value}")
    print(f"{prefix}    Total Areas: {len(fdl.site.areas)}")
    
    # Areas
    for area in fdl.site.areas:
        print(f"{prefix}  Area: {area.name}")
        print(f"{prefix}    Area Properties:")
        print(f"{prefix}      Area ID: {area.area_id}")
        print(f"{prefix}      Type: {area.type}")
        print(f"{prefix}      Instance Count: {len(area.instances)}")
        print(f"{prefix}      Connection Count: {len(area.connections)}")
        
        # Asset Instances
        print(f"{prefix}    Asset Instances ({len(area.instances)} instances):")
        for instance in area.instances[:3]:  # Show first 3
            print(f"{prefix}      Instance: {instance.instance_id}")
            print(f"{prefix}        Ref Asset: {instance.ref_asset}")
            if instance.name:
                print(f"{prefix}        Name: {instance.name}")
            print(f"{prefix}        Transform: T={instance.transform.translation}, "
                  f"R={instance.transform.rotation}, "
                  f"S={instance.transform.scale}")
            if instance.tag_overrides:
                print(f"{prefix}        Tag Overrides: {len(instance.tag_overrides)} overrides")
            if instance.metadata:
                print(f"{prefix}        Metadata: {list(instance.metadata.keys())}")
        
        if len(area.instances) > 3:
            print(f"{prefix}      ... and {len(area.instances) - 3} more instances")
        
        # Connections
        if area.connections:
            print(f"{prefix}    Connections ({len(area.connections)} connections):")
            for connection in area.connections[:3]:  # Show first 3
                print(f"{prefix}      Connection: {connection.connection_id}")
                print(f"{prefix}        Type: {connection.type}")
                print(f"{prefix}        From: {connection.from_instance}")
                print(f"{prefix}        To: {connection.to_instance}")
            
            if len(area.connections) > 3:
                print(f"{prefix}      ... and {len(area.connections) - 3} more connections")
    
    # Global Settings
    print(f"{prefix}  Global Settings:")
    if fdl.global_constraints:
        if fdl.global_constraints.scaling_constraints:
            sc = fdl.global_constraints.scaling_constraints
            print(f"{prefix}    Scaling Constraints:")
            print(f"{prefix}      Allow Scaling: {sc.allow_scaling}")
            print(f"{prefix}      Allow Non-Uniform: {sc.allow_non_uniform_scaling}")
            if sc.min_scale is not None:
                print(f"{prefix}      Min Scale: {sc.min_scale}")
            if sc.max_scale is not None:
                print(f"{prefix}      Max Scale: {sc.max_scale}")
        
        if fdl.global_constraints.collision_detection:
            cd = fdl.global_constraints.collision_detection
            print(f"{prefix}    Collision Detection:")
            print(f"{prefix}      Enabled: {cd.enabled}")
            print(f"{prefix}      Clearance Distance: {cd.clearance_distance} m")


def test_factory_layout_tree_view():
    """測試 Factory Layout Tree View 功能"""
    
    print("=" * 80)
    print("Factory Layout Tree View Integration Test")
    print("=" * 80)
    
    # 1. 創建核心服務
    print("\n[Step 1] Creating core services...")
    event_bus = InMemoryEventBus()
    tsdb = SQLiteTSDB(":memory:")
    ndh_service = NDHService(event_bus=event_bus, tsdb=tsdb)
    
    print("  ✓ Event Bus created")
    print("  ✓ TSDB created")
    print("  ✓ NDH Service created")
    
    # 2. 載入 IADL 和 FDL
    print("\n[Step 2] Loading IADL and FDL...")
    iadl_dir = Path(__file__).parent / "testfiles" / "IADL"
    fdl_file = Path(__file__).parent / "testfiles" / "FDL" / "semiconductor_fab.yaml"
    
    try:
        ndh_service.load_iadl_assets(str(iadl_dir))
        print(f"  ✓ Loaded {len(ndh_service.asset_library.assets)} IADL assets")
        
        ndh_service.load_fdl_from_file(str(fdl_file))
        print(f"  ✓ Loaded FDL: {ndh_service.fdl.site.name}")
    except Exception as e:
        print(f"  ✗ Failed to load assets: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 顯示 FDL 結構
    print("\n[Step 3] Displaying FDL structure...")
    print()
    print_tree_structure(ndh_service.fdl)
    
    # 4. 統計資訊
    print("\n" + "=" * 80)
    print("Factory Layout Summary")
    print("=" * 80)
    
    total_instances = sum(len(area.instances) for area in ndh_service.fdl.site.areas)
    total_connections = sum(len(area.connections) for area in ndh_service.fdl.site.areas)
    
    print(f"  FDL Site: {ndh_service.fdl.site.name}")
    print(f"  Total Areas: {len(ndh_service.fdl.site.areas)}")
    print(f"  Total Asset Instances: {total_instances}")
    print(f"  Total Connections: {total_connections}")
    print(f"  Test Status: ✓ PASSED")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    success = test_factory_layout_tree_view()
    sys.exit(0 if success else 1)

