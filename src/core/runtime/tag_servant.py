"""
Tag Servant - 管理單個 Tag Instance 的狀態和行為

Tag Servant 負責：
1. 訂閱外部數據源的值變化（通過 MappingService）
2. 發布 TagValueChanged 事件到 Event Bus
3. 寫入數據到 TSDB
4. 管理 Tag 的生命週期
"""

from typing import Optional, Any
from dataclasses import dataclass
import time

from ..eventbus.interfaces import IEventBus, Event
from ..tsdb.interfaces import ITSDB, TagValue
from ..iadl.models import Tag


@dataclass
class TagServantConfig:
    """Tag Servant 配置"""
    auto_publish_events: bool = True  # 是否自動發布事件
    auto_write_tsdb: bool = False  # 是否自動寫入 TSDB（需要提供 TSDB 實例）
    value_change_threshold: Optional[float] = None  # 值變化閾值（僅對數值型 Tag 有效）


class TagServant:
    """Tag Servant - 管理單個 Tag Instance"""
    
    def __init__(
        self,
        tag_instance_id: str,
        tag_definition: Tag,
        asset_instance_id: str,
        event_bus: IEventBus,
        tsdb: Optional[ITSDB] = None,
        config: Optional[TagServantConfig] = None
    ):
        self.tag_instance_id = tag_instance_id
        self.tag_definition = tag_definition
        self.asset_instance_id = asset_instance_id
        self.event_bus = event_bus
        self.tsdb = tsdb
        self.config = config or TagServantConfig()
        
        self.current_value: Optional[Any] = None
        self.last_update_time: Optional[float] = None
        self.is_running: bool = False
    
    def start(self) -> None:
        """啟動 Tag Servant"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 訂閱外部數據源（如果有映射）
        # TODO: 通過 MappingService 訂閱外部數據源
        
        # 發布 TagCreated 事件
        if self.config.auto_publish_events:
            self._publish_tag_created()
    
    def stop(self) -> None:
        """停止 Tag Servant"""
        if not self.is_running:
            return
        
        # 取消訂閱外部數據源
        # TODO: 通過 MappingService 取消訂閱
        
        # 發布 TagDeleted 事件
        if self.config.auto_publish_events:
            self._publish_tag_deleted()
        
        self.is_running = False
    
    def update_value(self, value: Any) -> None:
        """更新 Tag 值"""
        if not self.is_running:
            return
        
        # 檢查值變化閾值
        if self.config.value_change_threshold is not None and self.current_value is not None:
            if isinstance(value, (int, float)) and isinstance(self.current_value, (int, float)):
                if abs(value - self.current_value) < self.config.value_change_threshold:
                    return  # 值變化小於閾值，不更新
        
        old_value = self.current_value
        self.current_value = value
        self.last_update_time = time.time()
        
        # 發布 TagValueChanged 事件
        if self.config.auto_publish_events:
            self._publish_tag_value_changed(old_value, value)
        
        # 寫入 TSDB
        if self.config.auto_write_tsdb and self.tsdb:
            self._write_to_tsdb(value)
    
    def get_value(self) -> Optional[Any]:
        """獲取當前值"""
        return self.current_value
    
    def get_last_update_time(self) -> Optional[float]:
        """獲取最後更新時間"""
        return self.last_update_time
    
    def _publish_tag_created(self) -> None:
        """發布 TagCreated 事件"""
        from ..tags.id_generator import generate_uuidv7
        from datetime import datetime
        
        event = Event(
            event_id=generate_uuidv7(),
            event_type="TagCreated",
            timestamp=datetime.utcnow().isoformat() + "Z",
            source=f"TagServant:{self.tag_instance_id}",
            payload={
                "tag_instance_id": self.tag_instance_id,
                "tag_id": self.tag_definition.tag_id,
                "asset_instance_id": self.asset_instance_id,
                "name": self.tag_definition.name,
                "kind": self.tag_definition.kind.value,
                "eu_unit": self.tag_definition.eu_unit
            }
        )
        self.event_bus.publish(event)
    
    def _publish_tag_value_changed(self, old_value: Any, new_value: Any) -> None:
        """發布 TagValueChanged 事件"""
        from ..tags.id_generator import generate_uuidv7
        from datetime import datetime
        
        event = Event(
            event_id=generate_uuidv7(),
            event_type="TagValueChanged",
            timestamp=datetime.utcnow().isoformat() + "Z",
            source=f"TagServant:{self.tag_instance_id}",
            payload={
                "tag_instance_id": self.tag_instance_id,
                "tag_id": self.tag_definition.tag_id,
                "asset_instance_id": self.asset_instance_id,
                "old_value": old_value,
                "new_value": new_value,
                "timestamp": self.last_update_time,
                "eu_unit": self.tag_definition.eu_unit
            }
        )
        self.event_bus.publish(event)
    
    def _publish_tag_deleted(self) -> None:
        """發布 TagDeleted 事件"""
        from ..tags.id_generator import generate_uuidv7
        from datetime import datetime
        
        event = Event(
            event_id=generate_uuidv7(),
            event_type="TagDeleted",
            timestamp=datetime.utcnow().isoformat() + "Z",
            source=f"TagServant:{self.tag_instance_id}",
            payload={
                "tag_instance_id": self.tag_instance_id,
                "tag_id": self.tag_definition.tag_id,
                "asset_instance_id": self.asset_instance_id
            }
        )
        self.event_bus.publish(event)
    
    def _write_to_tsdb(self, value: Any) -> None:
        """寫入 TSDB"""
        if not self.tsdb:
            return
        
        tag_value = TagValue(
            tag_id=self.tag_instance_id,
            timestamp=self.last_update_time or time.time(),
            value=value
        )
        self.tsdb.write_tag_value(tag_value)
    
    def __repr__(self) -> str:
        return f"TagServant(id={self.tag_instance_id}, name={self.tag_definition.name}, value={self.current_value})"


# Demo
if __name__ == "__main__":
    from ..eventbus.inmem import InMemoryEventBus
    from ..tsdb.sqlite_tsdb import SQLiteTSDB
    from ..tags.models import TagKind
    
    # 創建測試數據
    event_bus = InMemoryEventBus()
    tsdb = SQLiteTSDB(":memory:")
    
    # 創建 Tag Definition
    tag_def = Tag(
        tag_id="tag_001",
        name="Inlet Temperature",
        kind=TagKind.SENSOR,
        eu_unit="degC",
        local_position=[0.5, 0.0, 0.2]
    )
    
    # 訂閱事件
    def on_event(event: Event):
        print(f"[Event] {event.event_type} from {event.source}")
        print(f"  Payload: {event.payload}")
    
    event_bus.subscribe("*", on_event)
    
    # 創建 Tag Servant
    print("Creating Tag Servant...")
    config = TagServantConfig(auto_write_tsdb=True, value_change_threshold=0.1)
    servant = TagServant(
        tag_instance_id="pump_001_tag_001",
        tag_definition=tag_def,
        asset_instance_id="pump_001",
        event_bus=event_bus,
        tsdb=tsdb,
        config=config
    )
    
    print(f"\n{servant}")
    
    # 啟動 Tag Servant
    print("\nStarting Tag Servant...")
    servant.start()
    
    # 模擬值變化
    print("\nSimulating value changes...")
    time.sleep(0.5)
    servant.update_value(25.0)
    
    time.sleep(0.5)
    servant.update_value(25.05)  # 小於閾值，不會觸發事件
    
    time.sleep(0.5)
    servant.update_value(26.0)  # 大於閾值，會觸發事件
    
    time.sleep(0.5)
    servant.update_value(27.5)
    
    # 查詢 TSDB
    print("\nQuerying TSDB...")
    tag_values = tsdb.query_tag_values("pump_001_tag_001", 0, time.time())
    for tv in tag_values:
        print(f"  {tv}")
    
    # 停止 Tag Servant
    print("\nStopping Tag Servant...")
    time.sleep(0.5)
    servant.stop()
    
    print("\nDemo complete!")

