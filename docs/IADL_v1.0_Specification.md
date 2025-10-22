# IADL v1.0 規格文件

**Industrial Asset Definition Language (IADL) v1.0 Specification**

**版本**: 1.0  
**日期**: 2025-10-22  
**作者**: Michael Lin 林志錚  
**組織**: HTFA/Digital Twins Alliance

---

## 1. 概述

Industrial Asset Definition Language (IADL) 是一種用於定義工業資產的標準化語言。IADL v1.0 提供了完整的資產定義規範，包括幾何模型、座標系統、標籤（Tags）附著策略和元數據管理。

### 1.1 設計目標

IADL v1.0 的設計目標包括：

- **唯一識別**: 使用 UUIDv7 確保資產的全域唯一性和時間排序性。
- **模型引用**: 支援 USD 模型的靈活引用機制（路徑或 Reference）。
- **單位制統一**: 明確定義長度單位，確保跨系統一致性。
- **靈活的 Tag 附著**: 支援基於位置（by-pos）和基於原語（by-prim）兩種 Tag 附著策略。
- **版本化友好**: 基於原語的 Tag 附著對模型版本變更具有更好的耐受性。
- **元數據管理**: 記錄作者、版本等元數據，支援資產生命週期管理。

---

## 2. IADL v1.0 Schema

### 2.1 頂層結構

```yaml
asset_id: string (UUIDv7)           # 資產唯一識別碼
name: string                         # 資產名稱
description: string                  # 資產描述（可選）
model_ref: string                    # USD 模型引用（路徑或 Reference）
units:                               # 單位制定義
  length: string                     # 長度單位（m, cm, mm）
default_xform:                       # 預設變換矩陣
  translation: [float, float, float] # 平移（x, y, z）
  rotation: [float, float, float]    # 旋轉（歐拉角，度）
  scale: [float, float, float]       # 縮放（x, y, z）
tags: []                             # 標籤列表
metadata:                            # 元數據
  author: string                     # 作者
  version: string                    # 版本號（語義化版本）
  created_at: string                 # 創建時間（ISO 8601）
  updated_at: string                 # 更新時間（ISO 8601）
```

### 2.2 Tag 結構

```yaml
tag_id: string (UUIDv7)              # Tag 唯一識別碼
name: string                         # Tag 名稱
kind: string                         # Tag 類型（sensor, actuator, indicator, etc.）
eu_unit: string                      # 工程單位（m³/h, °C, bar, etc.）
worldSpace: boolean                  # 是否使用世界座標系（預設 false）
# Tag 附著策略（二選一）
localPosition: [float, float, float] # 基於位置（by-pos）：相對於資產原點的局部座標
attachPrimPath: string               # 基於原語（by-prim）：USD Prim 路徑
```

---

## 3. 詳細欄位說明

### 3.1 asset_id (UUIDv7)

**類型**: `string`  
**格式**: UUIDv7  
**必填**: 是

**說明**:

資產的全域唯一識別碼，使用 **UUIDv7** 格式。UUIDv7 相較於 UUIDv4 的優勢：

- **時間排序性**: UUIDv7 包含時間戳，可按生成時間排序，便於資產管理和查詢。
- **全域唯一性**: 確保在分散式系統中不會產生衝突。

**範例**:
```yaml
asset_id: "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e0f"
```

### 3.2 model_ref (USD 模型引用)

**類型**: `string`  
**必填**: 是

**說明**:

指向 USD 模型的引用，支援兩種格式：

1. **絕對路徑**: 指向本地或網路上的 USD 文件。
   ```yaml
   model_ref: "/assets/pump/pump_model.usd"
   ```

2. **USD Reference**: 使用 USD 的 Reference 語法。
   ```yaml
   model_ref: "@/assets/pump/pump_model.usd@</Pump>"
   ```

**最佳實踐**:

- 使用相對路徑或 Asset Resolver，提高可移植性。
- 確保 USD 文件遵循 Z-up、米制、右手座標系規範。

### 3.3 units (單位制定義)

**類型**: `object`  
**必填**: 是

**說明**:

定義資產使用的單位制，確保跨系統一致性。

**欄位**:

- **length** (`string`, 必填): 長度單位，支援 `m`（米）、`cm`（厘米）、`mm`（毫米）。

**範例**:
```yaml
units:
  length: "m"
```

**約束**:

- 必須與 USD 模型的 `metersPerUnit` 元數據一致。
- 建議統一使用 **米（m）** 作為標準單位。

### 3.4 default_xform (預設變換矩陣)

**類型**: `object`  
**必填**: 否

**說明**:

定義資產的預設變換矩陣，包括平移、旋轉和縮放。此變換在 FDL 中實例化資產時可被覆蓋。

**欄位**:

- **translation** (`[float, float, float]`): 平移向量（x, y, z），單位為 `units.length`。
- **rotation** (`[float, float, float]`): 旋轉向量（歐拉角，度），順序為 XYZ。
- **scale** (`[float, float, float]`): 縮放向量（x, y, z）。

**範例**:
```yaml
default_xform:
  translation: [0.0, 0.0, 0.0]
  rotation: [0.0, 0.0, 0.0]
  scale: [1.0, 1.0, 1.0]
```

**約束**:

- **縮放限制**: 製造業資產通常要求等比縮放，建議限制 `scale` 為 `[s, s, s]`，其中 `0.5 <= s <= 2.0`。
- **禁止非均勻縮放**: 非均勻縮放可能導致碰撞檢測和物理模擬錯誤。

### 3.5 tags (標籤列表)

**類型**: `array`  
**必填**: 否

**說明**:

定義資產上的標籤（Tags），用於關聯感測器、執行器、指示器等數位孿生元素。

**Tag 欄位**:

- **tag_id** (`string`, UUIDv7, 必填): Tag 的全域唯一識別碼。
- **name** (`string`, 必填): Tag 的名稱。
- **kind** (`string`, 必填): Tag 的類型，支援 `sensor`、`actuator`、`indicator`、`control_point` 等。
- **eu_unit** (`string`, 可選): 工程單位，例如 `m³/h`、`°C`、`bar`、`kW` 等。
- **worldSpace** (`boolean`, 可選, 預設 `false`): 是否使用世界座標系。若為 `true`，Tag 位置為世界座標；若為 `false`，Tag 位置為相對於資產原點的局部座標。
- **附著策略（二選一）**:
  - **localPosition** (`[float, float, float]`): 基於位置（by-pos），相對於資產原點的局部座標。
  - **attachPrimPath** (`string`): 基於原語（by-prim），USD Prim 的路徑。

**範例**:
```yaml
tags:
  - tag_id: "018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1a"
    name: "Flow Sensor"
    kind: "sensor"
    eu_unit: "m³/h"
    worldSpace: false
    attachPrimPath: "/Pump/Outlet"
  
  - tag_id: "018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1b"
    name: "Temperature Indicator"
    kind: "indicator"
    eu_unit: "°C"
    worldSpace: false
    localPosition: [0.5, 0.0, 1.2]
```

### 3.6 Tag 附著策略

#### 3.6.1 基於位置（by-pos）: localPosition

**適用場景**:

- Tag 位置固定，不隨模型幾何變化而變化。
- 簡單的資產，Tag 數量少。

**優點**:

- 簡單直觀，易於理解和實作。
- 不依賴 USD Prim 結構。

**缺點**:

- 對模型版本變更敏感：如果模型幾何發生變化，Tag 位置可能不再準確。
- 無法自動跟隨模型的局部變換。

**範例**:
```yaml
tags:
  - tag_id: "018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1b"
    name: "Pressure Sensor"
    kind: "sensor"
    eu_unit: "bar"
    worldSpace: false
    localPosition: [1.0, 0.0, 0.5]  # 相對於資產原點的局部座標
```

#### 3.6.2 基於原語（by-prim）: attachPrimPath

**適用場景**:

- Tag 需要附著在特定的幾何元素上（如閥門的出口、泵的入口）。
- 模型可能會進行版本更新，但 Prim 結構保持穩定。

**優點**:

- **版本化友好**: 只要 Prim 路徑保持不變，Tag 位置會自動跟隨模型的局部變換。
- **精確附著**: Tag 可以精確附著在特定的幾何元素上。

**缺點**:

- 需要 USD 模型具有清晰的 Prim 結構。
- 如果 Prim 路徑變更，Tag 附著會失效。

**範例**:
```yaml
tags:
  - tag_id: "018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1a"
    name: "Flow Sensor"
    kind: "sensor"
    eu_unit: "m³/h"
    worldSpace: false
    attachPrimPath: "/Pump/Outlet"  # 附著在 Pump 的 Outlet Prim 上
```

**最佳實踐**:

- **優先使用 by-prim**: 對於需要長期維護的資產，優先使用 `attachPrimPath`，以提高對模型版本變更的耐受性。
- **命名規範**: USD Prim 應遵循清晰的命名規範，例如 `/Asset/Component/SubComponent`。
- **文件化**: 在 USD 模型中添加註釋，說明關鍵 Prim 的用途和穩定性。

### 3.7 metadata (元數據)

**類型**: `object`  
**必填**: 否

**說明**:

記錄資產的元數據，支援資產生命週期管理。

**欄位**:

- **author** (`string`, 可選): 資產的創建者。
- **version** (`string`, 可選): 資產的版本號，建議使用語義化版本（Semantic Versioning），例如 `1.0.0`。
- **created_at** (`string`, 可選): 資產的創建時間，使用 ISO 8601 格式，例如 `2025-10-22T10:30:00Z`。
- **updated_at** (`string`, 可選): 資產的最後更新時間，使用 ISO 8601 格式。

**範例**:
```yaml
metadata:
  author: "Michael Lin"
  version: "1.0.0"
  created_at: "2025-10-22T10:30:00Z"
  updated_at: "2025-10-22T15:45:00Z"
```

---

## 4. 完整範例

### 4.1 範例 1: 泵（Pump）- 使用 by-prim

```yaml
asset_id: "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e0f"
name: "Centrifugal Pump Model A"
description: "High-efficiency centrifugal pump for water circulation"
model_ref: "@/assets/pumps/centrifugal_pump_a.usd@</Pump>"
units:
  length: "m"
default_xform:
  translation: [0.0, 0.0, 0.0]
  rotation: [0.0, 0.0, 0.0]
  scale: [1.0, 1.0, 1.0]
tags:
  - tag_id: "018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1a"
    name: "Inlet Flow Sensor"
    kind: "sensor"
    eu_unit: "m³/h"
    worldSpace: false
    attachPrimPath: "/Pump/Inlet"
  
  - tag_id: "018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1b"
    name: "Outlet Pressure Sensor"
    kind: "sensor"
    eu_unit: "bar"
    worldSpace: false
    attachPrimPath: "/Pump/Outlet"
  
  - tag_id: "018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1c"
    name: "Motor Temperature Indicator"
    kind: "indicator"
    eu_unit: "°C"
    worldSpace: false
    attachPrimPath: "/Pump/Motor"

metadata:
  author: "Michael Lin"
  version: "1.0.0"
  created_at: "2025-10-22T10:30:00Z"
  updated_at: "2025-10-22T10:30:00Z"
```

### 4.2 範例 2: 閥門（Valve）- 使用 by-pos

```yaml
asset_id: "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e10"
name: "Ball Valve DN50"
description: "Manual ball valve, DN50, PN16"
model_ref: "/assets/valves/ball_valve_dn50.usd"
units:
  length: "m"
default_xform:
  translation: [0.0, 0.0, 0.0]
  rotation: [0.0, 0.0, 0.0]
  scale: [1.0, 1.0, 1.0]
tags:
  - tag_id: "018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f2a"
    name: "Valve Position Indicator"
    kind: "indicator"
    eu_unit: "%"
    worldSpace: false
    localPosition: [0.0, 0.0, 0.15]  # 閥門中心上方 15cm
  
  - tag_id: "018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f2b"
    name: "Inlet Pressure Sensor"
    kind: "sensor"
    eu_unit: "bar"
    worldSpace: false
    localPosition: [-0.1, 0.0, 0.0]  # 閥門入口側

metadata:
  author: "Michael Lin"
  version: "1.0.0"
  created_at: "2025-10-22T11:00:00Z"
  updated_at: "2025-10-22T11:00:00Z"
```

---

## 5. 驗證規則

### 5.1 必填欄位驗證

- `asset_id`: 必須為有效的 UUIDv7 格式。
- `name`: 不能為空字串。
- `model_ref`: 必須為有效的 USD 路徑或 Reference。
- `units.length`: 必須為 `m`、`cm` 或 `mm`。

### 5.2 Tag 驗證

- `tag_id`: 必須為有效的 UUIDv7 格式，且在資產內唯一。
- `kind`: 必須為預定義的類型（`sensor`、`actuator`、`indicator`、`control_point` 等）。
- **附著策略**: 必須且僅能指定 `localPosition` 或 `attachPrimPath` 之一。
- `attachPrimPath`: 如果指定，必須為有效的 USD Prim 路徑。

### 5.3 縮放約束

- `default_xform.scale`: 建議為等比縮放 `[s, s, s]`，其中 `0.5 <= s <= 2.0`。
- 如果需要非均勻縮放，必須在 FDL 中明確聲明並通過驗證。

### 5.4 單位一致性

- `units.length` 必須與 USD 模型的 `metersPerUnit` 元數據一致。
- 如果不一致，應在載入時進行單位轉換。

---

## 6. 與 FDL v0.1 的整合

IADL v1.0 定義單個資產，FDL v0.1 定義工廠佈局。兩者的整合方式：

1. **資產引用**: FDL 中的 `AssetInstance` 透過 `asset_id` 引用 IADL 定義的資產。
2. **變換覆蓋**: FDL 中的 `transform` 會覆蓋 IADL 中的 `default_xform`。
3. **Tag 覆蓋**: FDL 中的 `tag_overrides` 可以覆蓋 IADL 中的 Tag 屬性（如 `eu_unit`、`localPosition`）。

**範例**:

```yaml
# FDL v0.1
assets:
  - asset_id: "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e0f"  # 引用 IADL 定義的泵
    instance_id: "pump_001"
    transform:
      translation: [10.0, 5.0, 0.0]  # 覆蓋 IADL 中的 default_xform
      rotation: [0.0, 0.0, 90.0]
      scale: [1.0, 1.0, 1.0]
    tag_overrides:
      - tag_id: "018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1a"
        eu_unit: "L/min"  # 覆蓋 IADL 中的 eu_unit
```

---

## 7. 最佳實踐

### 7.1 使用 UUIDv7

- **時間排序性**: UUIDv7 包含時間戳，便於按創建時間排序和查詢。
- **分散式友好**: 在分散式系統中生成 UUIDv7 不會產生衝突。

### 7.2 優先使用 by-prim

- **版本化友好**: `attachPrimPath` 對模型版本變更具有更好的耐受性。
- **清晰的 Prim 結構**: 確保 USD 模型具有清晰、穩定的 Prim 命名規範。

### 7.3 限制縮放

- **等比縮放**: 製造業資產通常要求等比縮放，避免非均勻縮放導致的問題。
- **縮放範圍**: 限制縮放範圍在 `0.5` 到 `2.0` 之間，避免過度縮放導致的視覺和物理問題。

### 7.4 單位統一

- **統一使用米（m）**: 建議所有資產統一使用米作為長度單位，簡化跨系統整合。
- **元數據一致性**: 確保 IADL 中的 `units.length` 與 USD 模型的 `metersPerUnit` 一致。

### 7.5 元數據管理

- **語義化版本**: 使用語義化版本號（如 `1.0.0`）管理資產版本。
- **時間戳**: 記錄創建和更新時間，便於追蹤資產生命週期。

---

## 8. 參考文件

- [FDL v0.1 規格文件](./FDL_v0.1_Specification.md)
- [軟體設計文件 v2.1](./IDTF_Fast_Prototype_Software_Design_Document_v2.1.md)
- [幾何座標系統與 Tag 對齊設計](./Geometry_Coordinate_Tag_Alignment_Design.md)
- [UUIDv7 規範](https://datatracker.ietf.org/doc/html/draft-peabody-dispatch-new-uuid-format)
- [OpenUSD 官方文件](https://openusd.org/release/index.html)

