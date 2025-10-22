"""
NDH Control Panel - Main Window (Updated with Queue Manager)

This file contains the updated main window with Queue Manager integration.
To apply: mv main_window_updated.py main_window.py
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QMenuBar, QStatusBar, QFileDialog, QMessageBox,
    QPushButton, QGroupBox, QLabel, QTreeWidget, QTreeWidgetItem,
    QSplitter
)
from PySide6.QtCore import Signal, Qt, QTimer
from typing import Optional

from ...core.eventbus.interfaces import IEventBus
from ...core.eventbus.inmem import InMemoryEventBus
from ...core.tsdb.interfaces import ITSDB
from ...core.tsdb.sqlite_tsdb import SQLiteTSDB
from ...core.queue.interfaces import QueueManager
from ...core.queue.sqlite_queue import SQLiteQueueManager
from ...core.runtime.mapping_svc import MappingService
from ...core.runtime.ndh_service import NDHService

from .event_monitor import EventMonitorWidget
from .tsdb_viewer import TSDBViewerWidget
from .tag_mapping_editor import TagMappingEditorWidget
from .queue_monitor import QueueMonitorWidget
from .realtime_tag_monitor import RealtimeTagMonitorWidget
from .asset_library_tree_view import AssetLibraryTreeView


class ServantControlWidget(QWidget):
    """Servant 控制面板 - 顯示和控制 Asset/Tag Servants"""
    
    def __init__(self, ndh_service: NDHService, parent=None):
        super().__init__(parent)
        self.ndh_service = ndh_service
        self._init_ui()
        
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # FDL 載入區域
        fdl_group = QGroupBox("FDL Configuration")
        fdl_layout = QVBoxLayout()
        
        # FDL 和 IADL 路徑顯示
        path_layout = QHBoxLayout()
        self.fdl_label = QLabel("FDL: Not loaded")
        self.iadl_label = QLabel("IADL: Not loaded")
        path_layout.addWidget(self.fdl_label)
        path_layout.addWidget(self.iadl_label)
        fdl_layout.addLayout(path_layout)
        
        # 載入按鈕
        btn_layout = QHBoxLayout()
        self.load_iadl_btn = QPushButton("Load IADL Directory")
        self.load_iadl_btn.clicked.connect(self._load_iadl)
        btn_layout.addWidget(self.load_iadl_btn)
        
        self.load_fdl_btn = QPushButton("Load FDL File")
        self.load_fdl_btn.clicked.connect(self._load_fdl)
        btn_layout.addWidget(self.load_fdl_btn)
        
        self.generate_btn = QPushButton("Generate Servants")
        self.generate_btn.clicked.connect(self._generate_servants)
        self.generate_btn.setEnabled(False)
        btn_layout.addWidget(self.generate_btn)
        
        fdl_layout.addLayout(btn_layout)
        fdl_group.setLayout(fdl_layout)
        layout.addWidget(fdl_group)
        
        # Servant 控制區域
        control_group = QGroupBox("Servant Controls")
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start All Servants")
        self.start_btn.clicked.connect(self._start_servants)
        self.start_btn.setEnabled(False)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop All Servants")
        self.stop_btn.clicked.connect(self._stop_servants)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # 統計資訊
        stats_layout = QHBoxLayout()
        self.asset_count_label = QLabel("Asset Servants: 0")
        self.tag_count_label = QLabel("Tag Servants: 0")
        stats_layout.addWidget(self.asset_count_label)
        stats_layout.addWidget(self.tag_count_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # Servant 樹狀結構
        self.servant_tree = QTreeWidget()
        self.servant_tree.setHeaderLabels(["Name", "Type", "Status", "Value"])
        self.servant_tree.setColumnWidth(0, 200)
        self.servant_tree.setColumnWidth(1, 150)
        self.servant_tree.setColumnWidth(2, 100)
        layout.addWidget(self.servant_tree)
        
        # Auto-refresh timer for tag values
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._update_tag_values)
        self.refresh_timer.start(1000)  # Update every second
    
    def _load_iadl(self):
        """載入 IADL 目錄"""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Select IADL Directory",
            str(Path.home())
        )
        
        if dir_path:
            try:
                self.ndh_service.load_iadl_assets(dir_path)
                self.iadl_label.setText(f"IADL: {Path(dir_path).name}")
                self._check_ready_to_generate()
                QMessageBox.information(
                    self,
                    "Success",
                    f"Loaded {len(self.ndh_service.asset_library.assets)} IADL assets"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load IADL: {e}")
    
    def _load_fdl(self):
        """載入 FDL 檔案"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select FDL File",
            str(Path.home()),
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        
        if file_path:
            try:
                self.ndh_service.load_fdl_from_file(file_path)
                self.fdl_label.setText(f"FDL: {Path(file_path).name}")
                self._check_ready_to_generate()
                QMessageBox.information(
                    self,
                    "Success",
                    f"Loaded FDL: {self.ndh_service.fdl.site.name}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load FDL: {e}")
    
    def _check_ready_to_generate(self):
        """檢查是否可以生成 Servants"""
        if self.ndh_service.fdl and self.ndh_service.asset_library:
            self.generate_btn.setEnabled(True)
    
    def _generate_servants(self):
        """生成 Servants"""
        try:
            self.ndh_service.generate_servants()
            self._update_servant_tree()
            self._update_stats()
            self.start_btn.setEnabled(True)
            QMessageBox.information(
                self,
                "Success",
                f"Generated {len(self.ndh_service.asset_servants)} Asset Servants"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate servants: {e}")
    
    def _start_servants(self):
        """啟動所有 Servants"""
        try:
            self.ndh_service.start_all_servants()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self._update_servant_tree()
            QMessageBox.information(
                self,
                "Success",
                f"Started {len(self.ndh_service.asset_servants)} Asset Servants"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start servants: {e}")
    
    def _stop_servants(self):
        """停止所有 Servants"""
        try:
            self.ndh_service.stop_all_servants()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self._update_servant_tree()
            QMessageBox.information(
                self,
                "Success",
                f"Stopped {len(self.ndh_service.asset_servants)} Asset Servants"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to stop servants: {e}")
    
    def _update_servant_tree(self):
        """更新 Servant 樹狀結構"""
        self.servant_tree.clear()
        
        for asset_id, asset_servant in self.ndh_service.asset_servants.items():
            # Asset Servant 節點
            asset_item = QTreeWidgetItem([
                asset_servant.instance.instance_id,
                asset_servant.asset_definition.name,
                "Running" if asset_servant.is_running else "Stopped",
                ""
            ])
            self.servant_tree.addTopLevelItem(asset_item)
            
            # Tag Servant 子節點
            for tag_servant in asset_servant.get_all_tag_servants():
                tag_item = QTreeWidgetItem([
                    tag_servant.tag_definition.name,
                    f"Tag ({tag_servant.tag_definition.kind.value})",
                    "Running" if tag_servant.is_running else "Stopped",
                    str(tag_servant.get_value() or "N/A")
                ])
                asset_item.addChild(tag_item)
            
            asset_item.setExpanded(True)
    
    def _update_tag_values(self):
        """更新 Tag 值顯示"""
        if not self.ndh_service.is_running:
            return
        
        # 遍歷樹狀結構更新 Tag 值
        for i in range(self.servant_tree.topLevelItemCount()):
            asset_item = self.servant_tree.topLevelItem(i)
            asset_id = asset_item.text(0)
            
            if asset_id in self.ndh_service.asset_servants:
                asset_servant = self.ndh_service.asset_servants[asset_id]
                
                for j in range(asset_item.childCount()):
                    tag_item = asset_item.child(j)
                    tag_servants = asset_servant.get_all_tag_servants()
                    if j < len(tag_servants):
                        tag_servant = tag_servants[j]
                        value = tag_servant.get_value()
                        tag_item.setText(3, str(value) if value is not None else "N/A")
    
    def _update_stats(self):
        """更新統計資訊"""
        asset_count = len(self.ndh_service.asset_servants)
        tag_count = len(self.ndh_service.get_all_tag_servants())
        self.asset_count_label.setText(f"Asset Servants: {asset_count}")
        self.tag_count_label.setText(f"Tag Servants: {tag_count}")


class NDHControlPanelMainWindow(QMainWindow):
    """NDH Control Panel 主視窗"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NDH Control Panel - IDTF Fast Prototype v1")
        self.setGeometry(100, 100, 1400, 900)
        
        # 創建核心服務
        self.event_bus: IEventBus = InMemoryEventBus()
        self.tsdb: ITSDB = SQLiteTSDB("ndh_test.db")
        self.queue_manager: QueueManager = SQLiteQueueManager("ndh_queue.db")
        self.mapping_service = MappingService(self.tsdb)
        self.ndh_service = NDHService(
            event_bus=self.event_bus,
            tsdb=self.tsdb
        )
        
        self._create_menu_bar()
        self._create_status_bar()
        self._create_central_widget()
        
        self.current_file: Optional[str] = None
        self.is_dirty: bool = False
    
    def _create_menu_bar(self):
        """創建菜單欄"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self._show_about)
    
    def _create_status_bar(self):
        """創建狀態欄"""
        self.statusBar().showMessage("Ready")
    
    def _create_central_widget(self):
        """創建中央部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 使用分割器佈局
        splitter = QSplitter(Qt.Horizontal)
        
        # 左側：Servant 控制面板
        self.servant_control = ServantControlWidget(self.ndh_service)
        splitter.addWidget(self.servant_control)
        
        # 右側：功能分頁
        self.tab_widget = QTabWidget()
        
        # Event Monitor tab
        self.event_monitor = EventMonitorWidget(self.event_bus)
        self.tab_widget.addTab(self.event_monitor, "Event Monitor")
        
        # TSDB Viewer tab
        self.tsdb_viewer = TSDBViewerWidget(self.tsdb)
        self.tab_widget.addTab(self.tsdb_viewer, "TSDB Viewer")
        
        # Tag Mapping Editor tab
        self.tag_mapping_editor = TagMappingEditorWidget(self.mapping_service)
        self.tab_widget.addTab(self.tag_mapping_editor, "Tag Mapping Editor")
        
        # Queue Monitor tab
        self.queue_monitor = QueueMonitorWidget(self.queue_manager)
        self.tab_widget.addTab(self.queue_monitor, "Queue Monitor")
        
        # Realtime Tag Monitor tab
        self.realtime_tag_monitor = RealtimeTagMonitorWidget(self.ndh_service, self.tsdb)
        self.tab_widget.addTab(self.realtime_tag_monitor, "Realtime Tag Monitor")
        
        # Asset Library Tree View tab (NEW)
        self.asset_library_tree_view = AssetLibraryTreeView(self.ndh_service)
        self.tab_widget.addTab(self.asset_library_tree_view, "Asset Library")
        
        splitter.addWidget(self.tab_widget)
        
        # 設置分割器比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        # 設置中央部件佈局
        layout = QVBoxLayout(central_widget)
        layout.addWidget(splitter)
    
    def _show_about(self):
        """顯示關於對話框"""
        QMessageBox.about(
            self,
            "About NDH Control Panel",
            "<h3>NDH Control Panel</h3>"
            "<p>IDTF Fast Prototype Python v1</p>"
            "<p>Version: 1.0.0</p>"
            "<p>Author: 林志錚 (Chih Cheng Lin, Michael Lin)</p>"
            "<br>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Load FDL and IADL assets</li>"
            "<li>Generate and control Asset/Tag Servants</li>"
            "<li>Monitor events in real-time</li>"
            "<li>Query TSDB data</li>"
            "<li>Monitor message queues</li>"
            "<li>Edit tag mappings</li>"
            "</ul>"
        )
    
    def closeEvent(self, event):
        """處理關閉事件"""
        # 停止所有 Servants
        if self.ndh_service.is_running:
            self.ndh_service.stop_all_servants()
        
        event.accept()


def main():
    """主函數"""
    app = QApplication(sys.argv)
    window = NDHControlPanelMainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

