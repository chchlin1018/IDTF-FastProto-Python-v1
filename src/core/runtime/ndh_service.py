"""
NDH Service - Neutral Data Hub 服務

NDH Service 負責：
1. 讀取 FDL 文件並生成 Asset Servants
2. 管理所有 Asset Servants 和 Tag Servants 的生命週期
3. 提供統一的介面來訪問和控制 Servants
4. 協調 Event Bus、TSDB 和 Mapping Service
"""

from typing import Dict, List, Optional
from pathlib import Path

from ..eventbus.interfaces import IEventBus
from ..tsdb.interfaces import ITSDB
from ..fdl.parser import parse_fdl_file
from ..fdl.models import FDL, AssetInstance
from ..iadl.parser import parse_iadl_file
from ..iadl.models import Asset
from .asset_servant import AssetServant, AssetServantConfig
from .tag_servant import TagServantConfig
from .asset_library_svc import AssetLibraryService


class NDHService:
    """NDH Service - 管理所有 Asset Servants 和 Tag Servants"""
    
    def __init__(
        self,
        event_bus: IEventBus,
        tsdb: Optional[ITSDB] = None,
        asset_library: Optional[AssetLibraryService] = None
    ):
        self.event_bus = event_bus
        self.tsdb = tsdb
        self.asset_library = asset_library or AssetLibraryService()
        
        self.fdl: Optional[FDL] = None
        self.asset_servants: Dict[str, AssetServant] = {}  # instance_id -> AssetServant
        self.is_running: bool = False
    
    def load_fdl_from_file(self, fdl_path: str) -> None:
        """從文件加載 FDL"""
        self.fdl = parse_fdl_file(fdl_path)
        area_count = len(self.fdl.site.areas) if self.fdl.site and self.fdl.site.areas else 0
        site_name = self.fdl.site.name if self.fdl.site else "Unknown"
        print(f"Loaded FDL: {site_name} ({area_count} areas)")
    
    def load_iadl_assets(self, iadl_dir: str) -> None:
        """從目錄加載所有 IADL 資產定義"""
        iadl_path = Path(iadl_dir)
        if not iadl_path.exists():
            raise ValueError(f"IADL directory not found: {iadl_dir}")
        
        for iadl_file in iadl_path.glob("*.yaml"):
            try:
                asset = parse_iadl_file(str(iadl_file))
                self.asset_library.add_asset(asset)
                print(f"Loaded IADL asset: {asset.name} ({asset.asset_id})")
            except Exception as e:
                print(f"Failed to load {iadl_file}: {e}")
    
    def generate_servants(self) -> None:
        """生成所有 Asset Servants 和 Tag Servants"""
        if not self.fdl:
            raise ValueError("FDL not loaded. Call load_fdl_from_file() first.")
        
        print("\nGenerating Asset Servants...")
        
        # 遍歷所有 Areas 和 Instances
        if self.fdl.site and self.fdl.site.areas:
            for area in self.fdl.site.areas:
                for instance in area.instances:
                    self._create_asset_servant(instance)
        
        print(f"\nGenerated {len(self.asset_servants)} Asset Servants")
        
        # 統計 Tag Servants
        total_tags = sum(len(servant.tag_servants) for servant in self.asset_servants.values())
        print(f"Generated {total_tags} Tag Servants")
    
    def _create_asset_servant(self, instance: AssetInstance) -> None:
        """創建單個 Asset Servant"""
        # 從 Asset Library 獲取 Asset Definition
        asset_def = self.asset_library.get_asset(instance.ref_asset)
        if not asset_def:
            print(f"Warning: Asset definition not found for {instance.ref_asset}, skipping instance {instance.instance_id}")
            return
        
        # 創建 Asset Servant 配置
        config = AssetServantConfig(
            auto_publish_events=True,
            enable_tag_servants=True
        )
        
        # 創建 Asset Servant
        servant = AssetServant(
            instance=instance,
            asset_definition=asset_def,
            event_bus=self.event_bus,
            config=config
        )
        
        # 如果啟用了 TSDB，為每個 Tag Servant 設置 TSDB
        if self.tsdb:
            for tag_servant in servant.tag_servants.values():
                tag_servant.tsdb = self.tsdb
                tag_servant.config.auto_write_tsdb = True
        
        self.asset_servants[instance.instance_id] = servant
        print(f"  Created Asset Servant: {instance.instance_id} ({asset_def.name}) with {len(servant.tag_servants)} tags")
    
    def start_all_servants(self) -> None:
        """啟動所有 Servants"""
        if self.is_running:
            return
        
        print("\nStarting all Asset Servants...")
        for servant in self.asset_servants.values():
            servant.start()
        
        self.is_running = True
        print(f"Started {len(self.asset_servants)} Asset Servants")
    
    def stop_all_servants(self) -> None:
        """停止所有 Servants"""
        if not self.is_running:
            return
        
        print("\nStopping all Asset Servants...")
        for servant in self.asset_servants.values():
            servant.stop()
        
        self.is_running = False
        print(f"Stopped {len(self.asset_servants)} Asset Servants")
    
    def get_asset_servant(self, instance_id: str) -> Optional[AssetServant]:
        """獲取指定的 Asset Servant"""
        return self.asset_servants.get(instance_id)
    
    def get_all_asset_servants(self) -> List[AssetServant]:
        """獲取所有 Asset Servants"""
        return list(self.asset_servants.values())
    
    def get_all_tag_servants(self) -> List:
        """獲取所有 Tag Servants"""
        tag_servants = []
        for asset_servant in self.asset_servants.values():
            tag_servants.extend(asset_servant.get_all_tag_servants())
        return tag_servants
    
    def __repr__(self) -> str:
        return f"NDHService(assets={len(self.asset_servants)}, tags={len(self.get_all_tag_servants())}, running={self.is_running})"


# Demo
if __name__ == "__main__":
    import time
    from ..eventbus.inmem import InMemoryEventBus
    from ..tsdb.sqlite_tsdb import SQLiteTSDB
    
    # 創建 Event Bus 和 TSDB
    event_bus = InMemoryEventBus()
    tsdb = SQLiteTSDB(":memory:")
    
    # 訂閱所有事件
    def on_event(event):
        print(f"[Event] {event.event_type} from {event.source}")
    
    event_bus.subscribe("*", on_event)
    
    # 創建 NDH Service
    print("Creating NDH Service...")
    ndh = NDHService(event_bus=event_bus, tsdb=tsdb)
    
    # 加載 IADL 資產定義
    print("\nLoading IADL assets...")
    try:
        ndh.load_iadl_assets("/home/ubuntu/IDTF-FastProto-Python-v1/testfiles/IADL")
    except Exception as e:
        print(f"Error loading IADL assets: {e}")
    
    # 加載 FDL
    print("\nLoading FDL...")
    try:
        ndh.load_fdl_from_file("/home/ubuntu/IDTF-FastProto-Python-v1/testfiles/FDL/semiconductor_fab.yaml")
    except Exception as e:
        print(f"Error loading FDL: {e}")
        exit(1)
    
    # 生成 Servants
    ndh.generate_servants()
    
    print(f"\n{ndh}")
    
    # 啟動所有 Servants
    ndh.start_all_servants()
    
    # 模擬 Tag 值變化
    print("\nSimulating tag value changes...")
    time.sleep(1)
    
    # 獲取第一個 Asset Servant
    if ndh.asset_servants:
        first_servant = list(ndh.asset_servants.values())[0]
        print(f"\nUpdating tags for {first_servant.instance.instance_id}...")
        
        # 更新第一個 Tag
        tag_servants = first_servant.get_all_tag_servants()
        if tag_servants:
            tag_servants[0].update_value(25.5)
            time.sleep(0.5)
            tag_servants[0].update_value(26.0)
    
    # 停止所有 Servants
    time.sleep(1)
    ndh.stop_all_servants()
    
    print("\nDemo complete!")

