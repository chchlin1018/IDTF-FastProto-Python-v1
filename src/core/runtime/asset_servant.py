"""
Asset Servant - 管理單個 AssetInstance 的狀態和行為

Asset Servant 負責：
1. 維護 AssetInstance 的狀態（位置、旋轉、縮放等）
2. 管理該資產的所有 Tag Servants
3. 發布資產相關的事件（InstanceCreated, InstanceUpdated, InstanceDeleted）
4. 處理資產的生命週期
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import time

from ..eventbus.interfaces import IEventBus, Event
from ..fdl.models import AssetInstance
from ..iadl.models import Asset, Tag
from .tag_servant import TagServant


@dataclass
class AssetServantConfig:
    """Asset Servant 配置"""
    auto_publish_events: bool = True  # 是否自動發布事件
    enable_tag_servants: bool = True  # 是否啟用 Tag Servants


class AssetServant:
    """Asset Servant - 管理單個 AssetInstance"""
    
    def __init__(
        self,
        instance: AssetInstance,
        asset_definition: Asset,
        event_bus: IEventBus,
        config: Optional[AssetServantConfig] = None
    ):
        self.instance = instance
        self.asset_definition = asset_definition
        self.event_bus = event_bus
        self.config = config or AssetServantConfig()
        
        self.tag_servants: Dict[str, TagServant] = {}
        self.is_running: bool = False
        
        # 初始化 Tag Servants
        if self.config.enable_tag_servants:
            self._initialize_tag_servants()
    
    def _initialize_tag_servants(self) -> None:
        """初始化所有 Tag Servants"""
        for tag in self.asset_definition.tags:
            # 創建 Tag Instance ID (instance_id + tag_id)
            tag_instance_id = f"{self.instance.instance_id}_{tag.tag_id}"
            
            tag_servant = TagServant(
                tag_instance_id=tag_instance_id,
                tag_definition=tag,
                asset_instance_id=self.instance.instance_id,
                event_bus=self.event_bus
            )
            self.tag_servants[tag.tag_id] = tag_servant
    
    def start(self) -> None:
        """啟動 Asset Servant"""
        if self.is_running:
            return
        
        self.is_running = True
        
        # 發布 InstanceCreated 事件
        if self.config.auto_publish_events:
            self._publish_instance_created()
        
        # 啟動所有 Tag Servants
        for tag_servant in self.tag_servants.values():
            tag_servant.start()
    
    def stop(self) -> None:
        """停止 Asset Servant"""
        if not self.is_running:
            return
        
        # 停止所有 Tag Servants
        for tag_servant in self.tag_servants.values():
            tag_servant.stop()
        
        # 發布 InstanceDeleted 事件
        if self.config.auto_publish_events:
            self._publish_instance_deleted()
        
        self.is_running = False
    
    def update_transform(self, translation: Optional[List[float]] = None,
                        rotation: Optional[List[float]] = None,
                        scale: Optional[List[float]] = None) -> None:
        """更新 AssetInstance 的 Transform"""
        if translation:
            self.instance.transform.translation = translation
        if rotation:
            self.instance.transform.rotation = rotation
        if scale:
            self.instance.transform.scale = scale
        
        # 發布 InstanceUpdated 事件
        if self.config.auto_publish_events:
            self._publish_instance_updated()
    
    def get_tag_servant(self, tag_id: str) -> Optional[TagServant]:
        """獲取指定的 Tag Servant"""
        return self.tag_servants.get(tag_id)
    
    def get_all_tag_servants(self) -> List[TagServant]:
        """獲取所有 Tag Servants"""
        return list(self.tag_servants.values())
    
    def _publish_instance_created(self) -> None:
        """發布 InstanceCreated 事件"""
        from ..tags.id_generator import generate_uuidv7
        from datetime import datetime
        
        event = Event(
            event_id=generate_uuidv7(),
            event_type="InstanceCreated",
            timestamp=datetime.utcnow().isoformat() + "Z",
            source=f"AssetServant:{self.instance.instance_id}",
            payload={
                "instance_id": self.instance.instance_id,
                "ref_asset": self.instance.ref_asset,
                "transform": {
                    "translation": self.instance.transform.translation,
                    "rotation": self.instance.transform.rotation,
                    "scale": self.instance.transform.scale
                }
            }
        )
        self.event_bus.publish(event)
    
    def _publish_instance_updated(self) -> None:
        """發布 InstanceUpdated 事件"""
        from ..tags.id_generator import generate_uuidv7
        from datetime import datetime
        
        event = Event(
            event_id=generate_uuidv7(),
            event_type="InstanceUpdated",
            timestamp=datetime.utcnow().isoformat() + "Z",
            source=f"AssetServant:{self.instance.instance_id}",
            payload={
                "instance_id": self.instance.instance_id,
                "transform": {
                    "translation": self.instance.transform.translation,
                    "rotation": self.instance.transform.rotation,
                    "scale": self.instance.transform.scale
                }
            }
        )
        self.event_bus.publish(event)
    
    def _publish_instance_deleted(self) -> None:
        """發布 InstanceDeleted 事件"""
        from ..tags.id_generator import generate_uuidv7
        from datetime import datetime
        
        event = Event(
            event_id=generate_uuidv7(),
            event_type="InstanceDeleted",
            timestamp=datetime.utcnow().isoformat() + "Z",
            source=f"AssetServant:{self.instance.instance_id}",
            payload={
                "instance_id": self.instance.instance_id
            }
        )
        self.event_bus.publish(event)
    
    def __repr__(self) -> str:
        return f"AssetServant(instance_id={self.instance.instance_id}, asset={self.asset_definition.name}, tags={len(self.tag_servants)})"


# Demo
if __name__ == "__main__":
    from ..eventbus.inmem import InMemoryEventBus
    from ..iadl.models import Transform, Units, Metadata
    from ..tags.models import TagKind
    
    # 創建測試數據
    event_bus = InMemoryEventBus()
    
    # 創建 Asset Definition
    asset_def = Asset(
        asset_id="018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e0f",
        name="Test Pump",
        model_ref="assets/pump.usd",
        units=Units(length="m", angle="deg"),
        default_xform=Transform(
            translation=[0.0, 0.0, 0.0],
            rotation=[0.0, 0.0, 0.0],
            scale=[1.0, 1.0, 1.0]
        ),
        tags=[
            Tag(
                tag_id="tag_001",
                name="Inlet Temperature",
                kind=TagKind.SENSOR,
                eu_unit="degC",
                local_position=[0.5, 0.0, 0.2]
            ),
            Tag(
                tag_id="tag_002",
                name="Outlet Pressure",
                kind=TagKind.SENSOR,
                eu_unit="bar",
                local_position=[0.5, 0.0, 0.8]
            )
        ],
        metadata=Metadata(author="Test", version="1.0.0")
    )
    
    # 創建 Asset Instance
    instance = AssetInstance(
        instance_id="pump_001",
        ref_asset="018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e0f",
        transform=Transform(
            translation=[10.0, 5.0, 0.0],
            rotation=[0.0, 0.0, 45.0],
            scale=[1.0, 1.0, 1.0]
        )
    )
    
    # 訂閱事件
    def on_event(event: Event):
        print(f"[Event] {event.event_type} from {event.source}: {event.payload}")
    
    event_bus.subscribe("*", on_event)
    
    # 創建 Asset Servant
    print("Creating Asset Servant...")
    servant = AssetServant(instance, asset_def, event_bus)
    
    print(f"\n{servant}")
    print(f"Tag Servants: {[ts.tag_instance_id for ts in servant.get_all_tag_servants()]}")
    
    # 啟動 Asset Servant
    print("\nStarting Asset Servant...")
    servant.start()
    
    # 模擬 Tag 值變化
    print("\nSimulating tag value changes...")
    time.sleep(0.5)
    tag_servant_1 = servant.get_tag_servant("tag_001")
    if tag_servant_1:
        tag_servant_1.update_value(25.5)
    
    time.sleep(0.5)
    tag_servant_2 = servant.get_tag_servant("tag_002")
    if tag_servant_2:
        tag_servant_2.update_value(3.2)
    
    # 更新 Transform
    print("\nUpdating transform...")
    time.sleep(0.5)
    servant.update_transform(translation=[15.0, 10.0, 0.0])
    
    # 停止 Asset Servant
    print("\nStopping Asset Servant...")
    time.sleep(0.5)
    servant.stop()
    
    print("\nDemo complete!")

