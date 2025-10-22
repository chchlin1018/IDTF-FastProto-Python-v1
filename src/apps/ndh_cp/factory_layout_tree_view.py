"""
Factory Layout Tree View Widget - Display FDL file structure
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QHeaderView
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QFont
from typing import Optional, Dict, Any

from ...core.runtime.ndh_service import NDHService
from ...core.fdl.models import FDL, Site, Area, AssetInstance, Connection


class FactoryLayoutTreeView(QWidget):
    """
    Factory Layout Tree View Widget.
    
    Displays the complete hierarchical structure of the FDL file:
    - Site information
    - Areas within the site
    - Asset instances within each area
    - Connections between assets
    - Properties and metadata at each level
    
    The tree structure is:
    FDL: {site_name}
    ├── Site Properties
    │   ├── Site ID: {site_id}
    │   ├── Location: {location}
    │   └── Units: {units}
    ├── Area: {area_name_1}
    │   ├── Area Properties
    │   │   ├── Area ID: {area_id}
    │   │   └── Type: {area_type}
    │   ├── Asset Instances ({count} instances)
    │   │   ├── Instance: {instance_id_1}
    │   │   │   ├── Ref Asset: {ref_asset}
    │   │   │   ├── Transform: {transform}
    │   │   │   └── Properties: {properties}
    │   │   └── Instance: {instance_id_2}
    │   └── Connections ({count} connections)
    │       └── Connection: {connection_id}
    │           ├── Type: {type}
    │           ├── From: {from_instance}
    │           └── To: {to_instance}
    └── Area: {area_name_2}
    """
    
    def __init__(self, ndh_service: Optional[NDHService] = None, parent=None):
        super().__init__(parent)
        self.ndh_service = ndh_service
        self._init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_tree)
        self.refresh_timer.start(2000)  # Refresh every 2 seconds
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Control panel
        control_group = QGroupBox("Factory Layout Controls")
        control_layout = QHBoxLayout()
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Tree")
        self.refresh_btn.clicked.connect(self._refresh_tree)
        control_layout.addWidget(self.refresh_btn)
        
        # Expand/Collapse buttons
        self.expand_all_btn = QPushButton("Expand All")
        self.expand_all_btn.clicked.connect(self._expand_all)
        control_layout.addWidget(self.expand_all_btn)
        
        self.collapse_all_btn = QPushButton("Collapse All")
        self.collapse_all_btn.clicked.connect(self._collapse_all)
        control_layout.addWidget(self.collapse_all_btn)
        
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Status info
        info_layout = QHBoxLayout()
        self.status_label = QLabel("Status: No FDL loaded")
        self.fdl_file_label = QLabel("FDL File: N/A")
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.fdl_file_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Tree widget
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Property", "Value", "Type"])
        self.tree_widget.setColumnWidth(0, 400)
        self.tree_widget.setColumnWidth(1, 300)
        self.tree_widget.setColumnWidth(2, 150)
        
        # Enable alternating row colors
        self.tree_widget.setAlternatingRowColors(True)
        
        layout.addWidget(self.tree_widget)
    
    def set_ndh_service(self, ndh_service: NDHService):
        """Set NDH service"""
        self.ndh_service = ndh_service
        self._refresh_tree()
    
    def _refresh_tree(self):
        """Refresh the factory layout tree"""
        if not self.ndh_service:
            return
        
        # Clear existing tree
        self.tree_widget.clear()
        
        # Check if FDL is loaded
        if not self.ndh_service.fdl:
            self.status_label.setText("Status: No FDL loaded")
            self.fdl_file_label.setText("FDL File: N/A")
            return
        
        fdl = self.ndh_service.fdl
        
        # Update status
        self.status_label.setText(f"Status: FDL loaded - {fdl.site.name}")
        self.fdl_file_label.setText(f"FDL File: {fdl.site.name}")
        
        # Create root node for FDL
        fdl_root = QTreeWidgetItem([f"FDL: {fdl.site.name}", "", "Site"])
        fdl_root.setFont(0, self._get_bold_font())
        fdl_root.setBackground(0, QColor(230, 240, 255))
        self.tree_widget.addTopLevelItem(fdl_root)
        
        # Add Site Properties
        self._add_site_properties(fdl_root, fdl.site, fdl)
        
        # Add Areas
        for area in fdl.site.areas:
            self._add_area(fdl_root, area)
        
        # Add Global Settings
        self._add_global_settings(fdl_root, fdl)
        
        # Expand root by default
        fdl_root.setExpanded(True)
    
    def _add_site_properties(self, parent: QTreeWidgetItem, site: Site, fdl: FDL):
        """Add site properties to the tree"""
        props_node = QTreeWidgetItem(["Site Properties", "", "Category"])
        props_node.setFont(0, self._get_bold_font())
        props_node.setBackground(0, QColor(240, 255, 240))
        parent.addChild(props_node)
        
        # Site ID
        self._add_property(props_node, "Site ID", site.site_id, "UUID")
        
        # Location
        if site.location:
            location_str = f"Lat: {site.location.get('latitude', 'N/A')}, " \
                          f"Lon: {site.location.get('longitude', 'N/A')}, " \
                          f"Alt: {site.location.get('altitude', 'N/A')}"
            self._add_property(props_node, "Location", location_str, "Coordinates")
        
        # Units
        if fdl.units:
            units_str = f"Length: {fdl.units.length.value}, " \
                       f"Angle: {fdl.units.angle.value}, " \
                       f"Up: {fdl.units.up_axis.value}, " \
                       f"Hand: {fdl.units.handedness.value}"
            self._add_property(props_node, "Units", units_str, "System")
        
        # Area count
        self._add_property(props_node, "Total Areas", str(len(site.areas)), "Count")
        
        props_node.setExpanded(True)
    
    def _add_area(self, parent: QTreeWidgetItem, area: Area):
        """Add an area to the tree"""
        area_node = QTreeWidgetItem([f"Area: {area.name}", "", "Area"])
        area_node.setFont(0, self._get_bold_font())
        area_node.setBackground(0, QColor(255, 250, 230))
        parent.addChild(area_node)
        
        # Area Properties
        props_node = QTreeWidgetItem(["Area Properties", "", "Category"])
        props_node.setFont(0, self._get_bold_font())
        area_node.addChild(props_node)
        
        self._add_property(props_node, "Area ID", area.area_id, "UUID")
        self._add_property(props_node, "Type", area.type, "String")
        self._add_property(props_node, "Instance Count", str(len(area.instances)), "Count")
        self._add_property(props_node, "Connection Count", str(len(area.connections)), "Count")
        
        # Asset Instances
        instances_node = QTreeWidgetItem([
            f"Asset Instances ({len(area.instances)} instances)",
            "",
            "Category"
        ])
        instances_node.setFont(0, self._get_bold_font())
        instances_node.setBackground(0, QColor(240, 255, 240))
        area_node.addChild(instances_node)
        
        for instance in area.instances:
            self._add_asset_instance(instances_node, instance)
        
        # Connections
        connections_node = QTreeWidgetItem([
            f"Connections ({len(area.connections)} connections)",
            "",
            "Category"
        ])
        connections_node.setFont(0, self._get_bold_font())
        connections_node.setBackground(0, QColor(255, 240, 240))
        area_node.addChild(connections_node)
        
        for connection in area.connections:
            self._add_connection(connections_node, connection)
        
        area_node.setExpanded(True)
        instances_node.setExpanded(True)
    
    def _add_asset_instance(self, parent: QTreeWidgetItem, instance: AssetInstance):
        """Add an asset instance to the tree"""
        instance_node = QTreeWidgetItem([
            f"Instance: {instance.instance_id}",
            "",
            "Asset Instance"
        ])
        parent.addChild(instance_node)
        
        # Ref Asset
        self._add_property(instance_node, "Ref Asset", instance.ref_asset, "Reference")
        
        # Name
        if instance.name:
            self._add_property(instance_node, "Name", instance.name, "String")
        
        # Transform
        transform_str = f"T: {instance.transform.translation}, " \
                       f"R: {instance.transform.rotation}, " \
                       f"S: {instance.transform.scale}"
        self._add_property(instance_node, "Transform", transform_str, "Transform")
        
        # Tag Overrides
        if instance.tag_overrides:
            overrides_node = QTreeWidgetItem([
                f"Tag Overrides ({len(instance.tag_overrides)} overrides)",
                "",
                "Category"
            ])
            instance_node.addChild(overrides_node)
            
            for i, override in enumerate(instance.tag_overrides):
                override_str = ", ".join([f"{k}: {v}" for k, v in override.items()])
                self._add_property(overrides_node, f"Override {i+1}", override_str, "Dict")
        
        # Collision Bounds
        if instance.collision_bounds:
            bounds_str = ", ".join([f"{k}: {v}" for k, v in instance.collision_bounds.items()])
            self._add_property(instance_node, "Collision Bounds", bounds_str, "Bounds")
        
        # Constraints
        if instance.constraints:
            constraints_node = QTreeWidgetItem(["Constraints", "", "Category"])
            instance_node.addChild(constraints_node)
            
            for key, value in instance.constraints.items():
                self._add_property(constraints_node, key, str(value), "Constraint")
        
        # Metadata
        if instance.metadata:
            metadata_node = QTreeWidgetItem(["Metadata", "", "Category"])
            instance_node.addChild(metadata_node)
            
            for key, value in instance.metadata.items():
                self._add_property(metadata_node, key, str(value), "Metadata")
    
    def _add_connection(self, parent: QTreeWidgetItem, connection: Connection):
        """Add a connection to the tree"""
        connection_node = QTreeWidgetItem([
            f"Connection: {connection.connection_id}",
            "",
            "Connection"
        ])
        parent.addChild(connection_node)
        
        # Type
        self._add_property(connection_node, "Type", connection.type, "String")
        
        # Name
        if connection.name:
            self._add_property(connection_node, "Name", connection.name, "String")
        
        # From
        from_str = connection.from_instance
        if connection.from_port:
            from_str += f" (port: {connection.from_port})"
        self._add_property(connection_node, "From", from_str, "Reference")
        
        # To
        to_str = connection.to_instance
        if connection.to_port:
            to_str += f" (port: {connection.to_port})"
        self._add_property(connection_node, "To", to_str, "Reference")
        
        # Path
        if connection.path:
            path_str = ", ".join([f"{k}: {v}" for k, v in connection.path.items()])
            self._add_property(connection_node, "Path", path_str, "Geometry")
        
        # Properties
        if connection.properties:
            props_node = QTreeWidgetItem(["Properties", "", "Category"])
            connection_node.addChild(props_node)
            
            for key, value in connection.properties.items():
                self._add_property(props_node, key, str(value), "Property")
    
    def _add_global_settings(self, parent: QTreeWidgetItem, fdl: FDL):
        """Add global settings to the tree"""
        settings_node = QTreeWidgetItem(["Global Settings", "", "Category"])
        settings_node.setFont(0, self._get_bold_font())
        settings_node.setBackground(0, QColor(255, 240, 255))
        parent.addChild(settings_node)
        
        if not fdl.global_constraints:
            return
        
        # Scaling Constraints
        if fdl.global_constraints.scaling_constraints:
            sc = fdl.global_constraints.scaling_constraints
            scaling_node = QTreeWidgetItem(["Scaling Constraints", "", "Category"])
            settings_node.addChild(scaling_node)
            
            self._add_property(scaling_node, "Allow Scaling", str(sc.allow_scaling), "Boolean")
            self._add_property(scaling_node, "Allow Non-Uniform", str(sc.allow_non_uniform_scaling), "Boolean")
            if sc.min_scale is not None:
                self._add_property(scaling_node, "Min Scale", str(sc.min_scale), "Float")
            if sc.max_scale is not None:
                self._add_property(scaling_node, "Max Scale", str(sc.max_scale), "Float")
        
        # Collision Detection
        if fdl.global_constraints.collision_detection:
            cd = fdl.global_constraints.collision_detection
            collision_node = QTreeWidgetItem(["Collision Detection", "", "Category"])
            settings_node.addChild(collision_node)
            
            self._add_property(collision_node, "Enabled", str(cd.enabled), "Boolean")
            self._add_property(collision_node, "Clearance Distance", f"{cd.clearance_distance} m", "Float")
    
    def _add_property(self, parent: QTreeWidgetItem, name: str, value: str, prop_type: str):
        """Add a property to the tree"""
        prop_item = QTreeWidgetItem([name, value, prop_type])
        parent.addChild(prop_item)
    
    def _expand_all(self):
        """Expand all tree nodes"""
        self.tree_widget.expandAll()
    
    def _collapse_all(self):
        """Collapse all tree nodes"""
        self.tree_widget.collapseAll()
    
    def _get_bold_font(self) -> QFont:
        """Get a bold font"""
        font = QFont()
        font.setBold(True)
        return font

