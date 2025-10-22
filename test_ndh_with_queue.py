#!/usr/bin/env python3.11
"""
NDH Control Panel with Queue Manager Integration Test
測試完整的工作流程：Event Bus + TSDB + Queue Manager
"""

import sys
import time
from pathlib import Path

# 添加 src 到路徑
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.eventbus.inmem import InMemoryEventBus
from core.tsdb.sqlite_tsdb import SQLiteTSDB
from core.queue.sqlite_queue import SQLiteQueueManager
from core.runtime.ndh_service import NDHService


def test_ndh_with_queue():
    """測試 NDH Service 與 Queue Manager 整合"""
    
    print("=" * 80)
    print("NDH Control Panel with Queue Manager Integration Test")
    print("=" * 80)
    
    # 1. 創建核心服務
    print("\n[Step 1] Creating core services...")
    event_bus = InMemoryEventBus()
    tsdb = SQLiteTSDB(":memory:")
    queue_manager = SQLiteQueueManager(":memory:")
    ndh_service = NDHService(event_bus=event_bus, tsdb=tsdb)
    
    print("  ✓ Event Bus created")
    print("  ✓ TSDB created")
    print("  ✓ Queue Manager created")
    print("  ✓ NDH Service created")
    
    # 2. 測試 Queue Manager
    print("\n[Step 2] Testing Queue Manager...")
    
    # 創建測試佇列
    test_queue = queue_manager.get_queue("test_queue")
    print(f"  ✓ Created queue: {test_queue}")
    
    # 放入訊息
    for i in range(5):
        msg = {
            "id": i,
            "type": "test",
            "data": f"Test message {i}"
        }
        test_queue.put(msg)
    
    print(f"  ✓ Put 5 messages into queue")
    print(f"  ✓ Queue size: {test_queue.size()}")
    
    # 取出訊息
    retrieved = []
    while test_queue.size() > 0:
        msg = test_queue.get(timeout=1.0)
        if msg:
            retrieved.append(msg)
    
    print(f"  ✓ Retrieved {len(retrieved)} messages")
    
    # 3. 載入 IADL 和 FDL
    print("\n[Step 3] Loading IADL and FDL...")
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
    
    # 4. 生成 Servants
    print("\n[Step 4] Generating Servants...")
    try:
        ndh_service.generate_servants()
        asset_count = len(ndh_service.asset_servants)
        tag_count = len(ndh_service.get_all_tag_servants())
        print(f"  ✓ Generated {asset_count} Asset Servants")
        print(f"  ✓ Generated {tag_count} Tag Servants")
    except Exception as e:
        print(f"  ✗ Failed to generate servants: {e}")
        return False
    
    # 5. 啟動 Servants 並將事件發送到佇列
    print("\n[Step 5] Starting Servants and routing events to queue...")
    
    # 創建事件佇列
    event_queue = queue_manager.get_queue("events")
    
    # 訂閱事件並發送到佇列
    event_count = {"count": 0}
    
    def on_event(event):
        event_count["count"] += 1
        # 將事件發送到佇列
        event_queue.put(event.to_dict())
        print(f"  [Event {event_count['count']}] {event.event_type} -> Queue")
    
    event_bus.subscribe("*", on_event)
    
    try:
        ndh_service.start_all_servants()
        print(f"  ✓ Started {len(ndh_service.asset_servants)} Asset Servants")
        print(f"  ✓ Events in queue: {event_queue.size()}")
    except Exception as e:
        print(f"  ✗ Failed to start servants: {e}")
        return False
    
    # 6. 從佇列讀取事件
    print("\n[Step 6] Reading events from queue...")
    time.sleep(0.5)
    
    events_from_queue = []
    while event_queue.size() > 0:
        event = event_queue.get(timeout=0.1)
        if event:
            events_from_queue.append(event)
    
    print(f"  ✓ Retrieved {len(events_from_queue)} events from queue")
    for event in events_from_queue[:5]:  # 顯示前5個事件
        print(f"    - {event['event_type']} from {event['source']}")
    
    # 7. 列出所有佇列
    print("\n[Step 7] Listing all queues...")
    all_queues = queue_manager.list_queues()
    print(f"  ✓ Found {len(all_queues)} queues:")
    for queue_name in all_queues:
        queue = queue_manager.get_queue(queue_name)
        print(f"    - {queue_name}: size={queue.size()}")
    
    # 8. 停止 Servants
    print("\n[Step 8] Stopping Servants...")
    try:
        ndh_service.stop_all_servants()
        print(f"  ✓ Stopped {len(ndh_service.asset_servants)} Asset Servants")
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
    print(f"  Events in Queue: {len(events_from_queue)}")
    print(f"  Total Queues: {len(all_queues)}")
    print(f"  Test Status: ✓ PASSED")
    print("=" * 80)
    
    return True


if __name__ == "__main__":
    success = test_ndh_with_queue()
    sys.exit(0 if success else 1)

