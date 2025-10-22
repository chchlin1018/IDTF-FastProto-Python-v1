# IDTF FastProto 源代碼目錄

本目錄包含 IDTF Fast Prototype 專案的所有源代碼。

---

## 目錄結構

```
src/
├── apps/                   # 應用程式層
│   ├── iadl_designer/      # IADL Designer GUI 應用
│   ├── fdl_designer/       # FDL Designer GUI 應用
│   └── ndh_cp/             # NDH Control Panel GUI 應用
│
├── core/                   # 核心模組層
│   ├── iadl/               # IADL schema, parser, validator
│   ├── fdl/                # FDL schema, parser, validator
│   ├── usdkit/             # USD IO, utils, xform, unit conversion
│   ├── geom/               # Picking, bbox, collision helpers
│   ├── tags/               # Tag model, ID rules
│   ├── eventbus/           # Event Bus interfaces + implementations
│   ├── tsdb/               # TSDB interfaces + implementations
│   ├── io/                 # AVEVA importer, CSV, YAML, JSON
│   └── runtime/            # App services: AssetLibrarySvc, LayoutSvc, MappingSvc
│
└── tools/                  # 工具層
    ├── usd_cli/            # USD 命令行工具
    ├── fbx2usd_proxy/      # FBX 到 USD 轉換代理
    ├── fixtures/           # 測試固件
    └── dataset_generators/ # 數據集生成器
```

---

## 模組說明

### 應用程式層 (`apps/`)

#### `iadl_designer/`
**IADL Designer GUI 應用**

IADL Designer 是用於創建、編輯和驗證 IADL (Industrial Asset Definition Language) 資產定義的圖形化工具。

**主要功能**:
- 創建和編輯 IADL 資產定義
- 3D 預覽資產模型（使用 OpenUSD）
- Tag 編輯器（支援 by-pos 和 by-prim 兩種附著策略）
- 資產驗證（縮放約束、單位一致性等）
- 導出為 YAML/JSON 格式

**技術棧**:
- PySide6 (GUI)
- OpenUSD (3D 視圖)
- YAML/JSON (數據格式)

#### `fdl_designer/`
**FDL Designer GUI 應用**

FDL Designer 是用於創建、編輯和可視化工廠佈局的圖形化工具。

**主要功能**:
- 創建和編輯 FDL (Factory Definition Language) 工廠佈局
- 3D 場景編輯（拖放資產實例、調整位置和旋轉）
- 批量佈局生成（網格、直線、圓形）
- 碰撞檢測（AABB/OBB + Mesh）
- 連接編輯器（管線、電纜等）
- 導出為 YAML/JSON 和 USD 格式

**技術棧**:
- PySide6 (GUI)
- OpenUSD (3D 場景)
- trimesh (碰撞檢測)

#### `ndh_cp/`
**NDH Control Panel GUI 應用**

NDH Control Panel 是用於監控和管理 Neutral Data Hub (NDH) 的圖形化控制面板。

**主要功能**:
- 監控 Event Bus 狀態和事件流
- 查詢和可視化 TSDB 時序數據
- 管理資產實例和 Tag 實例
- 事件重放和調試
- 外部數據源整合（AVEVA, SCADA 等）

**技術棧**:
- PySide6 (GUI)
- Event Bus (ZMQ/MQTT)
- TSDB (SQLite/DuckDB/TDEngine)

---

### 核心模組層 (`core/`)

#### `iadl/`
**IADL Schema, Parser, Validator**

提供 IADL 的 Schema 定義、解析器和驗證器。

**主要模組**:
- `schema.py`: IADL v1.0 JSON Schema 定義
- `parser.py`: YAML/JSON 解析器
- `validator.py`: 驗證器（必填欄位、UUIDv7、縮放約束等）
- `models.py`: IADL 數據模型（Asset, Tag, Transform 等）

#### `fdl/`
**FDL Schema, Parser, Validator**

提供 FDL 的 Schema 定義、解析器和驗證器。

**主要模組**:
- `schema.py`: FDL v0.1 JSON Schema 定義
- `parser.py`: YAML/JSON 解析器
- `validator.py`: 驗證器（縮放約束、碰撞檢測等）
- `models.py`: FDL 數據模型（Site, Area, AssetInstance, Connection 等）
- `batch_layout.py`: 批量佈局生成器（網格、直線、圓形）

#### `usdkit/`
**USD IO, Utils, Xform, Unit Conversion**

提供 OpenUSD 的輸入輸出、工具函數、變換處理和單位轉換功能。

**主要模組**:
- `io.py`: USD 文件讀寫
- `xform.py`: Transform 矩陣處理（TransformUtils）
- `units.py`: 單位轉換（米、厘米、毫米）
- `reference.py`: USD Reference 和 Variant 處理
- `stage.py`: USD Stage 管理

#### `geom/`
**Picking, Bbox, Collision Helpers**

提供幾何操作的輔助函數，包括拾取、包圍盒和碰撞檢測。

**主要模組**:
- `picking.py`: 3D 拾取（Ray casting）
- `bbox.py`: AABB/OBB 包圍盒計算
- `collision.py`: 碰撞檢測（AABB, OBB, Mesh）
- `clearance.py`: 安全距離計算

#### `tags/`
**Tag Model, ID Rules**

提供 Tag 的數據模型和 ID 生成規則。

**主要模組**:
- `models.py`: Tag 數據模型
- `id_generator.py`: UUIDv7 生成器
- `attachment.py`: Tag 附著策略（by-pos, by-prim）

#### `eventbus/`
**Event Bus Interfaces + Implementations**

提供 Event Bus 的抽象介面和多種實作。

**主要模組**:
- `interfaces.py`: IEventBus 抽象介面
- `inmem.py`: In-Memory Event Bus（MVP）
- `zmq_bus.py`: ZMQ Event Bus
- `mqtt_bus.py`: MQTT Event Bus
- `events.py`: 事件定義（TagValueChanged, InstanceCreated 等）

#### `tsdb/`
**TSDB Interfaces + Implementations**

提供 TSDB 的抽象介面和多種實作。

**主要模組**:
- `interfaces.py`: ITSDB 抽象介面
- `sqlite_tsdb.py`: SQLite TSDB（MVP）
- `duckdb_tsdb.py`: DuckDB TSDB
- `tdengine_tsdb.py`: TDEngine TSDB

#### `io/`
**AVEVA Importer, CSV, YAML, JSON**

提供數據導入導出功能。

**主要模組**:
- `aveva_importer.py`: AVEVA 數據導入器
- `csv_io.py`: CSV 讀寫
- `yaml_io.py`: YAML 讀寫
- `json_io.py`: JSON 讀寫

#### `runtime/`
**App Services**

提供應用程式級別的服務。

**主要模組**:
- `asset_library_svc.py`: 資產庫服務（管理 IADL 資產）
- `layout_svc.py`: 佈局服務（管理 FDL 佈局）
- `mapping_svc.py`: 映射服務（Tag 到外部系統的映射）

---

### 工具層 (`tools/`)

#### `usd_cli/`
**USD 命令行工具**

提供 USD 文件的命令行操作工具。

**主要功能**:
- 查看 USD 文件信息
- 轉換 USD 文件格式（usda ↔ usdc）
- 驗證 USD 文件
- 批量處理 USD 文件

#### `fbx2usd_proxy/`
**FBX 到 USD 轉換代理**

提供 FBX 到 USD 的轉換服務。

**主要功能**:
- 監控文件夾，自動轉換 FBX 文件
- 使用 Blender Python API 進行轉換
- 驗證轉換結果（座標系統、單位制）
- 生成轉換報告

#### `fixtures/`
**測試固件**

提供測試用的固定數據和資產。

**內容**:
- 測試用的 IADL 資產定義
- 測試用的 FDL 佈局
- 測試用的 USD 模型
- Golden Cases 測試數據

#### `dataset_generators/`
**數據集生成器**

提供生成測試數據集的工具。

**主要功能**:
- 生成隨機 IADL 資產
- 生成隨機 FDL 佈局
- 生成模擬時序數據
- 生成碰撞測試案例

---

## 開發指南

### 環境設置

```bash
# 使用 uv 創建虛擬環境
uv venv
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate  # Windows

# 安裝依賴
uv pip install -r requirements.txt
```

### 運行應用

```bash
# IADL Designer
python -m src.apps.iadl_designer

# FDL Designer
python -m src.apps.fdl_designer

# NDH Control Panel
python -m src.apps.ndh_cp
```

### 運行測試

```bash
# 運行所有測試
pytest

# 運行特定模組的測試
pytest tests/core/iadl/
pytest tests/core/fdl/
```

### 代碼風格

本專案遵循 PEP 8 代碼風格指南。

```bash
# 檢查代碼風格
flake8 src/

# 自動格式化代碼
black src/
```

---

## 參考文件

- [軟體設計文件 v2.1](../docs/IDTF_Fast_Prototype_Software_Design_Document_v2.1.md)
- [IADL v1.0 規格](../docs/IADL_v1.0_Specification.md)
- [FDL v0.1 規格](../docs/FDL_v0.1_Specification.md)
- [FDL v0.1 規格更新](../docs/FDL_v0.1_Specification_Update.md)
- [NDH 事件模型與 TSDB 設計](../docs/NDH_Event_Model_and_TSDB_Design_Update.md)

