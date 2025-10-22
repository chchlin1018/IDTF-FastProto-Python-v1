import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget, QMenuBar, QStatusBar, QFileDialog, QMessageBox
from PySide6.QtCore import Signal
from typing import Optional

from ...core.eventbus.interfaces import IEventBus
from ...core.eventbus.inmem import InMemoryEventBus
from ...core.tsdb.interfaces import ITSDB
from ...core.tsdb.sqlite_tsdb import SQLiteTSDB
from ...core.runtime.mapping_svc import MappingService

# Placeholder for NDH Control Panel widgets
class EventMonitorWidget(QWidget):
    def __init__(self, event_bus: IEventBus, parent=None):
        super().__init__(parent)
        self.event_bus = event_bus
        layout = QVBoxLayout(self)
        layout.addWidget(QMessageBox(QMessageBox.Information, "Event Monitor", "Event Monitor Placeholder", parent=self))
        self.setWindowTitle("Event Monitor")

class TSDBViewerWidget(QWidget):
    def __init__(self, tsdb: ITSDB, parent=None):
        super().__init__(parent)
        self.tsdb = tsdb
        layout = QVBoxLayout(self)
        layout.addWidget(QMessageBox(QMessageBox.Information, "TSDB Viewer", "TSDB Viewer Placeholder", parent=self))
        self.setWindowTitle("TSDB Viewer")

class TagMappingEditorWidget(QWidget):
    def __init__(self, mapping_service: MappingService, parent=None):
        super().__init__(parent)
        self.mapping_service = mapping_service
        layout = QVBoxLayout(self)
        layout.addWidget(QMessageBox(QMessageBox.Information, "Tag Mapping Editor", "Tag Mapping Editor Placeholder", parent=self))
        self.setWindowTitle("Tag Mapping Editor")


class NDHCpMainWindow(QMainWindow):
    file_opened = Signal(str)
    file_saved = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("NDH Control Panel")
        self.setGeometry(100, 100, 1200, 800)

        self.event_bus: IEventBus = InMemoryEventBus()
        self.tsdb: ITSDB = SQLiteTSDB("ndh_test.db") # Use a test DB for MVP
        self.mapping_service = MappingService(self.tsdb) # MappingService needs TSDB

        self._create_menu_bar()
        self._create_status_bar()
        self._create_central_widget()

        self.current_file: Optional[str] = None
        self.is_dirty: bool = False

    def _create_menu_bar(self) -> None:
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("&File")
        # open_action = file_menu.addAction("&Open...")
        # open_action.triggered.connect(self._open_file)
        # save_action = file_menu.addAction("&Save")
        # save_action.triggered.connect(self._save_file)
        # save_as_action = file_menu.addAction("Save &As...")
        # save_as_action.triggered.connect(self._save_file_as)
        file_menu.addSeparator()
        exit_action = file_menu.addAction("E&xit")
        exit_action.triggered.connect(self.close)

        # Add other menus as needed (e.g., View, Tools, Help)

    def _create_status_bar(self) -> None:
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def _create_central_widget(self) -> None:
        self.tab_widget = QTabWidget()
        self.setCentralWidget(self.tab_widget)

        self.event_monitor = EventMonitorWidget(self.event_bus)
        self.tsdb_viewer = TSDBViewerWidget(self.tsdb)
        self.tag_mapping_editor = TagMappingEditorWidget(self.mapping_service)

        self.tab_widget.addTab(self.event_monitor, "Event Monitor")
        self.tab_widget.addTab(self.tsdb_viewer, "TSDB Viewer")
        self.tab_widget.addTab(self.tag_mapping_editor, "Tag Mapping Editor")

    # def _open_file(self) -> None:
    #     file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*);;NDH Files (*.ndh)")
    #     if file_path:
    #         # Load NDH configuration or state
    #         self.statusBar.showMessage(f"Opened: {file_path}")
    #         self.current_file = file_path
    #         self.is_dirty = False
    #         self.file_opened.emit(file_path)

    # def _save_file(self) -> None:
    #     if self.current_file:
    #         # Save NDH configuration or state
    #         self.statusBar.showMessage(f"Saved: {self.current_file}")
    #         self.is_dirty = False
    #         self.file_saved.emit(self.current_file)
    #     else:
    #         self._save_file_as()

    # def _save_file_as(self) -> None:
    #     file_path, _ = QFileDialog.getSaveFileName(self, "Save File As", "", "All Files (*);;NDH Files (*.ndh)")
    #     if file_path:
    #         self.current_file = file_path
    #         self._save_file()

    def closeEvent(self, event) -> None:
        if self.is_dirty:
            reply = QMessageBox.question(self, "NDH Control Panel",
                                         "You have unsaved changes. Do you want to save them before exiting?",
                                         QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
            if reply == QMessageBox.Save:
                # self._save_file()
                event.accept()
            elif reply == QMessageBox.Cancel:
                event.ignore()
            else:
                event.accept()
        else:
            event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NDHCpMainWindow()
    window.show()
    sys.exit(app.exec())
