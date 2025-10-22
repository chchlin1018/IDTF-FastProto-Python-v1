"""
FDL Designer - Layout Editor Widget
"""

from typing import Optional, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGraphicsView, QGraphicsScene, QGraphicsRectItem,
    QGraphicsTextItem, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QBrush

from ...core.fdl.models import Site, AssetInstance
from ...core.iadl.models import Transform


class InstanceGraphicsItem(QGraphicsRectItem):
    """
    A QGraphicsRectItem representing an AssetInstance in the layout.
    """
    def __init__(self, instance: AssetInstance, parent=None):
        super().__init__(parent)
        self.instance = instance
        self.setFlags(QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        self.setToolTip(f"Instance: {instance.name}\nID: {instance.instance_id[:8]}...")
        self._update_geometry()
        self._update_color()

    def _update_geometry(self):
        # For MVP, assume a default size and position based on transform
        # In a real scenario, this would come from the asset's bounding box
        size = 1.0 # Default size for visualization
        x = self.instance.transform.translation[0] - size / 2
        y = self.instance.transform.translation[1] - size / 2
        self.setRect(x, y, size, size)
        # Rotation is more complex for QGraphicsRectItem, for MVP we just use position

    def _update_color(self, selected=False):
        if selected:
            self.setBrush(QBrush(QColor(Qt.blue).lighter(150)))
            self.setPen(QPen(QColor(Qt.darkBlue), 2))
        else:
            self.setBrush(QBrush(QColor(Qt.gray).lighter(150)))
            self.setPen(QPen(QColor(Qt.darkGray), 1))

    def itemChange(self, change, value):
        if change == QGraphicsRectItem.ItemSelectedChange:
            self._update_color(value)
        elif change == QGraphicsRectItem.ItemPositionChange:
            # Update instance's transform based on new position
            new_pos = value
            self.instance.transform.translation[0] = new_pos.x() + self.rect().width() / 2
            self.instance.transform.translation[1] = new_pos.y() + self.rect().height() / 2
            # Emit signal from scene/widget to notify of change
        return super().itemChange(change, value)


class LayoutEditorWidget(QWidget):
    """
    Widget for visualizing and editing the FDL layout.
    For MVP, this is a 2D representation using QGraphicsView.
    """
    instance_transform_changed = Signal(str, dict) # instance_id, {translation, rotation, scale}
    layout_changed = Signal() # Emitted when layout changes (e.g., instance moved)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.site: Optional[Site] = None
        self.instance_items: Dict[str, InstanceGraphicsItem] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QGraphicsView.Antialiasing)
        self.view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

        # Add a grid to the scene for better visualization
        self._draw_grid()

        layout.addWidget(self.view)

    def _draw_grid(self):
        grid_size = 10
        pen = QPen(QColor(200, 200, 200), 0.5)
        for x in range(-100, 101, grid_size):
            self.scene.addLine(x, -100, x, 100, pen)
        for y in range(-100, 101, grid_size):
            self.scene.addLine(-100, y, 100, y, pen)

    def set_site(self, site: Site):
        """
        Set the current FDL Site and populate the layout.
        """
        self.site = site
        self.scene.clear()
        self.instance_items.clear()
        self._draw_grid() # Redraw grid after clearing

        if self.site and self.site.areas:
            for instance in self.site.areas[0].instances: # Assuming single area for MVP
                self._add_instance_to_scene(instance)
        self.view.setSceneRect(self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50))

    def _add_instance_to_scene(self, instance: AssetInstance):
        item = InstanceGraphicsItem(instance)
        self.scene.addItem(item)
        self.instance_items[instance.instance_id] = item

    def add_instance(self, instance: AssetInstance):
        """
        Add a new instance to the layout.
        """
        if self.site and self.site.areas:
            # Assuming instance is already added to site.areas[0].instances
            self._add_instance_to_scene(instance)
            self.view.setSceneRect(self.scene.itemsBoundingRect().adjusted(-50, -50, 50, 50))
            self.layout_changed.emit()

    def remove_instance(self, instance_id: str):
        """
        Remove an instance from the layout.
        """
        if instance_id in self.instance_items:
            item = self.instance_items.pop(instance_id)
            self.scene.removeItem(item)
            self.layout_changed.emit()

    def select_instance(self, instance: AssetInstance):
        """
        Select an instance in the layout.
        """
        for item_id, item in self.instance_items.items():
            item.setSelected(item_id == instance.instance_id)

    def update_instance_transform(self, instance_id: str, transform: dict):
        """
        Update the transform of an instance, typically from the instance list.
        """
        if instance_id in self.instance_items:
            item = self.instance_items[instance_id]
            instance = item.instance
            instance.transform.translation[0] = transform["translation"][0]
            instance.transform.translation[1] = transform["translation"][1]
            instance.transform.translation[2] = transform["translation"][2]
            instance.transform.rotation[0] = transform["rotation"][0]
            instance.transform.rotation[1] = transform["rotation"][1]
            instance.transform.rotation[2] = transform["rotation"][2]
            instance.transform.scale[0] = transform["scale"][0]
            instance.transform.scale[1] = transform["scale"][1]
            instance.transform.scale[2] = transform["scale"][2]
            item._update_geometry() # Update visual representation
            item.setPos(QPointF(instance.transform.translation[0] - item.rect().width() / 2, 
                                instance.transform.translation[1] - item.rect().height() / 2))
            self.layout_changed.emit()


if __name__ == '__main__':
    """Demo: Test LayoutEditorWidget"""
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

    widget = LayoutEditorWidget()
    widget.set_site(test_site)
    widget.show()

    sys.exit(app.exec())
