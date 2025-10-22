"""
FDL Designer - Instance List Widget
"""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QToolBar, QMessageBox
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction

from ...core.fdl.models import Site, AssetInstance
from ...core.tags.id_generator import generate_instance_id
from .add_instance_dialog import AddInstanceDialog


class InstanceListWidget(QWidget):
    """
    Widget for displaying and managing a list of AssetInstances within an FDL Site.
    """
    
    instance_selected = Signal(AssetInstance)
    instance_added = Signal(AssetInstance) # Emitted when a new instance is added
    instance_removed = Signal(str) # Emitted when an instance is removed (instance_id)
    instances_changed = Signal() # Emitted when the list of instances changes
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.site: Optional[Site] = None
        self.instances: List[AssetInstance] = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        add_action = QAction("Add Instance", self)
        add_action.triggered.connect(self.add_instance_dialog)
        toolbar.addAction(add_action)
        
        edit_action = QAction("Edit Instance", self)
        edit_action.triggered.connect(self.edit_instance)
        toolbar.addAction(edit_action)
        
        remove_action = QAction("Remove Instance", self)
        remove_action.triggered.connect(self.remove_instance_dialog)
        toolbar.addAction(remove_action)
        
        layout.addWidget(toolbar)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)
    
    def set_site(self, site: Site):
        """
        Set the current FDL Site and populate the instance list.
        """
        self.site = site
        self.instances = site.areas[0].instances if site.areas else [] # Assuming single area for MVP
        self._update_list()
    
    def get_instances(self) -> List[AssetInstance]:
        """
        Return the current list of AssetInstances.
        """
        return self.instances
    
    def _update_list(self):
        """
        Refresh the QListWidget with current instances.
        """
        self.list_widget.clear()
        for instance in self.instances:
            item_text = f"{instance.name} ({instance.instance_id[:8]}...)"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, instance.instance_id)
            self.list_widget.addItem(item)
    
    def add_instance_dialog(self):
        """
        Show dialog to add a new AssetInstance.
        """
        dialog = AddInstanceDialog(parent=self)
        if dialog.exec():
            instance = dialog.get_instance()
            if self.site and self.site.areas:
                self.site.areas[0].instances.append(instance)
                self.instances = self.site.areas[0].instances # Update reference
                self._update_list()
                self.instance_added.emit(instance)
                self.instances_changed.emit()
            else:
                QMessageBox.warning(self, "Add Instance", "Cannot add instance: No area defined in site.")
    
    def edit_instance(self):
        """
        Show dialog to edit the selected AssetInstance.
        """
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.information(self, "Edit Instance", "Please select an instance to edit.")
            return
        
        instance_id = current_item.data(Qt.UserRole)
        instance = self._find_instance_by_id(instance_id)
        
        if instance:
            dialog = AddInstanceDialog(instance=instance, parent=self)
            if dialog.exec():
                updated_instance = dialog.get_instance()
                # Find and replace the instance in the list
                for i, inst in enumerate(self.instances):
                    if inst.instance_id == updated_instance.instance_id:
                        self.instances[i] = updated_instance
                        break
                self._update_list()
                self.instances_changed.emit()
    
    def remove_instance_dialog(self):
        """
        Remove the selected AssetInstance.
        """
        current_item = self.list_widget.currentItem()
        if not current_item:
            QMessageBox.information(self, "Remove Instance", "Please select an instance to remove.")
            return
        
        instance_id = current_item.data(Qt.UserRole)
        instance = self._find_instance_by_id(instance_id)
        
        if instance:
            reply = QMessageBox.question(
                self,
                "Remove Instance",
                f"Are you sure you want to remove instance 
                \'{instance.name}\' ({instance.instance_id[:8]}...)?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                if self.site and self.site.areas:
                    self.site.areas[0].instances.remove(instance)
                    self.instances = self.site.areas[0].instances # Update reference
                    self._update_list()
                    self.instance_removed.emit(instance_id)
                    self.instances_changed.emit()
    
    def _find_instance_by_id(self, instance_id: str) -> Optional[AssetInstance]:
        """
        Helper to find an AssetInstance by its ID.
        """
        for instance in self.instances:
            if instance.instance_id == instance_id:
                return instance
        return None
    
    def _on_item_double_clicked(self, item: QListWidgetItem):
        """
        Handle double-click on an item to edit the instance.
        """
        self.edit_instance()
    
    def _on_selection_changed(self):
        """
        Emit instance_selected signal when selection changes.
        """
        current_item = self.list_widget.currentItem()
        if current_item:
            instance_id = current_item.data(Qt.UserRole)
            instance = self._find_instance_by_id(instance_id)
            if instance:
                self.instance_selected.emit(instance)

    def update_instance_transform(self, instance_id: str, transform: dict):
        """
        Update the transform of an instance, typically from the layout editor.
        """
        instance = self._find_instance_by_id(instance_id)
        if instance:
            instance.transform.translation = transform["translation"]
            instance.transform.rotation = transform["rotation"]
            instance.transform.scale = transform["scale"]
            self.instances_changed.emit()


if __name__ == '__main__':
    """Demo: Test InstanceListWidget"""
    import sys
    from PySide6.QtWidgets import QApplication
    from ...core.fdl.models import Site, Area, Transform
    from ...core.iadl.models import Asset
    from ...core.tags.id_generator import generate_asset_id, generate_instance_id
    
    app = QApplication(sys.argv)
    
    # Create dummy assets for testing
    asset1 = Asset(
        asset_id=generate_asset_id(),
        name="Pump Model A",
        model_ref="/path/to/pump_a.usd",
        units=None, default_xform=None, tags=[], metadata=None
    )
    asset2 = Asset(
        asset_id=generate_asset_id(),
        name="Valve Type B",
        model_ref="/path/to/valve_b.usd",
        units=None, default_xform=None, tags=[], metadata=None
    )
    
    # Create dummy instances
    instance1 = AssetInstance(
        instance_id=generate_instance_id(),
        name="Pump_001",
        ref_asset=asset1.asset_id,
        transform=Transform(translation=[1.0, 2.0, 0.0], rotation=[0.0, 0.0, 0.0], scale=[1.0, 1.0, 1.0]),
        tag_overrides=[]
    )
    instance2 = AssetInstance(
        instance_id=generate_instance_id(),
        name="Valve_005",
        ref_asset=asset2.asset_id,
        transform=Transform(translation=[5.0, 1.0, 0.0], rotation=[0.0, 0.0, 90.0], scale=[1.0, 1.0, 1.0]),
        tag_overrides=[]
    )
    
    # Create a dummy site
    test_site = Site(
        name="Test Site",
        areas=[
            Area(
                name="Main Area",
                instances=[instance1, instance2]
            )
        ]
    )
    
    widget = InstanceListWidget()
    widget.set_site(test_site)
    widget.show()
    
    sys.exit(app.exec())
