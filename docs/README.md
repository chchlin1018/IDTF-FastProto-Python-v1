# IDTF Fast Prototype 設計文件

本目錄包含 IDTF Fast Prototype 專案的所有核心設計文件。

## 文件清單

### 1. 軟體設計文件

**[IDTF_Fast_Prototype_Software_Design_Document_v2.1.md](./IDTF_Fast_Prototype_Software_Design_Document_v2.1.md)**

整體系統架構設計文件，整合了所有核心設計更新。

**內容**：
- 專案概述與目標
- 系統架構設計（整體架構圖、核心組件職責）
- 核心組件詳細設計（IADL/FDL Designer, NDH, Asset Pipeline）
- 數據模型與介面規範（FDL v0.1, IADL, 事件模型）
- 技術棧（Python 3.9+, PySide6, OpenUSD, uv/conda, PyInstaller/Nuitka/Briefcase）
- 部署與打包策略（GUI 框架選擇、環境管理、CI/CD 跨平台測試、打包工具選擇）
- 開發路線圖（MVP → v1.1 → v1.2）

**版本**: 2.1  
**日期**: 2025-10-22  
**PDF**: [IDTF_Fast_Prototype_Software_Design_Document_v2.1.pdf](./IDTF_Fast_Prototype_Software_Design_Document_v2.1.pdf)

---

### 2. FDL v0.1 規格文件

**[FDL_v0.1_Specification.md](./FDL_v0.1_Specification.md)**

Factory Definition Language (FDL) v0.1 的完整規格定義。

**內容**：
- FDL 概述與設計目標
- 頂層結構（version, coordinate_system, site, assets, connections）
- Asset Instance 結構（transform, tag_overrides, aabb, constraints）
- Connection 結構（路徑、屬性、約束）
- FDL → USD 組合策略（Reference + Variant）
- 驗證規則與約束
- NDH 解析器設計
- 使用範例（泵房、控制室等工業場景）

**版本**: 0.1  
**日期**: 2025-10-22  
**PDF**: [FDL_v0.1_Specification.pdf](./FDL_v0.1_Specification.pdf)

---

### 3. NDH 事件模型與 TSDB 設計更新

**[NDH_Event_Model_and_TSDB_Design_Update.md](./NDH_Event_Model_and_TSDB_Design_Update.md)**

Neutral Data Hub (NDH) 的事件模型與時序數據庫選型設計。

**內容**：
- 事件契約（Event IDL）設計
  - 基礎事件 Schema（JSON Schema）
  - 核心事件類型（TagValueChanged, InstanceCreated, AlarmRaised 等）
  - 事件版本管理（Semantic Versioning）
- 抽象 Event Bus 介面設計
  - IEventBus 介面定義
  - 傳遞保證級別（AT_MOST_ONCE, AT_LEAST_ONCE, EXACTLY_ONCE）
  - 多種實作（In-Memory, ZMQ, MQTT）
- TSDB 抽象與演進路徑
  - ITSDB 介面定義
  - 演進路徑：SQLite (MVP) → DuckDB/Parquet (Mid-term) → TDEngine/InfluxDB (Production)
  - 多種實作（SQLite TSDB, DuckDB TSDB, TDEngine TSDB）

**版本**: 1.1  
**日期**: 2025-10-22  
**PDF**: [NDH_Event_Model_and_TSDB_Design_Update.pdf](./NDH_Event_Model_and_TSDB_Design_Update.pdf)

---

### 4. 幾何座標系統與 Tag 對齊設計

**[Geometry_Coordinate_Tag_Alignment_Design.md](./Geometry_Coordinate_Tag_Alignment_Design.md)**

幾何座標系統統一與 Tag 位置對齊的技術解決方案。

**內容**：
- 問題識別與分析
  - 簡化的 Tag 位置處理問題
  - FBX → USD 轉換不一致問題
  - 缺乏驗證機制問題
- 統一座標系與單位制規範
  - IADL 座標系統規範（Z-up, 米制, 右手座標系）
  - 座標系統轉換規則
  - USD Stage Metadata 設定
- FBX → USD 轉換標準化
  - 轉換流程（載入 → 檢測 → 轉換 → 標準化 → 驗證）
  - FBXToUSDConverter 實作
- 完整 Transform 矩陣鏈處理
  - TransformUtils 實作
  - TagPositionEditor 改進
- 單元測試與驗證
  - Golden Cases 定義（簡單平移、旋轉、縮放、層級嵌套）

**版本**: 1.0  
**日期**: 2025-10-22  
**PDF**: [Geometry_Coordinate_Tag_Alignment_Design.pdf](./Geometry_Coordinate_Tag_Alignment_Design.pdf)

---

### 5. FBX 到 USD 轉換策略更新

**[FBX_to_USD_Conversion_Strategy_Update.md](./FBX_to_USD_Conversion_Strategy_Update.md)**

FBX 到 USD 轉換的外部化策略與實作方案。

**內容**：
- 挑戰與動機
  - pyassimp 手動轉換的問題（材質、法線、UV、骨架等）
- 新策略：外部化轉換流程
  - 將 FBX→USD 轉換視為獨立的預處理步驟
  - 應用程式僅負責監控和匯入已生成的 USD 檔案
- 轉換策略對比
  - pyassimp vs Autodesk FBX SDK vs Blender Python API vs USD 官方工具
  - 推薦在快速原型階段使用 Blender Python API
- 實作設計
  - Blender 轉換腳本
  - FBX 轉換服務
  - USD 驗證器
  - PyQt6 GUI 整合範例
- 結論與優勢

**版本**: 1.2  
**日期**: 2025-10-22  
**PDF**: [FBX_to_USD_Conversion_Strategy_Update.pdf](./FBX_to_USD_Conversion_Strategy_Update.pdf)

---

## 文件關係圖

```
軟體設計文件 v2.1 (整體架構)
    ├── FDL v0.1 規格 (數據模型)
    ├── NDH 事件模型與 TSDB 設計 (事件驅動架構)
    ├── 幾何座標系統與 Tag 對齊設計 (座標系統統一)
    └── FBX 到 USD 轉換策略 (資產管道)
```

## 閱讀順序建議

1. **首次閱讀**：先閱讀 [軟體設計文件 v2.1](./IDTF_Fast_Prototype_Software_Design_Document_v2.1.md)，了解整體架構和設計目標。

2. **深入理解數據模型**：閱讀 [FDL v0.1 規格](./FDL_v0.1_Specification.md)，了解工廠佈局的標準數據模型。

3. **深入理解事件驅動架構**：閱讀 [NDH 事件模型與 TSDB 設計](./NDH_Event_Model_and_TSDB_Design_Update.md)，了解事件契約、Event Bus 和 TSDB 的設計。

4. **深入理解座標系統**：閱讀 [幾何座標系統與 Tag 對齊設計](./Geometry_Coordinate_Tag_Alignment_Design.md)，了解座標系統統一和 Transform 矩陣鏈處理。

5. **深入理解資產管道**：閱讀 [FBX 到 USD 轉換策略](./FBX_to_USD_Conversion_Strategy_Update.md)，了解外部化轉換流程和實作方案。

## 版本歷史

- **2025-10-22**: 初始版本，包含所有核心設計文件
  - 軟體設計文件 v2.1
  - FDL v0.1 規格
  - NDH 事件模型與 TSDB 設計 v1.1
  - 幾何座標系統與 Tag 對齊設計 v1.0
  - FBX 到 USD 轉換策略 v1.2

