# IDTF Fast Prototype GUI 應用程式實作指南

**版本**: 1.0  
**日期**: 2025-10-22  
**作者**: Michael Lin 林志錚

---

## 概述

本文件提供 IDTF Fast Prototype 三個 GUI 應用程式的完整實作指南：
1. **IADL Designer** - 工業資產定義語言設計器
2. **FDL Designer** - 工廠定義語言設計器
3. **NDH Control Panel** - 中性數據中樞控制面板

---

## 技術棧

- **GUI 框架**: PySide6 (Qt for Python, LGPL)
- **3D 視圖**: OpenUSD (pxr.Usd, pxr.UsdGeom)
- **數據視覺化**: matplotlib, pyqtgraph
- **核心服務**: 已實作的 Runtime 模組

---

## 1. IADL Designer

### 1.1 應用程式架構

```
iadl_designer/
├── main.py                  # 應用程式入口
├── main_window.py           # 主窗口 (已實作)
├── asset_editor.py          # 資產編輯器
├── tag_list.py              # Tag 列表視圖
├── tag_editor.py            # Tag 編輯器
├── properties_panel.py      # 屬性面板
├── usd_viewer.py            # USD 3D 視圖
└── dialogs/
    ├── new_asset_dialog.py  # 新建資產對話框
    └── tag_dialog.py        # Tag 編輯對話框
```

### 1.2 核心組件設計

#### AssetEditorWidget

**職責**: 編輯 Asset 的基本資訊（name, model_ref, units, default_xform, metadata）

**關鍵功能**:
```python
class AssetEditorWidget(QWidget):
    asset_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self.asset: Optional[Asset] = None
        self._setup_ui()
    
    def _setup_ui(self):
        """
        創建表單佈局：
        - QLineEdit for name
        - QLineEdit for model_ref (with browse button)
        - QComboBox for units.length
        - Transform editor (translation, rotation, scale)
        - Metadata editor (author, version, created_at)
        """
        pass
    
    def set_asset(self, asset: Asset):
        """Load asset data into form fields"""
        self.asset = asset
        # Update all form fields
    
    def get_asset(self) -> Asset:
        """Collect data from form fields and return Asset"""
        # Read all form fields and construct Asset
        return self.asset
```

**實作要點**:
- 使用 QFormLayout 組織表單
- Transform 編輯器使用 3 個 QDoubleSpinBox 分別編輯 x, y, z
- 連接所有輸入控件的 `textChanged`/`valueChanged` 信號到 `asset_changed`

---

#### TagListWidget

**職責**: 顯示和管理 Asset 的 Tags 列表

**關鍵功能**:
```python
class TagListWidget(QWidget):
    tag_selected = Signal(Tag)
    tag_added = Signal(Tag)
    tag_removed = Signal(str)  # tag_id
    
    def __init__(self):
        super().__init__()
        self.tags: List[Tag] = []
        self._setup_ui()
    
    def _setup_ui(self):
        """
        創建佈局：
        - QListWidget for tag list
        - Toolbar with Add/Remove/Edit buttons
        """
        pass
    
    def set_tags(self, tags: List[Tag]):
        """Load tags into list"""
        self.tags = tags
        self._update_list()
    
    def _update_list(self):
        """Refresh QListWidget"""
        pass
    
    def add_tag(self):
        """Show TagDialog to create new tag"""
        pass
    
    def remove_tag(self):
        """Remove selected tag"""
        pass
    
    def edit_tag(self):
        """Show TagDialog to edit selected tag"""
        pass
```

**實作要點**:
- 使用 QListWidget 顯示 Tag 列表
- 每個列表項顯示 Tag 名稱和類型
- 雙擊列表項打開編輯對話框

---

#### USDViewerWidget

**職責**: 顯示 USD 模型的 3D 視圖

**關鍵功能**:
```python
class USDViewerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.stage: Optional[Usd.Stage] = None
        self._setup_ui()
    
    def load_usd(self, usd_path: str):
        """Load USD file and display"""
        from pxr import Usd, UsdGeom
        self.stage = Usd.Stage.Open(usd_path)
        self._render_stage()
    
    def _render_stage(self):
        """Render USD stage (simplified, use USD imaging)"""
        # For MVP: Show stage hierarchy in tree view
        # For production: Integrate USD Hydra renderer
        pass
```

**實作要點**:
- MVP 階段：使用 QTreeWidget 顯示 USD 層次結構
- 生產階段：整合 USD Hydra 渲染器（需要 OpenGL 支援）
- 或使用 USD View 作為外部查看器

---

### 1.3 對話框設計

#### TagDialog

**職責**: 創建或編輯 Tag

**關鍵功能**:
```python
class TagDialog(QDialog):
    def __init__(self, tag: Optional[Tag] = None, parent=None):
        super().__init__(parent)
        self.tag = tag
        self._setup_ui()
        if tag:
            self._load_tag(tag)
    
    def _setup_ui(self):
        """
        創建表單：
        - Name (QLineEdit)
        - Kind (QComboBox: analog, digital, string)
        - EU Unit (QLineEdit)
        - Attachment Strategy (QRadioButton: by-pos / by-prim)
        - Local Position (3 x QDoubleSpinBox) or Attach Prim Path (QLineEdit)
        - OK/Cancel buttons
        """
        pass
    
    def get_tag(self) -> Tag:
        """Collect form data and return Tag"""
        pass
```

---

## 2. FDL Designer

### 2.1 應用程式架構

```
fdl_designer/
├── main.py                    # 應用程式入口
├── main_window.py             # 主窗口
├── layout_editor.py           # 佈局編輯器
├── instance_list.py           # 實例列表視圖
├── batch_layout_dialog.py     # 批量佈局生成對話框
├── collision_viewer.py        # 碰撞檢測視覺化
├── usd_3d_view.py             # USD 3D 視圖（整合場景）
└── dialogs/
    ├── new_fdl_dialog.py      # 新建 FDL 對話框
    ├── add_instance_dialog.py # 添加實例對話框
    └── area_dialog.py         # 區域編輯對話框
```

### 2.2 核心組件設計

#### LayoutEditorWidget

**職責**: 編輯 FDL 佈局（Site, Areas, Instances）

**關鍵功能**:
```python
class LayoutEditorWidget(QWidget):
    fdl_changed = Signal()
    
    def __init__(self):
        super().__init__()
        self.fdl: Optional[FDL] = None
        self.layout_service = LayoutService()
        self._setup_ui()
    
    def _setup_ui(self):
        """
        創建佈局：
        - Site info panel (name, site_id, units)
        - Area tree view (QTreeWidget)
        - Instance list for selected area
        - Toolbar (Add Area, Add Instance, Batch Layout, Detect Collisions)
        """
        pass
    
    def set_fdl(self, fdl: FDL):
        """Load FDL into editor"""
        self.fdl = fdl
        self.layout_service.fdl = fdl
        self._update_tree()
    
    def add_area(self):
        """Show AreaDialog to create new area"""
        pass
    
    def add_instance(self):
        """Show AddInstanceDialog to add instance to selected area"""
        pass
    
    def generate_batch_layout(self):
        """Show BatchLayoutDialog to generate instances"""
        pass
    
    def detect_collisions(self):
        """Run collision detection and show results"""
        # Use layout_service.detect_collisions()
        # Show results in CollisionViewerWidget
        pass
```

---

#### BatchLayoutDialog

**職責**: 配置並生成批量佈局

**關鍵功能**:
```python
class BatchLayoutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """
        創建表單：
        - Pattern type (QComboBox: grid, line, circle)
        - Asset reference (QComboBox from AssetLibraryService)
        - Count (QSpinBox)
        - Spacing (QDoubleSpinBox)
        - Start position (3 x QDoubleSpinBox)
        - Pattern-specific parameters (dynamic based on pattern type)
        - Preview button
        - OK/Cancel buttons
        """
        pass
    
    def get_batch_layout(self) -> BatchLayout:
        """Collect form data and return BatchLayout"""
        pass
    
    def preview_layout(self):
        """Show preview of generated instances"""
        # Use generate_batch_instances() to preview
        pass
```

---

#### CollisionViewerWidget

**職責**: 視覺化碰撞檢測結果

**關鍵功能**:
```python
class CollisionViewerWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def show_collisions(self, collisions: List[Tuple[str, str]]):
        """
        Display collision pairs:
        - QTableWidget with columns: Instance 1, Instance 2, Action
        - Highlight colliding instances in 3D view
        """
        pass
```

---

### 2.3 3D 視圖整合

#### USD3DViewWidget

**職責**: 顯示整個工廠佈局的 3D 視圖

**關鍵功能**:
```python
class USD3DViewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.stage: Optional[Usd.Stage] = None
        self._setup_ui()
    
    def load_fdl(self, fdl: FDL):
        """
        Load FDL and compose USD stage:
        1. Create stage
        2. For each instance, add USD reference
        3. Apply transforms
        4. Render stage
        """
        from ...core.usdkit.io import create_stage, add_reference
        from ...core.usdkit.xform import set_prim_transform
        
        self.stage = create_stage()
        
        for area in fdl.site.areas:
            for instance in area.instances:
                # Add reference and set transform
                prim_path = f"/World/{instance.instance_id}"
                # ... (use usdkit functions)
        
        self._render_stage()
    
    def highlight_instances(self, instance_ids: List[str]):
        """Highlight specific instances (e.g., colliding instances)"""
        pass
```

---

## 3. NDH Control Panel

### 3.1 應用程式架構

```
ndh_cp/
├── main.py                  # 應用程式入口
├── main_window.py           # 主窗口
├── event_monitor.py         # Event Bus 監控
├── tsdb_viewer.py           # TSDB 數據視覺化
├── tag_mapping_editor.py    # Tag 映射編輯器
├── data_source_config.py    # 外部數據源配置
└── widgets/
    ├── event_list.py        # 事件列表
    ├── tag_chart.py         # Tag 數據圖表
    └── mapping_table.py     # 映射表格
```

### 3.2 核心組件設計

#### EventMonitorWidget

**職責**: 監控和顯示 Event Bus 事件

**關鍵功能**:
```python
class EventMonitorWidget(QWidget):
    def __init__(self, event_bus: IEventBus):
        super().__init__()
        self.event_bus = event_bus
        self._setup_ui()
        self._subscribe_to_events()
    
    def _setup_ui(self):
        """
        創建佈局：
        - Event filter (QComboBox for event types)
        - Event list (QTableWidget: timestamp, type, source, payload)
        - Event details panel
        - Clear/Pause buttons
        """
        pass
    
    def _subscribe_to_events(self):
        """Subscribe to all event types"""
        def on_event(event: Event):
            self._add_event_to_list(event)
        
        self.event_bus.subscribe("*", on_event)
    
    def _add_event_to_list(self, event: Event):
        """Add event to table"""
        pass
```

---

#### TSDBViewerWidget

**職責**: 視覺化 TSDB 時間序列數據

**關鍵功能**:
```python
class TSDBViewerWidget(QWidget):
    def __init__(self, tsdb: ITSDB):
        super().__init__()
        self.tsdb = tsdb
        self._setup_ui()
    
    def _setup_ui(self):
        """
        創建佈局：
        - Tag selector (QComboBox)
        - Time range selector (QDateTimeEdit x 2)
        - Chart (matplotlib or pyqtgraph)
        - Aggregation options (QComboBox)
        - Refresh button
        """
        pass
    
    def plot_tag_values(self, tag_id: str, start_time: datetime, end_time: datetime):
        """Query TSDB and plot values"""
        values = self.tsdb.query_tag_values(tag_id, start_time, end_time)
        
        # Plot using matplotlib
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        
        fig, ax = plt.subplots()
        timestamps = [v.timestamp for v in values]
        data = [v.value for v in values]
        ax.plot(timestamps, data)
        ax.set_xlabel('Time')
        ax.set_ylabel('Value')
        ax.set_title(f'Tag: {tag_id}')
        
        # Embed in Qt widget
        canvas = FigureCanvasQTAgg(fig)
        # Add canvas to layout
```

---

#### TagMappingEditorWidget

**職責**: 編輯 Tag 實例與外部數據源的映射

**關鍵功能**:
```python
class TagMappingEditorWidget(QWidget):
    def __init__(self, mapping_service: MappingService):
        super().__init__()
        self.mapping_service = mapping_service
        self._setup_ui()
    
    def _setup_ui(self):
        """
        創建佈局：
        - Mapping table (QTableWidget: Tag Instance, External Source, External Tag Name, Read Only, Polling Interval)
        - Add/Remove/Edit buttons
        - Import/Export buttons (CSV)
        """
        pass
    
    def add_mapping(self):
        """Show dialog to create new mapping"""
        pass
    
    def import_mappings_from_csv(self):
        """Import mappings from CSV file"""
        from ...core.io.csv_utils import read_csv_as_dicts
        # Read CSV and create TagMapping objects
        pass
    
    def export_mappings_to_csv(self):
        """Export mappings to CSV file"""
        from ...core.io.csv_utils import write_csv_from_dicts
        # Convert TagMapping objects to dicts and write CSV
        pass
```

---

## 4. 共用組件

### 4.1 Transform Editor Widget

**職責**: 編輯 Transform (translation, rotation, scale)

```python
class TransformEditorWidget(QWidget):
    transform_changed = Signal(Transform)
    
    def __init__(self):
        super().__init__()
        self._setup_ui()
    
    def _setup_ui(self):
        """
        創建佈局：
        - Translation: 3 x QDoubleSpinBox (X, Y, Z)
        - Rotation: 3 x QDoubleSpinBox (X, Y, Z) in degrees
        - Scale: 3 x QDoubleSpinBox (X, Y, Z)
        - Lock uniform scale checkbox
        """
        pass
    
    def set_transform(self, transform: Transform):
        """Load transform into spin boxes"""
        pass
    
    def get_transform(self) -> Transform:
        """Collect values and return Transform"""
        pass
```

---

## 5. 實作優先級

### P0 (MVP - 1-2 週)

**IADL Designer**:
- ✅ Main window (已實作)
- AssetEditorWidget (基本表單)
- TagListWidget (列表 + Add/Remove)
- TagDialog (基本 Tag 編輯)

**FDL Designer**:
- Main window
- LayoutEditorWidget (Site + Area 樹狀視圖)
- Instance list
- AddInstanceDialog

**NDH Control Panel**:
- Main window
- EventMonitorWidget (基本事件列表)
- TagMappingEditorWidget (映射表格)

### P1 (功能完善 - 1 個月)

**IADL Designer**:
- USDViewerWidget (USD 層次結構視圖)
- PropertiesPanel (詳細屬性編輯)
- Tag 附著策略視覺化

**FDL Designer**:
- BatchLayoutDialog (批量佈局生成)
- CollisionViewerWidget (碰撞檢測結果)
- USD3DViewWidget (簡化 3D 視圖)

**NDH Control Panel**:
- TSDBViewerWidget (基本圖表)
- 數據源配置界面

### P2 (高級功能 - 3 個月)

**IADL Designer**:
- 完整的 USD 3D 渲染（Hydra）
- Tag 世界位置視覺化
- 資產庫瀏覽器

**FDL Designer**:
- 完整的 USD 3D 渲染（Hydra）
- 實時碰撞檢測
- 連接編輯器（管道、電纜）

**NDH Control Panel**:
- 實時數據更新
- 高級圖表（多 Tag、聚合）
- 警報管理

---

## 6. 測試策略

### 6.1 單元測試

使用 pytest 和 pytest-qt 測試 GUI 組件：

```python
def test_asset_editor_widget(qtbot):
    from src.apps.iadl_designer.asset_editor import AssetEditorWidget
    
    widget = AssetEditorWidget()
    qtbot.addWidget(widget)
    
    # Test set_asset
    asset = create_test_asset()
    widget.set_asset(asset)
    
    # Test get_asset
    retrieved_asset = widget.get_asset()
    assert retrieved_asset.name == asset.name
```

### 6.2 整合測試

測試完整的工作流程：

```python
def test_iadl_designer_workflow(qtbot):
    from src.apps.iadl_designer.main_window import IADLDesignerMainWindow
    
    window = IADLDesignerMainWindow()
    qtbot.addWidget(window)
    
    # Load asset
    window._load_asset(Path("testfiles/IADL/chiller.yaml"))
    
    # Modify asset
    # ...
    
    # Save asset
    window._save_asset(Path("/tmp/test_output.yaml"))
    
    # Verify saved file
    assert Path("/tmp/test_output.yaml").exists()
```

---

## 7. 部署

### 7.1 打包

使用 PyInstaller 打包應用程式：

```bash
# IADL Designer
pyinstaller --name="IADL Designer" \
            --windowed \
            --icon=assets/iadl_icon.ico \
            src/apps/iadl_designer/main.py

# FDL Designer
pyinstaller --name="FDL Designer" \
            --windowed \
            --icon=assets/fdl_icon.ico \
            src/apps/fdl_designer/main.py

# NDH Control Panel
pyinstaller --name="NDH Control Panel" \
            --windowed \
            --icon=assets/ndh_icon.ico \
            src/apps/ndh_cp/main.py
```

### 7.2 依賴處理

確保 PyInstaller spec 文件包含所有依賴：

```python
# iadl_designer.spec
a = Analysis(
    ['src/apps/iadl_designer/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src/core', 'core'),
        ('testfiles', 'testfiles'),
    ],
    hiddenimports=[
        'PySide6',
        'pxr',
        'yaml',
        'jsonschema',
    ],
    ...
)
```

---

## 8. 下一步行動

### 短期（本週）

1. 完成 IADL Designer 的 AssetEditorWidget
2. 完成 TagListWidget 和 TagDialog
3. 測試基本的 IADL 編輯工作流程

### 中期（本月）

1. 完成 FDL Designer 的 LayoutEditorWidget
2. 實作批量佈局生成功能
3. 完成 NDH Control Panel 的 EventMonitorWidget

### 長期（3 個月）

1. 整合 USD 3D 渲染
2. 實作實時數據更新
3. 完成所有高級功能

---

## 附錄：關鍵代碼範例

### A. PySide6 基本模板

```python
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton
from PySide6.QtCore import Qt
import sys

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")
        
        button = QPushButton("Click Me")
        button.clicked.connect(self.on_button_clicked)
        self.setCentralWidget(button)
    
    def on_button_clicked(self):
        print("Button clicked!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec())
```

### B. USD 視圖範例

```python
from pxr import Usd, UsdGeom
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem

class USDHierarchyWidget(QTreeWidget):
    def load_stage(self, stage: Usd.Stage):
        self.clear()
        
        def add_prim_to_tree(prim, parent_item):
            item = QTreeWidgetItem(parent_item, [prim.GetName(), prim.GetTypeName()])
            for child in prim.GetChildren():
                add_prim_to_tree(child, item)
        
        root_prim = stage.GetPseudoRoot()
        for child in root_prim.GetChildren():
            add_prim_to_tree(child, self)
```

---

**文件結束**

