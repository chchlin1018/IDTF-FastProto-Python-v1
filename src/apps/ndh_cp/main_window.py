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
from ...core.runtime.mapping_svc import MappingService
from ...core.runtime.ndh_service import NDHService

from .event_monitor import EventMonitorWidget
from .tsdb_viewer import TSDBViewerWidget
from .tag_mapping_editor import TagMappingEditorWidget


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
        self.load_fdl_btn = QPushButton("Load FDL File")
        self.load_fdl_btn.clicked.connect(self._load_fdl)
        self.generate_btn = QPushButton("Generate Servants")
        self.generate_btn.clicked.connect(self._generate_servants)
        self.generate_btn.setEnabled(False)
        
        btn_layout.addWidget(self.load_iadl_btn)
        btn_layout.addWidget(self.load_fdl_btn)
        btn_layout.addWidget(self.generate_btn)
        fdl_layout.addLayout(btn_layout)
        
        fdl_group.setLayout(fdl_layout)
        layout.addWidget(fdl_group)
        
        # Servant 控制區域
        control_group = QGroupBox("Servant Control")
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start All Servants")
        self.start_btn.clicked.connect(self._start_servants)
        self.start_btn.setEnabled(False)
        
        self.stop_btn = QPushButton("Stop All Servants")
        self.stop_btn.clicked.connect(self._stop_servants)
        self.stop_btn.setEnabled(False)
        
        self.status_label = QLabel("Status: Idle")
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.stop_btn)
        control_layout.addStretch()
        control_layout.addWidget(self.status_label)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Servant 列表顯示
        list_group = QGroupBox("Servants")
        list_layout = QVBoxLayout()
        
        self.servant_tree = QTreeWidget()
        self.servant_tree.setHeaderLabels(["Type", "ID", "Name", "Status", "Value"])
        self.servant_tree.setColumnWidth(0, 100)
        self.servant_tree.setColumnWidth(1, 200)
        self.servant_tree.setColumnWidth(2, 200)
        
        list_layout.addWidget(self.servant_tree)
        list_group.setLayout(list_layout)
        layout.addWidget(list_group)
        
        # 統計資訊
        stats_layout = QHBoxLayout()
        self.asset_count_label = QLabel("Asset Servants: 0")
        self.tag_count_label = QLabel("Tag Servants: 0")
        stats_layout.addWidget(self.asset_count_label)
        stats_layout.addWidget(self.tag_count_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # 定時更新 Tag 值顯示
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_tag_values)
        
        self.iadl_loaded = False
        self.fdl_loaded = False
        
    def _load_iadl(self):
        """載入 IADL 目錄"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select IADL Directory", 
            str(Path.home())
        )
        if dir_path:
            try:
                self.ndh_service.load_iadl_assets(dir_path)
                self.iadl_label.setText(f"IADL: {Path(dir_path).name}")
                self.iadl_loaded = True
                self._check_ready_to_generate()
                QMessageBox.information(self, "Success", 
                    f"Loaded IADL assets from {dir_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                    f"Failed to load IADL assets: {str(e)}")
    
    def _load_fdl(self):
        """載入 FDL 檔案"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open FDL File", 
            str(Path.home()),
            "FDL Files (*.yaml *.yml *.json);;All Files (*)"
        )
        if file_path:
            try:
                self.ndh_service.load_fdl_from_file(file_path)
                self.fdl_label.setText(f"FDL: {Path(file_path).name}")
                self.fdl_loaded = True
                self._check_ready_to_generate()
                QMessageBox.information(self, "Success", 
                    f"Loaded FDL from {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", 
                    f"Failed to load FDL: {str(e)}")
    
    def _check_ready_to_generate(self):
        """檢查是否可以生成 Servants"""
        if self.iadl_loaded and self.fdl_loaded:
            self.generate_btn.setEnabled(True)
    
    def _generate_servants(self):
        """生成 Asset Servants 和 Tag Servants"""
        try:
            self.ndh_service.generate_servants()
            self._update_servant_tree()
            self.start_btn.setEnabled(True)
            self.status_label.setText("Status: Servants Generated")
            QMessageBox.information(self, "Success", 
                f"Generated {len(self.ndh_service.asset_servants)} Asset Servants")
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                f"Failed to generate servants: {str(e)}")
    
    def _start_servants(self):
        """啟動所有 Servants"""
        try:
            self.ndh_service.start_all_servants()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.status_label.setText("Status: Running")
            self.update_timer.start(1000)  # 每秒更新一次
            QMessageBox.information(self, "Success", "All servants started")
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                f"Failed to start servants: {str(e)}")
    
    def _stop_servants(self):
        """停止所有 Servants"""
        try:
            self.ndh_service.stop_all_servants()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_label.setText("Status: Stopped")
            self.update_timer.stop()
            QMessageBox.information(self, "Success", "All servants stopped")
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                f"Failed to stop servants: {str(e)}")
    
    def _update_servant_tree(self):
        """更新 Servant 樹狀顯示"""
        self.servant_tree.clear()
        
        asset_count = 0
        tag_count = 0
        
        for asset_servant in self.ndh_service.get_all_asset_servants():
            # 創建 Asset Servant 節點
            asset_item = QTreeWidgetItem([
                "Asset",
                asset_servant.instance.instance_id,
                asset_servant.asset_definition.name,
                "Running" if asset_servant.is_running else "Stopped",
                ""
            ])
            self.servant_tree.addTopLevelItem(asset_item)
            asset_count += 1
            
            # 添加 Tag Servant 子節點
            for tag_servant in asset_servant.get_all_tag_servants():
                tag_item = QTreeWidgetItem([
                    "Tag",
                    tag_servant.tag_instance_id,
                    tag_servant.tag_definition.name,
                    "Running" if tag_servant.is_running else "Stopped",
                    str(tag_servant.current_value) if tag_servant.current_value is not None else "N/A"
                ])
                asset_item.addChild(tag_item)
                tag_count += 1
        
        self.servant_tree.expandAll()
        
        self.asset_count_label.setText(f"Asset Servants: {asset_count}")
        self.tag_count_label.setText(f"Tag Servants: {tag_count}")
    
    def _update_tag_values(self):
        """更新 Tag 值顯示"""
        # 遍歷樹狀結構，更新 Tag 值
        for i in range(self.servant_tree.topLevelItemCount()):
            asset_item = self.servant_tree.topLevelItem(i)
            for j in range(asset_item.childCount()):
                tag_item = asset_item.child(j)
                tag_instance_id = tag_item.text(1)
                
                # 從 NDH Service 獲取對應的 Tag Servant
                for asset_servant in self.ndh_service.get_all_asset_servants():
                    for tag_servant in asset_servant.get_all_tag_servants():
                        if tag_servant.tag_instance_id == tag_instance_id:
                            value_str = str(tag_servant.current_value) if tag_servant.current_value is not None else "N/A"
                            tag_item.setText(4, value_str)
                            break


class NDHCpMainWindow(QMainWindow):
    file_opened = Signal(str)
    file_saved = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("NDH Control Panel - IDTF Fast Prototype v1")
        self.setGeometry(100, 100, 1400, 900)

        # 創建核心服務
        self.event_bus: IEventBus = InMemoryEventBus()
        self.tsdb: ITSDB = SQLiteTSDB("ndh_test.db")
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

    def _create_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)

        # View Menu
        view_menu = menu_bar.addMenu("&View")
        refresh_action = view_menu.addAction("&Refresh")
        refresh_action.triggered.connect(self._refresh_views)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = help_menu.addAction("&About")
        about_action.triggered.connect(self._show_about)

    def _create_status_bar(self) -> None:
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def _create_central_widget(self) -> None:
        # 創建主分割器
        main_splitter = QSplitter(Qt.Horizontal)
        
        # 左側：Servant 控制面板
        self.servant_control = ServantControlWidget(self.ndh_service)
        main_splitter.addWidget(self.servant_control)
        
        # 右側：Tab Widget
        self.tab_widget = QTabWidget()
        
        self.event_monitor = EventMonitorWidget(self.event_bus)
        self.tsdb_viewer = TSDBViewerWidget(self.tsdb)
        self.tag_mapping_editor = TagMappingEditorWidget(self.mapping_service)

        self.tab_widget.addTab(self.event_monitor, "Event Monitor")
        self.tab_widget.addTab(self.tsdb_viewer, "TSDB Viewer")
        self.tab_widget.addTab(self.tag_mapping_editor, "Tag Mapping Editor")
        
        main_splitter.addWidget(self.tab_widget)
        
        # 設置分割比例
        main_splitter.setSizes([500, 900])
        
        self.setCentralWidget(main_splitter)

    def _refresh_views(self) -> None:
        """刷新所有視圖"""
        self.servant_control._update_servant_tree()
        self.statusBar.showMessage("Views refreshed", 2000)

    def _show_about(self) -> None:
        """顯示關於對話框"""
        QMessageBox.about(self, "About NDH Control Panel",
            "<h3>NDH Control Panel</h3>"
            "<p>IDTF Fast Prototype Python v1</p>"
            "<p>Neutral Data Hub Control Panel for managing Asset Servants and Tag Servants</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Load FDL and IADL files</li>"
            "<li>Generate and manage Asset/Tag Servants</li>"
            "<li>Monitor events in real-time</li>"
            "<li>Query TSDB data</li>"
            "<li>Edit tag mappings</li>"
            "</ul>"
            "<p>Author: 林志錚 (Chih Cheng Lin, Michael Lin)</p>"
        )

    def closeEvent(self, event) -> None:
        # 停止所有 Servants
        if self.ndh_service.is_running:
            reply = QMessageBox.question(self, "NDH Control Panel",
                "Servants are still running. Stop them before exiting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            
            if reply == QMessageBox.Yes:
                self.ndh_service.stop_all_servants()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NDHCpMainWindow()
    window.show()
    sys.exit(app.exec())

