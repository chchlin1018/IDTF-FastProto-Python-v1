# IDTF Fast Prototype 實作計劃

**版本**: 1.0  
**日期**: 2025-10-22  
**作者**: Michael Lin 林志錚

---

## 執行摘要

本文件提供 IDTF Fast Prototype 專案的完整實作計劃，包括所有核心模組的詳細設計、實作優先級和測試策略。

---

## 實作狀態

### 已完成模組 ✅

#### 1. Tags 模組 (`src/core/tags/`)

**檔案**:
- ✅ `id_generator.py`: UUIDv7 生成器
- ✅ `models.py`: Tag 和 TagInstance 數據模型
- ✅ `attachment.py`: Tag 附著策略處理

**功能**:
- UUIDv7 生成（asset_id, tag_id）
- Tag 數據模型（by-pos 和 by-prim 兩種附著策略）
- Tag 世界座標計算

#### 2. IADL Models (`src/core/iadl/models.py`)

**功能**:
- Asset 數據模型
- Transform, Units, Metadata 數據模型
- 驗證邏輯（縮放約束、Tag 唯一性）

---

## 待實作模組

### 階段 1: 核心數據模組（優先級：高）

#### 1.1 IADL 模組 (`src/core/iadl/`)

**待實作檔案**:

##### `parser.py` - IADL 解析器

```python
"""IADL Parser - Parse YAML/JSON to Asset model"""

import yaml
import json
from pathlib import Path
from typing import Union
from .models import Asset


def parse_iadl_file(file_path: Union[str, Path]) -> Asset:
    """
    Parse IADL file (YAML or JSON) to Asset model.
    
    Args:
        file_path: Path to IADL file
    
    Returns:
        Asset: Parsed asset
    
    Example:
        >>> asset = parse_iadl_file("pump_001.yaml")
        >>> print(asset.name)
        Centrifugal Pump Model A
    """
    file_path = Path(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        if file_path.suffix in ['.yaml', '.yml']:
            data = yaml.safe_load(f)
        elif file_path.suffix == '.json':
            data = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    return Asset.from_dict(data)


def parse_iadl_string(content: str, format: str = 'yaml') -> Asset:
    """Parse IADL string to Asset model."""
    if format == 'yaml':
        data = yaml.safe_load(content)
    elif format == 'json':
        data = json.loads(content)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    return Asset.from_dict(data)


def write_iadl_file(asset: Asset, file_path: Union[str, Path], format: str = 'yaml'):
    """Write Asset model to IADL file."""
    file_path = Path(file_path)
    data = asset.to_dict()
    
    with open(file_path, 'w', encoding='utf-8') as f:
        if format == 'yaml':
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        elif format == 'json':
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
```

##### `validator.py` - IADL 驗證器

```python
"""IADL Validator - Validate Asset against IADL v1.0 specification"""

from typing import List, Tuple
from .models import Asset
from ..tags.id_generator import is_valid_uuidv7


class ValidationError:
    """Validation error."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
    
    def __str__(self):
        return f"{self.field}: {self.message}"


class IADLValidator:
    """IADL v1.0 Validator."""
    
    def __init__(self):
        self.errors: List[ValidationError] = []
    
    def validate(self, asset: Asset) -> Tuple[bool, List[ValidationError]]:
        """
        Validate asset against IADL v1.0 specification.
        
        Args:
            asset: Asset to validate
        
        Returns:
            Tuple[bool, List[ValidationError]]: (is_valid, errors)
        """
        self.errors = []
        
        # Validate asset_id (UUIDv7)
        if not is_valid_uuidv7(asset.asset_id):
            self.errors.append(ValidationError(
                "asset_id",
                f"Invalid UUIDv7 format: {asset.asset_id}"
            ))
        
        # Validate name
        if not asset.name or not asset.name.strip():
            self.errors.append(ValidationError("name", "name cannot be empty"))
        
        # Validate model_ref
        if not asset.model_ref or not asset.model_ref.strip():
            self.errors.append(ValidationError("model_ref", "model_ref cannot be empty"))
        
        # Validate units
        try:
            asset.units.validate()
        except ValueError as e:
            self.errors.append(ValidationError("units", str(e)))
        
        # Validate default_xform
        try:
            asset.default_xform.validate(allow_scaling=True, allow_non_uniform_scaling=False)
        except ValueError as e:
            self.errors.append(ValidationError("default_xform", str(e)))
        
        # Validate tags
        tag_ids = set()
        for i, tag in enumerate(asset.tags):
            # Check tag_id uniqueness
            if tag.tag_id in tag_ids:
                self.errors.append(ValidationError(
                    f"tags[{i}].tag_id",
                    f"Duplicate tag_id: {tag.tag_id}"
                ))
            tag_ids.add(tag.tag_id)
            
            # Validate tag_id (UUIDv7)
            if not is_valid_uuidv7(tag.tag_id):
                self.errors.append(ValidationError(
                    f"tags[{i}].tag_id",
                    f"Invalid UUIDv7 format: {tag.tag_id}"
                ))
            
            # Validate tag attachment
            try:
                tag._validate()
            except ValueError as e:
                self.errors.append(ValidationError(f"tags[{i}]", str(e)))
        
        return len(self.errors) == 0, self.errors
```

---

#### 1.2 FDL 模組 (`src/core/fdl/`)

**待實作檔案**:

##### `models.py` - FDL 數據模型

```python
"""FDL Models - Factory Description Language data models"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from ..iadl.models import Transform


@dataclass
class Site:
    """Site definition."""
    name: str
    site_id: Optional[str] = None
    location: Optional[Dict[str, float]] = None  # latitude, longitude, altitude
    areas: List["Area"] = field(default_factory=list)


@dataclass
class Area:
    """Area definition."""
    name: str
    area_id: Optional[str] = None
    type: str = "production"  # production, storage, control, utility
    instances: List["AssetInstance"] = field(default_factory=list)
    connections: List["Connection"] = field(default_factory=list)


@dataclass
class AssetInstance:
    """Asset instance definition."""
    instance_id: str
    ref_asset: str  # Reference to IADL asset_id
    name: Optional[str] = None
    transform: Transform = field(default_factory=Transform)
    tag_overrides: List[Dict[str, Any]] = field(default_factory=list)
    collision_bounds: Optional[Dict[str, Any]] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Connection:
    """Connection definition."""
    connection_id: str
    type: str  # pipe, cable, duct
    name: Optional[str] = None
    from_instance: str
    from_port: Optional[str] = None
    to_instance: str
    to_port: Optional[str] = None
    path: Optional[Dict[str, Any]] = None
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FDL:
    """FDL (Factory Description Language) definition."""
    fdl_version: str = "0.1"
    units: Dict[str, str] = field(default_factory=lambda: {
        "length": "mm",
        "angle": "deg",
        "up_axis": "Z",
        "handedness": "right"
    })
    site: Optional[Site] = None
    global_constraints: Dict[str, Any] = field(default_factory=dict)
    batch_layouts: List[Dict[str, Any]] = field(default_factory=list)
```

##### `batch_layout.py` - 批量佈局生成器

```python
"""Batch Layout Generator - Generate grid, line, circle layouts"""

import numpy as np
from typing import List, Dict, Any
from .models import AssetInstance, Transform


def generate_grid_layout(
    ref_asset: str,
    rows: int,
    columns: int,
    spacing_x: float,
    spacing_y: float,
    origin: List[float],
    naming_prefix: str = "Asset"
) -> List[AssetInstance]:
    """
    Generate grid layout.
    
    Args:
        ref_asset: Reference asset ID
        rows: Number of rows
        columns: Number of columns
        spacing_x: X-axis spacing
        spacing_y: Y-axis spacing
        origin: Origin position [x, y, z]
        naming_prefix: Instance ID prefix
    
    Returns:
        List[AssetInstance]: Generated instances
    """
    instances = []
    
    for row in range(rows):
        for col in range(columns):
            instance_id = f"{naming_prefix}_{row:02d}_{col:02d}"
            translation = [
                origin[0] + col * spacing_x,
                origin[1] + row * spacing_y,
                origin[2]
            ]
            
            instance = AssetInstance(
                instance_id=instance_id,
                ref_asset=ref_asset,
                transform=Transform(translation=translation)
            )
            instances.append(instance)
    
    return instances


def generate_line_layout(
    ref_asset: str,
    count: int,
    start: List[float],
    end: List[float],
    naming_prefix: str = "Asset"
) -> List[AssetInstance]:
    """Generate line layout."""
    instances = []
    start_arr = np.array(start)
    end_arr = np.array(end)
    direction = (end_arr - start_arr) / (count - 1) if count > 1 else np.zeros(3)
    
    for i in range(count):
        instance_id = f"{naming_prefix}_{i:02d}"
        translation = (start_arr + i * direction).tolist()
        
        instance = AssetInstance(
            instance_id=instance_id,
            ref_asset=ref_asset,
            transform=Transform(translation=translation)
        )
        instances.append(instance)
    
    return instances


def generate_circle_layout(
    ref_asset: str,
    count: int,
    center: List[float],
    radius: float,
    start_angle: float = 0.0,
    naming_prefix: str = "Asset"
) -> List[AssetInstance]:
    """Generate circle layout."""
    instances = []
    center_arr = np.array(center)
    angle_step = 360.0 / count
    
    for i in range(count):
        instance_id = f"{naming_prefix}_{i:02d}"
        angle = start_angle + i * angle_step
        angle_rad = np.radians(angle)
        
        translation = center_arr + np.array([
            radius * np.cos(angle_rad),
            radius * np.sin(angle_rad),
            0
        ])
        
        instance = AssetInstance(
            instance_id=instance_id,
            ref_asset=ref_asset,
            transform=Transform(
                translation=translation.tolist(),
                rotation=[0.0, 0.0, angle]
            )
        )
        instances.append(instance)
    
    return instances
```

---

### 階段 2: USD 與幾何模組（優先級：高）

#### 2.1 USD Kit 模組 (`src/core/usdkit/`)

**待實作檔案**:

##### `xform.py` - Transform 工具

```python
"""USD Transform Utilities"""

import numpy as np
from typing import List, Tuple
from pxr import Usd, UsdGeom, Gf


class TransformUtils:
    """Transform matrix utilities."""
    
    @staticmethod
    def create_transform_matrix(
        translation: List[float],
        rotation: List[float],
        scale: List[float]
    ) -> np.ndarray:
        """
        Create 4x4 transform matrix from translation, rotation, scale.
        
        Args:
            translation: [x, y, z]
            rotation: [rx, ry, rz] in degrees (Euler angles)
            scale: [sx, sy, sz]
        
        Returns:
            np.ndarray: 4x4 transform matrix
        """
        # Create translation matrix
        T = np.eye(4)
        T[:3, 3] = translation
        
        # Create rotation matrices (XYZ order)
        rx, ry, rz = np.radians(rotation)
        
        Rx = np.array([
            [1, 0, 0, 0],
            [0, np.cos(rx), -np.sin(rx), 0],
            [0, np.sin(rx), np.cos(rx), 0],
            [0, 0, 0, 1]
        ])
        
        Ry = np.array([
            [np.cos(ry), 0, np.sin(ry), 0],
            [0, 1, 0, 0],
            [-np.sin(ry), 0, np.cos(ry), 0],
            [0, 0, 0, 1]
        ])
        
        Rz = np.array([
            [np.cos(rz), -np.sin(rz), 0, 0],
            [np.sin(rz), np.cos(rz), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        R = Rz @ Ry @ Rx
        
        # Create scale matrix
        S = np.diag([scale[0], scale[1], scale[2], 1.0])
        
        # Combine: T * R * S
        return T @ R @ S
    
    @staticmethod
    def get_world_transform(prim: Usd.Prim) -> Gf.Matrix4d:
        """Get world transform of a USD prim."""
        xformable = UsdGeom.Xformable(prim)
        return xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default())
```

##### `units.py` - 單位轉換

```python
"""Unit Conversion Utilities"""

METERS_PER_UNIT = {
    "m": 1.0,
    "cm": 0.01,
    "mm": 0.001,
    "in": 0.0254,
    "ft": 0.3048
}


def convert_length(value: float, from_unit: str, to_unit: str) -> float:
    """Convert length from one unit to another."""
    if from_unit not in METERS_PER_UNIT:
        raise ValueError(f"Unknown unit: {from_unit}")
    if to_unit not in METERS_PER_UNIT:
        raise ValueError(f"Unknown unit: {to_unit}")
    
    # Convert to meters first
    meters = value * METERS_PER_UNIT[from_unit]
    
    # Convert to target unit
    return meters / METERS_PER_UNIT[to_unit]
```

---

#### 2.2 Geom 模組 (`src/core/geom/`)

**待實作檔案**:

##### `bbox.py` - 包圍盒計算

```python
"""Bounding Box Utilities"""

from dataclasses import dataclass
from typing import List
import numpy as np


@dataclass
class AABB:
    """Axis-Aligned Bounding Box."""
    min: List[float]  # [x, y, z]
    max: List[float]  # [x, y, z]
    
    def intersects(self, other: "AABB") -> bool:
        """Check if this AABB intersects with another."""
        return (
            self.min[0] <= other.max[0] and self.max[0] >= other.min[0] and
            self.min[1] <= other.max[1] and self.max[1] >= other.min[1] and
            self.min[2] <= other.max[2] and self.max[2] >= other.min[2]
        )
    
    def contains_point(self, point: List[float]) -> bool:
        """Check if this AABB contains a point."""
        return (
            self.min[0] <= point[0] <= self.max[0] and
            self.min[1] <= point[1] <= self.max[1] and
            self.min[2] <= point[2] <= self.max[2]
        )
```

##### `collision.py` - 碰撞檢測

```python
"""Collision Detection Utilities"""

from typing import List, Tuple
from .bbox import AABB


def detect_aabb_collisions(aabbs: List[Tuple[str, AABB]]) -> List[Tuple[str, str]]:
    """
    Detect AABB collisions using broadphase.
    
    Args:
        aabbs: List of (instance_id, AABB) tuples
    
    Returns:
        List[Tuple[str, str]]: List of colliding instance ID pairs
    """
    collisions = []
    
    for i in range(len(aabbs)):
        for j in range(i + 1, len(aabbs)):
            id1, aabb1 = aabbs[i]
            id2, aabb2 = aabbs[j]
            
            if aabb1.intersects(aabb2):
                collisions.append((id1, id2))
    
    return collisions
```

---

### 階段 3: 事件與數據模組（優先級：中）

#### 3.1 Event Bus 模組 (`src/core/eventbus/`)

**待實作檔案**:

##### `interfaces.py` - Event Bus 介面

```python
"""Event Bus Interfaces"""

from abc import ABC, abstractmethod
from typing import Callable, Any, List
from enum import Enum


class DeliveryGuarantee(Enum):
    """Event delivery guarantee level."""
    AT_MOST_ONCE = "at_most_once"
    AT_LEAST_ONCE = "at_least_once"
    EXACTLY_ONCE = "exactly_once"


class IEventBus(ABC):
    """Event Bus abstract interface."""
    
    @abstractmethod
    def publish(self, event_type: str, event_data: dict, guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE):
        """Publish an event."""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, callback: Callable[[dict], None]):
        """Subscribe to an event type."""
        pass
    
    @abstractmethod
    def unsubscribe(self, event_type: str, callback: Callable[[dict], None]):
        """Unsubscribe from an event type."""
        pass
```

##### `inmem.py` - In-Memory Event Bus

```python
"""In-Memory Event Bus Implementation"""

from typing import Callable, Dict, List
from .interfaces import IEventBus, DeliveryGuarantee


class InMemoryEventBus(IEventBus):
    """In-memory event bus (MVP implementation)."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
    
    def publish(self, event_type: str, event_data: dict, guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE):
        """Publish event to all subscribers."""
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(event_data)
                except Exception as e:
                    print(f"Error in event handler: {e}")
    
    def subscribe(self, event_type: str, callback: Callable[[dict], None]):
        """Subscribe to event type."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable[[dict], None]):
        """Unsubscribe from event type."""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)
```

---

#### 3.2 TSDB 模組 (`src/core/tsdb/`)

**待實作檔案**:

##### `interfaces.py` - TSDB 介面

```python
"""TSDB Interfaces"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class ITSDB(ABC):
    """Time-Series Database abstract interface."""
    
    @abstractmethod
    def write_tag_value(self, tag_id: str, timestamp: int, value: Any):
        """Write a tag value."""
        pass
    
    @abstractmethod
    def query_tag_values(
        self,
        tag_id: str,
        start_time: int,
        end_time: int,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query tag values in a time range."""
        pass
```

##### `sqlite_tsdb.py` - SQLite TSDB

```python
"""SQLite TSDB Implementation"""

import sqlite3
from typing import List, Dict, Any, Optional
from .interfaces import ITSDB


class SQLiteTSDB(ITSDB):
    """SQLite-based TSDB (MVP implementation)."""
    
    def __init__(self, db_path: str = ":memory:"):
        self.conn = sqlite3.connect(db_path)
        self._create_tables()
    
    def _create_tables(self):
        """Create tables."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tag_values (
                tag_id TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                value REAL,
                PRIMARY KEY (tag_id, timestamp)
            )
        """)
        self.conn.commit()
    
    def write_tag_value(self, tag_id: str, timestamp: int, value: Any):
        """Write tag value."""
        self.conn.execute(
            "INSERT OR REPLACE INTO tag_values (tag_id, timestamp, value) VALUES (?, ?, ?)",
            (tag_id, timestamp, float(value))
        )
        self.conn.commit()
    
    def query_tag_values(
        self,
        tag_id: str,
        start_time: int,
        end_time: int,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Query tag values."""
        query = """
            SELECT timestamp, value
            FROM tag_values
            WHERE tag_id = ? AND timestamp >= ? AND timestamp <= ?
            ORDER BY timestamp
        """
        
        if limit:
            query += f" LIMIT {limit}"
        
        cursor = self.conn.execute(query, (tag_id, start_time, end_time))
        
        results = []
        for row in cursor:
            results.append({
                "timestamp": row[0],
                "value": row[1]
            })
        
        return results
```

---

## 實作優先級

### P0 (立即實作)
- ✅ Tags 模組
- ✅ IADL models
- ⏳ IADL parser, validator
- ⏳ FDL models, parser, validator
- ⏳ FDL batch_layout

### P1 (短期實作，1-2 週)
- ⏳ USD Kit (xform, units, io)
- ⏳ Geom (bbox, collision)
- ⏳ Event Bus (interfaces, inmem)
- ⏳ TSDB (interfaces, sqlite)

### P2 (中期實作，1 個月)
- ⏳ IO 模組 (yaml, json, csv)
- ⏳ Runtime 服務 (AssetLibrarySvc, LayoutSvc)
- ⏳ Tools (usd_cli, fbx2usd_proxy)

### P3 (長期實作，3 個月)
- ⏳ GUI 應用 (IADL Designer, FDL Designer, NDH CP)
- ⏳ Event Bus (zmq, mqtt)
- ⏳ TSDB (duckdb, tdengine)

---

## 測試策略

### 單元測試

使用 pytest 進行單元測試：

```bash
# 測試目錄結構
tests/
├── core/
│   ├── tags/
│   │   ├── test_id_generator.py
│   │   ├── test_models.py
│   │   └── test_attachment.py
│   ├── iadl/
│   │   ├── test_models.py
│   │   ├── test_parser.py
│   │   └── test_validator.py
│   └── fdl/
│       ├── test_models.py
│       ├── test_parser.py
│       └── test_batch_layout.py
```

### Golden Cases 測試

創建標準測試案例：

```
tests/fixtures/
├── iadl/
│   ├── pump_001.yaml
│   ├── valve_001.yaml
│   └── tank_001.yaml
├── fdl/
│   ├── pump_room.yaml
│   └── tank_farm.yaml
└── usd/
    ├── pump_model.usd
    └── valve_model.usd
```

---

## 下一步行動

1. **完成 IADL 和 FDL 模組**
   - 實作 parser 和 validator
   - 實作 batch_layout
   - 撰寫單元測試

2. **實作 USD Kit 和 Geom 模組**
   - 實作 Transform 工具
   - 實作 AABB 和碰撞檢測
   - 撰寫單元測試

3. **實作 Event Bus 和 TSDB 模組**
   - 實作 In-Memory Event Bus
   - 實作 SQLite TSDB
   - 撰寫單元測試

4. **開始 GUI 應用開發**
   - 設計 GUI 介面
   - 實作 IADL Designer
   - 實作 FDL Designer

---

## 參考文件

- [軟體設計文件 v2.1](./docs/IDTF_Fast_Prototype_Software_Design_Document_v2.1.md)
- [IADL v1.0 規格](./docs/IADL_v1.0_Specification.md)
- [FDL v0.1 規格](./docs/FDL_v0.1_Specification.md)
- [FDL v0.1 規格更新](./docs/FDL_v0.1_Specification_Update.md)

