"""
FDL Designer - Add/Edit Instance Dialog
"""

from typing import Optional, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QDialogButtonBox, QHBoxLayout, QWidget, QDoubleSpinBox
)
from PySide6.QtCore import Qt

from ...core.fdl.models import AssetInstance
from ...core.iadl.models import Transform # Re-use Transform model
from ...core.tags.id_generator import generate_instance_id


class TransformEditorWidget(QWidget):
    """Widget for editing Transform (translation, rotation, scale)."""
    
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


class AddInstanceDialog(QDialog):
    """Dialog for adding or editing an AssetInstance."""
    
    def __init__(self, instance: Optional[AssetInstance] = None, parent=None):
        super().__init__(parent)
        self.instance = instance
        self.is_edit_mode = instance is not None
        
        self.setWindowTitle("Edit Instance" if self.is_edit_mode else "Add Instance")
        self.resize(500, 600)
        
        self._setup_ui()
        
        if instance:
            self._load_instance(instance)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Instance ID (read-only)
        self.instance_id_edit = QLineEdit()
        if self.is_edit_mode:
            self.instance_id_edit.setReadOnly(True)
        else:
            self.instance_id_edit.setText(generate_instance_id())
            self.instance_id_edit.setReadOnly(True)
        form_layout.addRow("Instance ID:", self.instance_id_edit)
        
        # Name
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        
        # Reference Asset (for MVP, just text input, later from Asset Library)
        self.ref_asset_edit = QLineEdit()
        self.ref_asset_edit.setPlaceholderText("Enter Asset ID or browse...")
        form_layout.addRow("Reference Asset ID:", self.ref_asset_edit)
        
        layout.addLayout(form_layout)
        
        # Transform Editor
        self.transform_editor = TransformEditorWidget()
        layout.addWidget(self.transform_editor)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _load_instance(self, instance: AssetInstance):
        """Load instance data into form fields."""
        self.instance_id_edit.setText(instance.instance_id)
        self.name_edit.setText(instance.name)
        self.ref_asset_edit.setText(instance.ref_asset)
        self.transform_editor.set_transform(instance.transform)
    
    def get_instance(self) -> AssetInstance:
        """Collect form data and return AssetInstance."""
        instance_id = self.instance_id_edit.text()
        name = self.name_edit.text()
        ref_asset = self.ref_asset_edit.text()
        transform = self.transform_editor.get_transform()
        
        return AssetInstance(
            instance_id=instance_id,
            name=name,
            ref_asset=ref_asset,
            transform=transform,
            tag_overrides=[] # Not implemented in MVP
        )


if __name__ == '__main__':
    """Demo: Test AddInstanceDialog"""
    import sys
    from PySide6.QtWidgets import QApplication, QPushButton
    
    app = QApplication(sys.argv)
    
    def show_add_dialog():
        dialog = AddInstanceDialog()
        if dialog.exec():
            instance = dialog.get_instance()
            print(f"Added instance: {instance.name} (Asset: {instance.ref_asset})")
            print(f"Transform: {instance.transform.translation}")
    
    def show_edit_dialog():
        test_instance = AssetInstance(
            instance_id=generate_instance_id(),
            name="Test Pump 001",
            ref_asset="018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e11",
            transform=Transform(
                translation=[10.0, 5.0, 0.0],
                rotation=[0.0, 0.0, 45.0],
                scale=[1.0, 1.0, 1.0]
            ),
            tag_overrides=[]
        )
        dialog = AddInstanceDialog(instance=test_instance)
        if dialog.exec():
            instance = dialog.get_instance()
            print(f"Edited instance: {instance.name} (Asset: {instance.ref_asset})")
            print(f"Transform: {instance.transform.translation}")
            
    add_btn = QPushButton("Add Instance")
    add_btn.clicked.connect(show_add_dialog)
    add_btn.show()
    
    edit_btn = QPushButton("Edit Instance")
    edit_btn.clicked.connect(show_edit_dialog)
    edit_btn.move(150, 0)
    edit_btn.show()
    
    sys.exit(app.exec())
