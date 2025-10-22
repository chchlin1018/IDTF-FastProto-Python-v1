"""
IADL Designer - Tag List Widget
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QToolBar, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction

from ...core.tags.models import Tag
from .tag_dialog import TagDialog


class TagListWidget(QWidget):
    """Widget for displaying and managing Tags list."""
    
    tag_selected = Signal(Tag)
    tag_added = Signal(Tag)
    tag_removed = Signal(str)  # tag_id
    tags_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tags: List[Tag] = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        add_action = QAction("Add", self)
        add_action.triggered.connect(self.add_tag)
        toolbar.addAction(add_action)
        
        edit_action = QAction("Edit", self)
        edit_action.triggered.connect(self.edit_tag)
        toolbar.addAction(edit_action)
        
        remove_action = QAction("Remove", self)
        remove_action.triggered.connect(self.remove_tag)
        toolbar.addAction(remove_action)
        
        layout.addWidget(toolbar)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)
    
    def set_tags(self, tags: List[Tag]):
        """Load tags into list."""
        self.tags = tags
        self._update_list()
    
    def get_tags(self) -> List[Tag]:
        """Return current tags list."""
        return self.tags
    
    def _update_list(self):
        """Refresh QListWidget."""
        self.list_widget.clear()
        
        for tag in self.tags:
            # Display format: "Tag Name (kind)"
            item_text = f"{tag.name} ({tag.kind})"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, tag.tag_id)
            self.list_widget.addItem(item)
    
    def add_tag(self):
        """Show TagDialog to create new tag."""
        dialog = TagDialog(parent=self)
        
        if dialog.exec():
            tag = dialog.get_tag()
            self.tags.append(tag)
            self._update_list()
            self.tag_added.emit(tag)
            self.tags_changed.emit()
    
    def edit_tag(self):
        """Show TagDialog to edit selected tag."""
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.information(self, "Edit Tag", "Please select a tag to edit")
            return
        
        tag_id = current_item.data(Qt.UserRole)
        tag = self._find_tag_by_id(tag_id)
        
        if tag:
            dialog = TagDialog(tag=tag, parent=self)
            
            if dialog.exec():
                updated_tag = dialog.get_tag()
                # Replace tag in list
                index = self.tags.index(tag)
                self.tags[index] = updated_tag
                self._update_list()
                self.tags_changed.emit()
    
    def remove_tag(self):
        """Remove selected tag."""
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.information(self, "Remove Tag", "Please select a tag to remove")
            return
        
        tag_id = current_item.data(Qt.UserRole)
        tag = self._find_tag_by_id(tag_id)
        
        if tag:
            reply = QMessageBox.question(
                self,
                "Remove Tag",
                f"Are you sure you want to remove tag '{tag.name}'?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.tags.remove(tag)
                self._update_list()
                self.tag_removed.emit(tag_id)
                self.tags_changed.emit()
    
    def _find_tag_by_id(self, tag_id: str) -> Optional[Tag]:
        """Find tag by ID."""
        for tag in self.tags:
            if tag.tag_id == tag_id:
                return tag
        return None
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on item."""
        self.edit_tag()
    
    def _on_selection_changed(self):
        """Handle selection change."""
        current_item = self.list_widget.currentItem()
        if current_item:
            tag_id = current_item.data(Qt.UserRole)
            tag = self._find_tag_by_id(tag_id)
            if tag:
                self.tag_selected.emit(tag)


if __name__ == '__main__':
    """Demo: Test TagListWidget"""
    import sys
    from PySide6.QtWidgets import QApplication
    from ...core.tags.id_generator import generate_tag_id
    
    app = QApplication(sys.argv)
    
    # Create test tags
    test_tags = [
        Tag(
            tag_id=generate_tag_id(),
            name="Temperature",
            kind="analog",
            eu_unit="°C",
            local_position=[0.0, 0.0, 1.0]
        ),
        Tag(
            tag_id=generate_tag_id(),
            name="Pressure",
            kind="analog",
            eu_unit="bar",
            local_position=[0.5, 0.0, 1.0]
        ),
        Tag(
            tag_id=generate_tag_id(),
            name="Status",
            kind="digital",
            local_position=[1.0, 0.0, 1.0]
        )
    ]
    
    widget = TagListWidget()
    widget.set_tags(test_tags)
    widget.show()
    
    sys.exit(app.exec())

