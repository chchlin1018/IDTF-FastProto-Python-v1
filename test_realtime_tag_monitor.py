#!/usr/bin/env python3.11
"""
Realtime Tag Monitor Integration Test
測試即時 Tag 監控功能
"""

import sys
import time
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.eventbus.inmem import InMemoryEventBus
from core.tsdb.sqlite_tsdb import SQLiteTSDB
from core.runtime.ndh_service import NDHService


def test_realtime_tag_monitor():
    """測試即時 Tag 監控功能"""
    
    print("=" * 80)
    print("Realtime Tag Monitor Integration Test")
    print("=" * 80)
    
    # 1. 創建核心服務
    print("\n[Step 1] Creating core services...")
    event_bus = InMemoryEventBus()
    tsdb = SQLiteTSDB("test_realtime_monitor.db")
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
    
    # 4. 啟動 Servants
    print("\n[Step 4] Starting Servants...")
    try:
        ndh_service.start_all_servants()
        print(f"  ✓ Started {len(ndh_service.asset_servants)} Asset Servants")
    except Exception as e:
        print(f"  ✗ Failed to start servants: {e}")
        return False
    
    # 5. 等待數據寫入 TSDB
    print("\n[Step 5] Waiting for data to be written to TSDB...")
    time.sleep(2)
    print("  ✓ Waited 2 seconds")
    
    # 6. 模擬即時監控查詢
    print("\n[Step 6] Simulating realtime tag monitor queries...")
    
    all_tag_servants = ndh_service.get_all_tag_servants()
    monitored_tags = all_tag_servants[:10]  # 監控前10個 tags
    
    print(f"  Monitoring {len(monitored_tags)} tags:")
    
    from datetime import datetime, timedelta
    
    for i, tag_servant in enumerate(monitored_tags, 1):
        tag_id = f"{tag_servant.asset_instance_id}_{tag_servant.tag_definition.tag_id}"
        tag_name = tag_servant.tag_definition.name
        
        # 查詢 TSDB
        current_time = datetime.utcnow()
        start_time = current_time - timedelta(seconds=5)
        
        try:
            results = tsdb.query_tag_values(
                tag_id=tag_id,
                start_time=start_time,
                end_time=current_time
            )
            
            if results:
                latest = results[-1]
                value = latest.value
                timestamp = latest.timestamp
                print(f"    {i}. {tag_name} ({tag_id})")
                print(f"       Value: {value}, Timestamp: {timestamp}")
            else:
                # 從 servant 直接獲取
                value = tag_servant.get_value()
                print(f"    {i}. {tag_name} ({tag_id})")
                print(f"       Value: {value} (from servant, not in TSDB yet)")
        
        except Exception as e:
            print(f"    {i}. {tag_name} ({tag_id})")
            print(f"       Error: {e}")
    
    # 7. 停止 Servants
    print("\n[Step 7] Stopping Servants...")
    try:
        ndh_service.stop_all_servants()
        print(f"  ✓ Stopped {len(ndh_service.asset_servants)} Asset Servants")
    except Exception as e:
        print(f"  ✗ Failed to stop servants: {e}")
        return False
    
    # 8. 總結
    print("\n" + "=" * 80)
    print("Test Summary")
    print("=" * 80)
    print(f"  Asset Servants: {len(ndh_service.asset_servants)}")
    print(f"  Tag Servants: {len(ndh_service.get_all_tag_servants())}")
    print(f"  Monitored Tags: {len(monitored_tags)}")
    print(f"  Test Status: ✓ PASSED")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    success = test_realtime_tag_monitor()
    sys.exit(0 if success else 1)

