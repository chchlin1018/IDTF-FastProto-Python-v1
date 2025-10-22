"""
FDL Designer - Main Window
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QFileDialog, QMessageBox, QToolBar, QStatusBar
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from ...core.fdl.models import Site
from ...core.fdl.parser import parse_fdl_file, write_fdl_file
from ...core.fdl.validator import FDLValidator

from .instance_list import InstanceListWidget
from .layout_editor import LayoutEditorWidget


class FDLDesignerMainWindow(QMainWindow):
    """
    Main window for the FDL Designer application.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FDL Designer")
        self.resize(1200, 800)
        
        self.current_site: Optional[Site] = None
        self.current_file_path: Optional[str] = None
        
        self._setup_ui()
        self._create_actions()
        self._create_menus()
        self._create_toolbars()
        self._create_status_bar()
        
        self.update_ui_state()
    
    def _setup_ui(self):
        """Set up the main window's layout and widgets."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # Splitter for Instance List and Layout Editor
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.instance_list_widget = InstanceListWidget()
        self.layout_editor_widget = LayoutEditorWidget()
        
        self.splitter.addWidget(self.instance_list_widget)
        self.splitter.addWidget(self.layout_editor_widget)
        
        self.splitter.setStretchFactor(0, 1) # Instance List takes 1/4
        self.splitter.setStretchFactor(1, 3) # Layout Editor takes 3/4
        
        main_layout.addWidget(self.splitter)
        
        # Connect signals
        self.instance_list_widget.instance_selected.connect(self.layout_editor_widget.select_instance)
        self.instance_list_widget.instance_added.connect(self.layout_editor_widget.add_instance)
        self.instance_list_widget.instance_removed.connect(self.layout_editor_widget.remove_instance)
        self.instance_list_widget.instances_changed.connect(self.set_modified)
        
        self.layout_editor_widget.instance_transform_changed.connect(self.instance_list_widget.update_instance_transform)
        self.layout_editor_widget.layout_changed.connect(self.set_modified)

    def _create_actions(self):
        """Create actions for menus and toolbars."""
        # File actions
        self.new_action = QAction("&New Site", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.setStatusTip("Create a new FDL Site")
        self.new_action.triggered.connect(self.new_site)
        
        self.open_action = QAction("&Open Site...", self)
        self.open_action.setShortcut("Ctrl+O")
        self.open_action.setStatusTip("Open an existing FDL Site file")
        self.open_action.triggered.connect(self.open_site)
        
        self.save_action = QAction("&Save", self)
        self.save_action.setShortcut("Ctrl+S")
        self.save_action.setStatusTip("Save the current FDL Site")
        self.save_action.triggered.connect(self.save_site)
        
        self.save_as_action = QAction("Save &As...", self)
        self.save_as_action.setShortcut("Ctrl+Shift+S")
        self.save_as_action.setStatusTip("Save the current FDL Site to a new file")
        self.save_as_action.triggered.connect(self.save_site_as)
        
        self.exit_action = QAction("E&xit", self)
        self.exit_action.setShortcut("Ctrl+Q")
        self.exit_action.setStatusTip("Exit the application")
        self.exit_action.triggered.connect(self.close)
        
        # Edit actions
        self.validate_action = QAction("&Validate Site", self)
        self.validate_action.setShortcut("Ctrl+V")
        self.validate_action.setStatusTip("Validate the current FDL Site")
        self.validate_action.triggered.connect(self.validate_site)
        
        # View actions
        # self.show_usd_viewer_action = QAction("Show USD Viewer", self)
        # self.show_usd_viewer_action.setCheckable(True)
        # self.show_usd_viewer_action.setChecked(True)
        # self.show_usd_viewer_action.triggered.connect(self._toggle_usd_viewer)

    def _create_menus(self):
        """Create menu bar."""
        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu("&File")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.open_action)
        file_menu.addAction(self.save_action)
        file_menu.addAction(self.save_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)
        
        edit_menu = menu_bar.addMenu("&Edit")
        edit_menu.addAction(self.validate_action)
        
        view_menu = menu_bar.addMenu("&View")
        # view_menu.addAction(self.show_usd_viewer_action)
        
        help_menu = menu_bar.addMenu("&Help")
        help_menu.addAction(QAction("About", self))
        
    def _create_toolbars(self):
        """Create toolbars."""
        file_toolbar = self.addToolBar("File")
        file_toolbar.addAction(self.new_action)
        file_toolbar.addAction(self.open_action)
        file_toolbar.addAction(self.save_action)
        
        edit_toolbar = self.addToolBar("Edit")
        edit_toolbar.addAction(self.validate_action)
        
    def _create_status_bar(self):
        """Create status bar."""
        self.statusBar().showMessage("Ready")
    
    def new_site(self):
        """Create a new empty Site."""
        if self.isWindowModified() and not self._confirm_save():
            return
        
        self.current_site = Site(name="New Site", areas=[])
        self.current_file_path = None
        self.instance_list_widget.set_site(self.current_site)
        self.layout_editor_widget.set_site(self.current_site)
        self.setWindowModified(False)
        self.statusBar().showMessage("New site created.")
        self.update_ui_state()
    
    def open_site(self):
        """Open an existing FDL Site file."""
        if self.isWindowModified() and not self._confirm_save():
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open FDL Site",
            os.getcwd(),
            "FDL Site Files (*.yaml *.json);;All Files (*)"
        )
        
        if file_path:
            self._load_site(Path(file_path))
    
    def _load_site(self, file_path: Path):
        """Load FDL Site from file."""
        try:
            site = parse_fdl_file(file_path)
            self.current_site = site
            self.current_file_path = str(file_path)
            self.instance_list_widget.set_site(self.current_site)
            self.layout_editor_widget.set_site(self.current_site)
            self.setWindowModified(False)
            self.statusBar().showMessage(f"Loaded {file_path.name}")
            self.update_ui_state()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load FDL site: {e}")
            self.statusBar().showMessage("Load failed.")
    
    def save_site(self):
        """Save the current FDL Site."""
        if not self.current_site:
            QMessageBox.warning(self, "Save Site", "No site to save.")
            return
        
        if self.current_file_path:
            self._perform_save(Path(self.current_file_path))
        else:
            self.save_site_as()
    
    def save_site_as(self):
        """Save the current FDL Site to a new file."""
        if not self.current_site:
            QMessageBox.warning(self, "Save Site", "No site to save.")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save FDL Site As",
            os.getcwd(),
            "FDL Site Files (*.yaml *.json);;All Files (*)"
        )
        
        if file_path:
            self._perform_save(Path(file_path))
    
    def _perform_save(self, file_path: Path):
        """Perform the actual save operation."""
        try:
            write_fdl_file(self.current_site, file_path)
            self.current_file_path = str(file_path)
            self.setWindowModified(False)
            self.statusBar().showMessage(f"Saved {file_path.name}")
            self.update_ui_state()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save FDL site: {e}")
            self.statusBar().showMessage("Save failed.")
            
    def validate_site(self):
        """Validate the current FDL Site."""
        if not self.current_site:
            QMessageBox.warning(self, "Validate Site", "No site to validate.")
            return
        
        validator = FDLValidator()
        is_valid = validator.validate_site(self.current_site)
        
        if is_valid:
            QMessageBox.information(self, "Validation Result", "FDL Site is valid!")
            self.statusBar().showMessage("Validation successful.")
        else:
            error_messages = "\n".join([str(err) for err in validator.errors])
            QMessageBox.warning(self, "Validation Result", f"FDL Site has validation errors:\n{error_messages}")
            self.statusBar().showMessage("Validation failed.")

    def _confirm_save(self) -> bool:
        """Ask user to save changes before closing or opening new file."""
        reply = QMessageBox.warning(
            self,
            "FDL Designer",
            "The site has been modified.\nDo you want to save your changes?",
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Save:
            return self.save_site()
        elif reply == QMessageBox.Cancel:
            return False
        return True
    
    def closeEvent(self, event):
        """Handle close event to prompt for saving changes."""
        if self.isWindowModified():
            if not self._confirm_save():
                event.ignore()
                return
        event.accept()
        
    def set_modified(self):
        """Set window modified state."""
        self.setWindowModified(True)
        self.update_ui_state()
    
    def update_ui_state(self):
        """Update UI elements based on current application state."""
        has_site = self.current_site is not None
        self.save_action.setEnabled(has_site)
        self.save_as_action.setEnabled(has_site)
        self.validate_action.setEnabled(has_site)
        
        if self.current_file_path:
            self.setWindowTitle(f"FDL Designer - {os.path.basename(self.current_file_path)}[*]")
        else:
            self.setWindowTitle("FDL Designer - Untitled[*]")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FDLDesignerMainWindow()
    window.show()
    sys.exit(app.exec())
