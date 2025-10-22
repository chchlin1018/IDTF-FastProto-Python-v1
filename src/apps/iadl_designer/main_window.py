"""
IADL Designer - Main Window
"""

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QMenuBar, QMenu, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QDockWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence

from ...core.iadl.models import Asset
from ...core.iadl.parser import parse_iadl_file, write_iadl_file
from ...core.iadl.validator import IADLValidator

from .asset_editor import AssetEditorWidget
from .tag_list import TagListWidget
from .properties_panel import PropertiesPanel


class IADLDesignerMainWindow(QMainWindow):
    """
    Main window for IADL Designer application.
    """
    
    asset_loaded = Signal(Asset)
    asset_saved = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        self.current_asset: Optional[Asset] = None
        self.current_file_path: Optional[Path] = None
        self.validator = IADLValidator()
        
        self._setup_ui()
        self._create_menus()
        self._create_toolbars()
        self._create_status_bar()
        self._connect_signals()
        
        self.setWindowTitle("IADL Designer")
        self.resize(1400, 900)
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Main splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.main_splitter)
        
        # Left panel: Asset Editor
        self.asset_editor = AssetEditorWidget()
        self.main_splitter.addWidget(self.asset_editor)
        
        # Right panel: Tag List and Properties
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tag_list = TagListWidget()
        self.properties_panel = PropertiesPanel()
        
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self.tag_list)
        right_splitter.addWidget(self.properties_panel)
        
        right_layout.addWidget(right_splitter)
        self.main_splitter.addWidget(right_widget)
        
        # Set splitter sizes
        self.main_splitter.setSizes([900, 500])
    
    def _create_menus(self):
        """Create application menus."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New", self)
        new_action.setShortcut(QKeySequence.New)
        new_action.triggered.connect(self.new_asset)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_asset)
        file_menu.addAction(open_action)
        
        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_asset)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_asset_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        validate_action = QAction("&Validate", self)
        validate_action.setShortcut(QKeySequence("Ctrl+V"))
        validate_action.triggered.connect(self.validate_asset)
        edit_menu.addAction(validate_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def _create_toolbars(self):
        """Create application toolbars."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Add toolbar actions
        new_action = QAction("New", self)
        new_action.triggered.connect(self.new_asset)
        toolbar.addAction(new_action)
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_asset)
        toolbar.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.triggered.connect(self.save_asset)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        validate_action = QAction("Validate", self)
        validate_action.triggered.connect(self.validate_asset)
        toolbar.addAction(validate_action)
    
    def _create_status_bar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def _connect_signals(self):
        """Connect internal signals."""
        self.asset_editor.asset_changed.connect(self._on_asset_changed)
        self.tag_list.tag_selected.connect(self.properties_panel.show_tag_properties)
    
    def new_asset(self):
        """Create a new asset."""
        # TODO: Implement new asset creation dialog
        self.status_bar.showMessage("New asset creation not yet implemented")
    
    def open_asset(self):
        """Open an existing asset file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open IADL Asset",
            "",
            "IADL Files (*.yaml *.yml *.json);;All Files (*)"
        )
        
        if file_path:
            self._load_asset(Path(file_path))
    
    def _load_asset(self, file_path: Path):
        """Load an asset from file."""
        try:
            asset = parse_iadl_file(file_path)
            self.current_asset = asset
            self.current_file_path = file_path
            
            # Update UI
            self.asset_editor.set_asset(asset)
            self.tag_list.set_tags(asset.tags)
            
            self.asset_loaded.emit(asset)
            self.status_bar.showMessage(f"Loaded: {file_path.name}")
            self.setWindowTitle(f"IADL Designer - {file_path.name}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Asset",
                f"Failed to load asset:\n{str(e)}"
            )
    
    def save_asset(self):
        """Save the current asset."""
        if self.current_file_path is None:
            self.save_asset_as()
        else:
            self._save_asset(self.current_file_path)
    
    def save_asset_as(self):
        """Save the current asset to a new file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save IADL Asset",
            "",
            "IADL YAML (*.yaml);;IADL JSON (*.json);;All Files (*)"
        )
        
        if file_path:
            self._save_asset(Path(file_path))
    
    def _save_asset(self, file_path: Path):
        """Save asset to file."""
        if self.current_asset is None:
            return
        
        try:
            # Get updated asset from editor
            asset = self.asset_editor.get_asset()
            
            # Validate before saving
            is_valid, errors = self.validator.validate(asset)
            if not is_valid:
                reply = QMessageBox.question(
                    self,
                    "Validation Errors",
                    f"Asset has validation errors:\n{chr(10).join(errors)}\n\nSave anyway?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.No:
                    return
            
            # Save to file
            write_iadl_file(asset, file_path)
            
            self.current_asset = asset
            self.current_file_path = file_path
            
            self.asset_saved.emit(str(file_path))
            self.status_bar.showMessage(f"Saved: {file_path.name}")
            self.setWindowTitle(f"IADL Designer - {file_path.name}")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Asset",
                f"Failed to save asset:\n{str(e)}"
            )
    
    def validate_asset(self):
        """Validate the current asset."""
        if self.current_asset is None:
            QMessageBox.information(self, "Validate", "No asset loaded")
            return
        
        asset = self.asset_editor.get_asset()
        is_valid, errors = self.validator.validate(asset)
        
        if is_valid:
            QMessageBox.information(
                self,
                "Validation Success",
                "Asset is valid!"
            )
        else:
            QMessageBox.warning(
                self,
                "Validation Errors",
                f"Asset has validation errors:\n\n{chr(10).join(errors)}"
            )
    
    def _on_asset_changed(self):
        """Handle asset changes."""
        # Mark as modified
        if self.current_file_path:
            self.setWindowTitle(f"IADL Designer - {self.current_file_path.name}*")
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About IADL Designer",
            "IADL Designer v1.0\n\n"
            "Industrial Asset Definition Language Designer\n"
            "Part of IDTF Fast Prototype Project"
        )
    
    def closeEvent(self, event):
        """Handle window close event."""
        # TODO: Check for unsaved changes
        event.accept()

