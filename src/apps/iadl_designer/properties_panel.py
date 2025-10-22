"""
IADL Designer - Properties Panel
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit, QLabel
)
from PySide6.QtCore import Qt

from ...core.tags.models import Tag


class PropertiesPanel(QWidget):
    """Widget for displaying detailed properties."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.title_label = QLabel("Properties")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)
    
    def show_tag_properties(self, tag: Tag):
        """Display tag properties."""
        self.title_label.setText(f"Tag Properties: {tag.name}")
        
        properties = []
        properties.append(f"Tag ID: {tag.tag_id}")
        properties.append(f"Name: {tag.name}")
        properties.append(f"Kind: {tag.kind}")
        
        if tag.eu_unit:
            properties.append(f"EU Unit: {tag.eu_unit}")
        
        if tag.local_position:
            pos = tag.local_position
            properties.append(f"Local Position: [{pos[0]:.3f}, {pos[1]:.3f}, {pos[2]:.3f}]")
        
        if tag.attach_prim_path:
            properties.append(f"Attach Prim Path: {tag.attach_prim_path}")
        
        self.text_edit.setPlainText("\n".join(properties))
    
    def clear(self):
        """Clear properties display."""
        self.title_label.setText("Properties")
        self.text_edit.clear()


if __name__ == '__main__':
    """Demo: Test PropertiesPanel"""
    import sys
    from PySide6.QtWidgets import QApplication
    from ...core.tags.id_generator import generate_tag_id
    
    app = QApplication(sys.argv)
    
    test_tag = Tag(
        tag_id=generate_tag_id(),
        name="Temperature",
        kind="analog",
        eu_unit="°C",
        local_position=[0.0, 0.0, 1.0]
    )
    
    widget = PropertiesPanel()
    widget.show_tag_properties(test_tag)
    widget.show()
    
    sys.exit(app.exec())

