# IDTF Fast Prototype - Python Implementation v1

**Industrial Digital Twin Framework (IDTF) Fast Prototype** 是一個基於 Python 的快速原型設計工具，用於創建、編輯和模擬工業數位孿生場景。

## 專案概述

IDTF Fast Prototype 支援 IADL (Industrial Asset Definition Language) 和 FDL (Factory Definition Language)，實現從資產定義到工廠佈局的完整工作流程。

### 核心特性

- **標準化數據模型**: 採用 FDL v0.1 作為工廠佈局的標準，統一 IADL 中的座標系統規範
- **事件驅動架構**: 引入 NDH（Neutral Data Hub）作為事件中心，實現模組之間的解耦和異步通信
- **高保真資產管道**: 建立外部化的、標準化的 FBX 到 USD 轉換管道
- **可演進的技術棧**: 設計抽象的 Event Bus 和 TSDB 介面，支援從 MVP 到生產級的平滑過渡

## 技術棧

| 類別 | 技術 |
|---|---|
| **程式語言** | Python 3.9+ |
| **GUI 框架** | PySide6 (LGPL) |
| **3D 圖形** | OpenUSD (Python API) |
| **數據格式** | YAML, JSON |
| **事件總線 (MVP)** | In-Memory (同步) |
| **時序數據庫 (MVP)** | SQLite |
| **3D 模型轉換** | Blender (Python API) |
| **環境管理** | uv 或 conda |
| **打包工具 (MVP)** | PyInstaller |
| **打包工具 (備選)** | Nuitka 或 Briefcase |

## 文件

所有設計文件位於 [`/docs`](./docs) 目錄：

### 核心規格

- [**FDL v0.1 規格文件**](./docs/FDL_v0.1_Specification.md) - 工廠描述語言的完整規格定義
  - 頂層結構、座標系統規範、資產實例定義
  - USD 組合策略（Reference + Variant）
  - 驗證規則與約束
  - [PDF 版本](./docs/FDL_v0.1_Specification.pdf)

### 設計文件

- [**軟體設計文件 v2.1**](./docs/IDTF_Fast_Prototype_Software_Design_Document_v2.1.md) - 整體系統架構設計
  - 系統架構圖
  - 核心組件設計（IADL/FDL Designer, NDH, Asset Pipeline）
  - 數據模型與介面規範
  - 部署與打包策略
  - 開發路線圖
  - [PDF 版本](./docs/IDTF_Fast_Prototype_Software_Design_Document_v2.1.pdf)

- [**NDH 事件模型與 TSDB 設計更新**](./docs/NDH_Event_Model_and_TSDB_Design_Update.md)
  - 事件契約（JSON Schema）
  - Event Bus 抽象介面（IEventBus）
  - TSDB 抽象介面（ITSDB）
  - 演進路徑（SQLite → DuckDB → TDEngine/InfluxDB）
  - [PDF 版本](./docs/NDH_Event_Model_and_TSDB_Design_Update.pdf)

- [**幾何座標系統與 Tag 對齊設計**](./docs/Geometry_Coordinate_Tag_Alignment_Design.md)
  - 統一座標系統規範（Z-up, 米制, 右手座標系）
  - FBX → USD 轉換標準化
  - Transform 矩陣鏈處理
  - Golden Cases 單元測試
  - [PDF 版本](./docs/Geometry_Coordinate_Tag_Alignment_Design.pdf)

- [**FBX 到 USD 轉換策略更新**](./docs/FBX_to_USD_Conversion_Strategy_Update.md)
  - 外部化轉換流程
  - Blender Python API 實作
  - 轉換驗證機制
  - [PDF 版本](./docs/FBX_to_USD_Conversion_Strategy_Update.pdf)

## 開發路線圖

### Phase 1: MVP (Minimum Viable Product)
- 核心 IADL/FDL 編輯和 3D 可視化
- In-Memory Event Bus + SQLite TSDB
- 手動 Blender 轉換腳本

### Phase 2: v1.1 - 自動化與整合
- FBX 轉換服務自動化
- DuckDB + Parquet TSDB
- 雙向事件同步

### Phase 3: v1.2 - 邁向生產
- ZMQ/MQTT Event Bus
- TDEngine/InfluxDB TSDB
- 事件重放機制
- AVEVA 整合

## 授權

本專案使用 LGPL 授權的 PySide6 作為 GUI 框架，以降低商業授權風險。

## 作者

Michael Lin 林志錚  
HTFA/Digital Twins Alliance

## 相關連結

- [IDTF V3.5 主專案](https://github.com/chchlin1018/IDTF-V3.5)

