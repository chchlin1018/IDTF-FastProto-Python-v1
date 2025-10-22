#!/usr/bin/env python3.11
"""
Asset Library Tree View Integration Test
測試 Asset Library Tree View 功能
"""

import sys
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.eventbus.inmem import InMemoryEventBus
from core.tsdb.sqlite_tsdb import SQLiteTSDB
from core.runtime.ndh_service import NDHService


def test_asset_library_tree_view():
    """測試 Asset Library Tree View 功能"""
    
    print("=" * 80)
    print("Asset Library Tree View Integration Test")
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
        return False
    
    # 3. 生成 Servants
    print("\n[Step 3] Generating Servants...")
    try:
        ndh_service.generate_servants()
        asset_count = len(ndh_service.asset_servants)
        tag_count = len(ndh_service.get_all_tag_servants())
        print(f"  ✓ Generated {asset_count} Asset Servants")
        print(f"  ✓ Generated {tag_count} Tag Servants")
    except Exception as e:
        print(f"  ✗ Failed to generate servants: {e}")
        return False
    
    # 4. 模擬 Asset Library Tree View 的數據收集
    print("\n[Step 4] Simulating Asset Library Tree View data collection...")
    
    # Group servants by asset type
    from collections import defaultdict
    asset_type_groups = defaultdict(list)
    
    for servant in ndh_service.asset_servants.values():
        asset_type_name = servant.asset_definition.name
        asset_type_groups[asset_type_name].append(servant)
    
    print(f"\n  Asset Types ({len(asset_type_groups)} types):")
    
    total_instances = 0
    total_tags = 0
    
    for asset_type_name, servants in sorted(asset_type_groups.items()):
        instance_count = len(servants)
        total_instances += instance_count
        
        print(f"\n    {asset_type_name} ({instance_count} instances):")
        
        for servant in servants:
            instance_id = servant.instance.instance_id
            tag_count = len(servant.get_all_tag_servants())
            total_tags += tag_count
            
            print(f"      - Instance: {instance_id} ({tag_count} tags)")
            
            # Show first 3 tags
            for i, tag_servant in enumerate(servant.get_all_tag_servants()[:3]):
                tag_name = tag_servant.tag_definition.name
                tag_kind = tag_servant.tag_definition.kind.value
                tag_unit = tag_servant.tag_definition.eu_unit or "N/A"
                print(f"          • Tag: {tag_name} ({tag_kind}, {tag_unit})")
            
            if len(servant.get_all_tag_servants()) > 3:
                print(f"          ... and {len(servant.get_all_tag_servants()) - 3} more tags")
    
    # 5. 顯示摘要
    print("\n" + "=" * 80)
    print("Asset Library Summary")
    print("=" * 80)
    print(f"  FDL Site: {ndh_service.fdl.site.name}")
    print(f"  Total Asset Types: {len(asset_type_groups)}")
    print(f"  Total Asset Instances: {total_instances}")
    print(f"  Total Tags: {total_tags}")
    print(f"  Test Status: ✓ PASSED")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    success = test_asset_library_tree_view()
    sys.exit(0 if success else 1)

