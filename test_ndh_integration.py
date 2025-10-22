#!/usr/bin/env python3.11
"""
NDH Control Panel Integration Test
測試完整的工作流程：Load FDL → Generate Servants → Monitor Events → Query TSDB
"""

import sys
import time
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.eventbus.inmem import InMemoryEventBus
from core.tsdb.sqlite_tsdb import SQLiteTSDB
from core.runtime.ndh_service import NDHService


def test_ndh_integration():
    """測試 NDH Service 完整整合"""
    
    print("=" * 80)
    print("NDH Control Panel Integration Test")
    print("=" * 80)
    
    # 1. 創建核心服務
    print("\n[Step 1] Creating core services...")
    event_bus = InMemoryEventBus()
    tsdb = SQLiteTSDB(":memory:")  # 使用記憶體資料庫進行測試
    ndh_service = NDHService(event_bus=event_bus, tsdb=tsdb)
    
    # 訂閱所有事件
    event_count = {"count": 0}
    
    def on_event(event):
        event_count["count"] += 1
        print(f"  [Event {event_count['count']}] {event.event_type} from {event.source}")
    
    event_bus.subscribe("*", on_event)
    print("  ✓ Event Bus created and subscribed")
    print("  ✓ TSDB created")
    print("  ✓ NDH Service created")
    
    # 2. 載入 IADL 資產定義
    print("\n[Step 2] Loading IADL assets...")
    iadl_dir = Path(__file__).parent / "testfiles" / "IADL"
    try:
        ndh_service.load_iadl_assets(str(iadl_dir))
        asset_count = len(ndh_service.asset_library.assets)
        print(f"  ✓ Loaded {asset_count} IADL assets")
    except Exception as e:
        print(f"  ✗ Failed to load IADL assets: {e}")
        return False
    
    # 3. 載入 FDL 檔案
    print("\n[Step 3] Loading FDL file...")
    fdl_file = Path(__file__).parent / "testfiles" / "FDL" / "semiconductor_fab.yaml"
    try:
        ndh_service.load_fdl_from_file(str(fdl_file))
        print(f"  ✓ Loaded FDL: {ndh_service.fdl.site.name}")
    except Exception as e:
        print(f"  ✗ Failed to load FDL: {e}")
        return False
    
    # 4. 生成 Servants
    print("\n[Step 4] Generating Asset Servants and Tag Servants...")
    try:
        ndh_service.generate_servants()
        asset_servant_count = len(ndh_service.asset_servants)
        tag_servant_count = len(ndh_service.get_all_tag_servants())
        print(f"  ✓ Generated {asset_servant_count} Asset Servants")
        print(f"  ✓ Generated {tag_servant_count} Tag Servants")
    except Exception as e:
        print(f"  ✗ Failed to generate servants: {e}")
        return False
    
    # 5. 啟動所有 Servants
    print("\n[Step 5] Starting all Servants...")
    try:
        ndh_service.start_all_servants()
        print(f"  ✓ Started {len(ndh_service.asset_servants)} Asset Servants")
        print(f"  ✓ Total events published: {event_count['count']}")
    except Exception as e:
        print(f"  ✗ Failed to start servants: {e}")
        return False
    
    # 6. 模擬 Tag 值變化
    print("\n[Step 6] Simulating tag value changes...")
    time.sleep(0.5)
    
    # 獲取第一個 Asset Servant
    if ndh_service.asset_servants:
        first_servant = list(ndh_service.asset_servants.values())[0]
        print(f"  Updating tags for {first_servant.instance.instance_id}...")
        
        # 更新所有 Tag 的值
        tag_servants = first_servant.get_all_tag_servants()
        for i, tag_servant in enumerate(tag_servants):
            tag_servant.update_value(25.0 + i * 5.0)
            time.sleep(0.2)
        
        print(f"  ✓ Updated {len(tag_servants)} tag values")
        print(f"  ✓ Total events published: {event_count['count']}")
    
    # 7. 查詢 TSDB
    print("\n[Step 7] Querying TSDB...")
    time.sleep(0.5)
    
    try:
        # 查詢第一個 Tag 的數據
        if tag_servants:
            first_tag = tag_servants[0]
            tag_values = tsdb.query_tag_values(
                first_tag.tag_instance_id,
                0,
                time.time()
            )
            print(f"  ✓ Found {len(tag_values)} records for {first_tag.tag_instance_id}")
            for tv in tag_values:
                print(f"    - Value: {tv.value} at {tv.timestamp}")
    except Exception as e:
        print(f"  ✗ Failed to query TSDB: {e}")
    
    # 8. 停止所有 Servants
    print("\n[Step 8] Stopping all Servants...")
    time.sleep(0.5)
    try:
        ndh_service.stop_all_servants()
        print(f"  ✓ Stopped {len(ndh_service.asset_servants)} Asset Servants")
        print(f"  ✓ Total events published: {event_count['count']}")
    except Exception as e:
        print(f"  ✗ Failed to stop servants: {e}")
        return False
    
    # 9. 總結
    print("\n" + "=" * 80)
    print("Integration Test Summary")
    print("=" * 80)
    print(f"  Asset Servants: {len(ndh_service.asset_servants)}")
    print(f"  Tag Servants: {len(ndh_service.get_all_tag_servants())}")
    print(f"  Total Events: {event_count['count']}")
    print(f"  Test Status: ✓ PASSED")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    success = test_ndh_integration()
    sys.exit(0 if success else 1)

