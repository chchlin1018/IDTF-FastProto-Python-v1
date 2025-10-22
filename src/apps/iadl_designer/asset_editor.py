"""
IADL Designer - Asset Editor Widget
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QFileDialog, QGroupBox, QDoubleSpinBox, QHBoxLayout
)
from PySide6.QtCore import Signal

from ...core.iadl.models import Asset, Transform, Units, Metadata
from ...core.tags.id_generator import generate_asset_id
from datetime import datetime


class TransformEditorWidget(QWidget):
    """Widget for editing Transform (translation, rotation, scale)."""
    
    transform_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QFormLayout(self)
        
        # Translation
        self.trans_x = QDoubleSpinBox()
        self.trans_y = QDoubleSpinBox()
        self.trans_z = QDoubleSpinBox()
        
        for spin in [self.trans_x, self.trans_y, self.trans_z]:
            spin.setRange(-10000, 10000)
            spin.setDecimals(3)
            spin.valueChanged.connect(self.transform_changed.emit)
        
        trans_layout = QHBoxLayout()
        trans_layout.addWidget(self.trans_x)
        trans_layout.addWidget(self.trans_y)
        trans_layout.addWidget(self.trans_z)
        layout.addRow("Translation (X, Y, Z):", trans_layout)
        
        # Rotation
        self.rot_x = QDoubleSpinBox()
        self.rot_y = QDoubleSpinBox()
        self.rot_z = QDoubleSpinBox()
        
        for spin in [self.rot_x, self.rot_y, self.rot_z]:
            spin.setRange(-360, 360)
            spin.setDecimals(2)
            spin.valueChanged.connect(self.transform_changed.emit)
        
        rot_layout = QHBoxLayout()
        rot_layout.addWidget(self.rot_x)
        rot_layout.addWidget(self.rot_y)
        rot_layout.addWidget(self.rot_z)
        layout.addRow("Rotation (X, Y, Z):", rot_layout)
        
        # Scale
        self.scale_x = QDoubleSpinBox()
        self.scale_y = QDoubleSpinBox()
        self.scale_z = QDoubleSpinBox()
        
        for spin in [self.scale_x, self.scale_y, self.scale_z]:
            spin.setRange(0.1, 10.0)
            spin.setValue(1.0)
            spin.setDecimals(3)
            spin.valueChanged.connect(self.transform_changed.emit)
        
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(self.scale_x)
        scale_layout.addWidget(self.scale_y)
        scale_layout.addWidget(self.scale_z)
        layout.addRow("Scale (X, Y, Z):", scale_layout)
    
    def set_transform(self, transform: Transform):
        """Load transform into spin boxes."""
        self.trans_x.setValue(transform.translation[0])
        self.trans_y.setValue(transform.translation[1])
        self.trans_z.setValue(transform.translation[2])
        
        self.rot_x.setValue(transform.rotation[0])
        self.rot_y.setValue(transform.rotation[1])
        self.rot_z.setValue(transform.rotation[2])
        
        self.scale_x.setValue(transform.scale[0])
        self.scale_y.setValue(transform.scale[1])
        self.scale_z.setValue(transform.scale[2])
    
    def get_transform(self) -> Transform:
        """Collect values and return Transform."""
        return Transform(
            translation=[self.trans_x.value(), self.trans_y.value(), self.trans_z.value()],
            rotation=[self.rot_x.value(), self.rot_y.value(), self.rot_z.value()],
            scale=[self.scale_x.value(), self.scale_y.value(), self.scale_z.value()]
        )


class AssetEditorWidget(QWidget):
    """Widget for editing Asset basic information."""
    
    asset_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.asset: Optional[Asset] = None
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Basic Info Group
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout(basic_group)
        
        # Asset ID (read-only)
        self.asset_id_edit = QLineEdit()
        self.asset_id_edit.setReadOnly(True)
        basic_layout.addRow("Asset ID:", self.asset_id_edit)
        
        # Name
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.asset_changed.emit)
        basic_layout.addRow("Name:", self.name_edit)
        
        # Model Reference
        model_ref_layout = QHBoxLayout()
        self.model_ref_edit = QLineEdit()
        self.model_ref_edit.textChanged.connect(self.asset_changed.emit)
        model_ref_layout.addWidget(self.model_ref_edit)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_model_ref)
        model_ref_layout.addWidget(browse_btn)
        
        basic_layout.addRow("Model Reference:", model_ref_layout)
        
        # Units
        self.units_combo = QComboBox()
        self.units_combo.addItems(["m", "cm", "mm", "in", "ft"])
        self.units_combo.currentTextChanged.connect(self.asset_changed.emit)
        basic_layout.addRow("Length Unit:", self.units_combo)
        
        layout.addWidget(basic_group)
        
        # Transform Group
        transform_group = QGroupBox("Default Transform")
        transform_layout = QVBoxLayout(transform_group)
        
        self.transform_editor = TransformEditorWidget()
        self.transform_editor.transform_changed.connect(self.asset_changed.emit)
        transform_layout.addWidget(self.transform_editor)
        
        layout.addWidget(transform_group)
        
        # Metadata Group
        metadata_group = QGroupBox("Metadata")
        metadata_layout = QFormLayout(metadata_group)
        
        self.author_edit = QLineEdit()
        self.author_edit.textChanged.connect(self.asset_changed.emit)
        metadata_layout.addRow("Author:", self.author_edit)
        
        self.version_edit = QLineEdit()
        self.version_edit.setPlaceholderText("e.g., 1.0.0")
        self.version_edit.textChanged.connect(self.asset_changed.emit)
        metadata_layout.addRow("Version:", self.version_edit)
        
        self.created_at_edit = QLineEdit()
        self.created_at_edit.setReadOnly(True)
        metadata_layout.addRow("Created At:", self.created_at_edit)
        
        self.updated_at_edit = QLineEdit()
        self.updated_at_edit.setReadOnly(True)
        metadata_layout.addRow("Updated At:", self.updated_at_edit)
        
        layout.addWidget(metadata_group)
        
        layout.addStretch()
    
    def _browse_model_ref(self):
        """Browse for USD model file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select USD Model",
            "",
            "USD Files (*.usd *.usda *.usdc);;All Files (*)"
        )
        if file_path:
            self.model_ref_edit.setText(file_path)
    
    def set_asset(self, asset: Asset):
        """Load asset data into form fields."""
        self.asset = asset
        
        # Block signals to prevent triggering asset_changed
        self.blockSignals(True)
        
        self.asset_id_edit.setText(asset.asset_id)
        self.name_edit.setText(asset.name)
        self.model_ref_edit.setText(asset.model_ref)
        
        # Units
        if asset.units:
            index = self.units_combo.findText(asset.units.length)
            if index >= 0:
                self.units_combo.setCurrentIndex(index)
        
        # Transform
        if asset.default_xform:
            self.transform_editor.set_transform(asset.default_xform)
        
        # Metadata
        if asset.metadata:
            self.author_edit.setText(asset.metadata.author or "")
            self.version_edit.setText(asset.metadata.version or "")
            self.created_at_edit.setText(asset.metadata.created_at or "")
            self.updated_at_edit.setText(asset.metadata.updated_at or "")
        
        self.blockSignals(False)
    
    def get_asset(self) -> Asset:
        """Collect data from form fields and return Asset."""
        if self.asset is None:
            # Create new asset
            asset_id = generate_asset_id()
            created_at = datetime.now().isoformat()
            updated_at = created_at
        else:
            asset_id = self.asset.asset_id
            created_at = self.asset.metadata.created_at if self.asset.metadata else datetime.now().isoformat()
            updated_at = datetime.now().isoformat()
        
        return Asset(
            asset_id=asset_id,
            name=self.name_edit.text(),
            model_ref=self.model_ref_edit.text(),
            units=Units(length=self.units_combo.currentText()),
            default_xform=self.transform_editor.get_transform(),
            tags=self.asset.tags if self.asset else [],
            metadata=Metadata(
                author=self.author_edit.text(),
                version=self.version_edit.text(),
                created_at=created_at,
                updated_at=updated_at
            )
        )


if __name__ == '__main__':
    """Demo: Test AssetEditorWidget"""
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Create test asset
    test_asset = Asset(
        asset_id=generate_asset_id(),
        name="Test Pump",
        model_ref="/path/to/pump.usd",
        units=Units(length="m"),
        default_xform=Transform(
            translation=[1.0, 2.0, 0.0],
            rotation=[0.0, 0.0, 90.0],
            scale=[1.0, 1.0, 1.0]
        ),
        tags=[],
        metadata=Metadata(
            author="Test User",
            version="1.0.0",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    )
    
    widget = AssetEditorWidget()
    widget.set_asset(test_asset)
    widget.show()
    
    sys.exit(app.exec())

