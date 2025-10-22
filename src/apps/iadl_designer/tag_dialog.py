"""
IADL Designer - Tag Dialog
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QRadioButton, QButtonGroup, QGroupBox, QDoubleSpinBox,
    QDialogButtonBox, QHBoxLayout, QWidget
)
from PySide6.QtCore import Qt

from ...core.tags.models import Tag
from ...core.tags.id_generator import generate_tag_id


class TagDialog(QDialog):
    """Dialog for creating or editing a Tag."""
    
    def __init__(self, tag: Optional[Tag] = None, parent=None):
        super().__init__(parent)
        self.tag = tag
        self.is_edit_mode = tag is not None
        
        self.setWindowTitle("Edit Tag" if self.is_edit_mode else "New Tag")
        self.resize(500, 400)
        
        self._setup_ui()
        
        if tag:
            self._load_tag(tag)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Form layout
        form_layout = QFormLayout()
        
        # Tag ID (read-only if editing)
        self.tag_id_edit = QLineEdit()
        if self.is_edit_mode:
            self.tag_id_edit.setReadOnly(True)
        else:
            self.tag_id_edit.setText(generate_tag_id())
            self.tag_id_edit.setReadOnly(True)
        form_layout.addRow("Tag ID:", self.tag_id_edit)
        
        # Name
        self.name_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_edit)
        
        # Kind
        self.kind_combo = QComboBox()
        self.kind_combo.addItems(["analog", "digital", "string"])
        self.kind_combo.currentTextChanged.connect(self._on_kind_changed)
        form_layout.addRow("Kind:", self.kind_combo)
        
        # EU Unit (only for analog)
        self.eu_unit_edit = QLineEdit()
        form_layout.addRow("EU Unit:", self.eu_unit_edit)
        
        layout.addLayout(form_layout)
        
        # Attachment Strategy Group
        attachment_group = QGroupBox("Attachment Strategy")
        attachment_layout = QVBoxLayout(attachment_group)
        
        # Radio buttons
        self.by_pos_radio = QRadioButton("By Position (local_position)")
        self.by_prim_radio = QRadioButton("By Prim (attach_prim_path)")
        
        self.attachment_group = QButtonGroup()
        self.attachment_group.addButton(self.by_pos_radio, 0)
        self.attachment_group.addButton(self.by_prim_radio, 1)
        
        self.by_pos_radio.setChecked(True)
        self.by_pos_radio.toggled.connect(self._on_attachment_strategy_changed)
        
        attachment_layout.addWidget(self.by_pos_radio)
        attachment_layout.addWidget(self.by_prim_radio)
        
        # Local Position
        self.pos_widget = QWidget()
        pos_layout = QFormLayout(self.pos_widget)
        
        self.pos_x = QDoubleSpinBox()
        self.pos_y = QDoubleSpinBox()
        self.pos_z = QDoubleSpinBox()
        
        for spin in [self.pos_x, self.pos_y, self.pos_z]:
            spin.setRange(-1000, 1000)
            spin.setDecimals(3)
        
        pos_input_layout = QHBoxLayout()
        pos_input_layout.addWidget(self.pos_x)
        pos_input_layout.addWidget(self.pos_y)
        pos_input_layout.addWidget(self.pos_z)
        pos_layout.addRow("Position (X, Y, Z):", pos_input_layout)
        
        attachment_layout.addWidget(self.pos_widget)
        
        # Attach Prim Path
        self.prim_widget = QWidget()
        prim_layout = QFormLayout(self.prim_widget)
        
        self.prim_path_edit = QLineEdit()
        self.prim_path_edit.setPlaceholderText("e.g., /Pump/Outlet")
        prim_layout.addRow("Prim Path:", self.prim_path_edit)
        
        attachment_layout.addWidget(self.prim_widget)
        self.prim_widget.setVisible(False)
        
        layout.addWidget(attachment_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _on_kind_changed(self, kind: str):
        """Handle kind change."""
        # Enable/disable EU Unit based on kind
        self.eu_unit_edit.setEnabled(kind == "analog")
    
    def _on_attachment_strategy_changed(self, checked: bool):
        """Handle attachment strategy change."""
        if self.by_pos_radio.isChecked():
            self.pos_widget.setVisible(True)
            self.prim_widget.setVisible(False)
        else:
            self.pos_widget.setVisible(False)
            self.prim_widget.setVisible(True)
    
    def _load_tag(self, tag: Tag):
        """Load tag data into form fields."""
        self.tag_id_edit.setText(tag.tag_id)
        self.name_edit.setText(tag.name)
        
        # Kind
        index = self.kind_combo.findText(tag.kind)
        if index >= 0:
            self.kind_combo.setCurrentIndex(index)
        
        # EU Unit
        if tag.eu_unit:
            self.eu_unit_edit.setText(tag.eu_unit)
        
        # Attachment strategy
        if tag.local_position:
            self.by_pos_radio.setChecked(True)
            self.pos_x.setValue(tag.local_position[0])
            self.pos_y.setValue(tag.local_position[1])
            self.pos_z.setValue(tag.local_position[2])
        elif tag.attach_prim_path:
            self.by_prim_radio.setChecked(True)
            self.prim_path_edit.setText(tag.attach_prim_path)
    
    def get_tag(self) -> Tag:
        """Collect form data and return Tag."""
        tag_id = self.tag_id_edit.text()
        name = self.name_edit.text()
        kind = self.kind_combo.currentText()
        eu_unit = self.eu_unit_edit.text() if kind == "analog" else None
        
        # Attachment strategy
        if self.by_pos_radio.isChecked():
            local_position = [
                self.pos_x.value(),
                self.pos_y.value(),
                self.pos_z.value()
            ]
            attach_prim_path = None
        else:
            local_position = None
            attach_prim_path = self.prim_path_edit.text()
        
        return Tag(
            tag_id=tag_id,
            name=name,
            kind=kind,
            eu_unit=eu_unit,
            local_position=local_position,
            attach_prim_path=attach_prim_path
        )


if __name__ == '__main__':
    """Demo: Test TagDialog"""
    import sys
    from PySide6.QtWidgets import QApplication, QPushButton
    
    app = QApplication(sys.argv)
    
    def show_new_tag_dialog():
        dialog = TagDialog()
        if dialog.exec():
            tag = dialog.get_tag()
            print(f"Created tag: {tag.name} ({tag.kind})")
    
    def show_edit_tag_dialog():
        test_tag = Tag(
            tag_id=generate_tag_id(),
            name="Temperature",
            kind="analog",
            eu_unit="°C",
            local_position=[0.0, 0.0, 1.0]
        )
        
        dialog = TagDialog(tag=test_tag)
        if dialog.exec():
            tag = dialog.get_tag()
            print(f"Updated tag: {tag.name} ({tag.kind})")
    
    # Test buttons
    new_btn = QPushButton("New Tag")
    new_btn.clicked.connect(show_new_tag_dialog)
    new_btn.show()
    
    edit_btn = QPushButton("Edit Tag")
    edit_btn.clicked.connect(show_edit_tag_dialog)
    edit_btn.move(150, 0)
    edit_btn.show()
    
    sys.exit(app.exec())

