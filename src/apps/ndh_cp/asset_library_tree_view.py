"""
Asset Library Tree View Widget - Display asset library hierarchy
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QHeaderView
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor, QFont
from typing import Optional, Dict, List
from collections import defaultdict

from ...core.runtime.ndh_service import NDHService


class AssetLibraryTreeView(QWidget):
    """
    Asset Library Tree View Widget.
    
    Displays a hierarchical tree view of:
    - FDL file information
    - Asset types from the asset library
    - Asset instances (servants) generated from FDL
    - Tag counts for each asset
    
    The tree structure is:
    FDL: {site_name}
    ├── Asset Types ({count} types)
    │   ├── {asset_type_1} ({instance_count} instances)
    │   │   ├── Instance: {instance_id_1} ({tag_count} tags)
    │   │   └── Instance: {instance_id_2} ({tag_count} tags)
    │   └── {asset_type_2} ({instance_count} instances)
    │       └── Instance: {instance_id_3} ({tag_count} tags)
    └── Summary
        ├── Total Asset Types: {count}
        ├── Total Asset Instances: {count}
        └── Total Tags: {count}
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
        control_group = QGroupBox("Asset Library Controls")
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
        self.tree_widget.setHeaderLabels(["Name", "Count", "Type"])
        self.tree_widget.setColumnWidth(0, 400)
        self.tree_widget.setColumnWidth(1, 100)
        self.tree_widget.setColumnWidth(2, 150)
        
        # Enable alternating row colors
        self.tree_widget.setAlternatingRowColors(True)
        
        layout.addWidget(self.tree_widget)
    
    def set_ndh_service(self, ndh_service: NDHService):
        """Set NDH service"""
        self.ndh_service = ndh_service
        self._refresh_tree()
    
    def _refresh_tree(self):
        """Refresh the asset library tree"""
        if not self.ndh_service:
            return
        
        # Clear existing tree
        self.tree_widget.clear()
        
        # Check if FDL is loaded
        if not self.ndh_service.fdl:
            self.status_label.setText("Status: No FDL loaded")
            self.fdl_file_label.setText("FDL File: N/A")
            return
        
        # Update status
        fdl_name = self.ndh_service.fdl.site.name
        self.status_label.setText(f"Status: FDL loaded - {fdl_name}")
        self.fdl_file_label.setText(f"FDL File: {fdl_name}")
        
        # Create root node for FDL
        fdl_root = QTreeWidgetItem([f"FDL: {fdl_name}", "", "Site"])
        fdl_root.setFont(0, self._get_bold_font())
        fdl_root.setBackground(0, QColor(230, 240, 255))
        self.tree_widget.addTopLevelItem(fdl_root)
        
        # Group asset servants by asset type
        asset_type_groups = self._group_servants_by_type()
        
        # Create "Asset Types" node
        asset_types_node = QTreeWidgetItem([
            "Asset Types",
            str(len(asset_type_groups)),
            "Category"
        ])
        asset_types_node.setFont(0, self._get_bold_font())
        asset_types_node.setBackground(0, QColor(240, 255, 240))
        fdl_root.addChild(asset_types_node)
        
        # Add each asset type
        total_instances = 0
        total_tags = 0
        
        for asset_type_name, servants in sorted(asset_type_groups.items()):
            instance_count = len(servants)
            total_instances += instance_count
            
            # Create asset type node
            asset_type_node = QTreeWidgetItem([
                asset_type_name,
                f"{instance_count} instances",
                "Asset Type"
            ])
            asset_type_node.setFont(0, self._get_bold_font())
            asset_types_node.addChild(asset_type_node)
            
            # Add each instance
            for servant in servants:
                instance_id = servant.instance.instance_id
                tag_count = len(servant.get_all_tag_servants())
                total_tags += tag_count
                
                instance_node = QTreeWidgetItem([
                    f"Instance: {instance_id}",
                    f"{tag_count} tags",
                    "Asset Instance"
                ])
                asset_type_node.addChild(instance_node)
                
                # Add tags as children
                for tag_servant in servant.get_all_tag_servants():
                    tag_name = tag_servant.tag_definition.name
                    tag_kind = tag_servant.tag_definition.kind.value
                    tag_unit = tag_servant.tag_definition.eu_unit or "N/A"
                    
                    tag_node = QTreeWidgetItem([
                        f"Tag: {tag_name}",
                        tag_unit,
                        f"Tag ({tag_kind})"
                    ])
                    tag_node.setForeground(0, QColor(100, 100, 100))
                    instance_node.addChild(tag_node)
        
        # Create "Summary" node
        summary_node = QTreeWidgetItem(["Summary", "", "Category"])
        summary_node.setFont(0, self._get_bold_font())
        summary_node.setBackground(0, QColor(255, 250, 230))
        fdl_root.addChild(summary_node)
        
        # Add summary items
        summary_items = [
            ("Total Asset Types", str(len(asset_type_groups)), "Metric"),
            ("Total Asset Instances", str(total_instances), "Metric"),
            ("Total Tags", str(total_tags), "Metric"),
        ]
        
        for name, count, item_type in summary_items:
            summary_item = QTreeWidgetItem([name, count, item_type])
            summary_item.setFont(1, self._get_bold_font())
            summary_node.addChild(summary_item)
        
        # Expand root and main categories by default
        fdl_root.setExpanded(True)
        asset_types_node.setExpanded(True)
        summary_node.setExpanded(True)
    
    def _group_servants_by_type(self) -> Dict[str, List]:
        """Group asset servants by their asset type name"""
        if not self.ndh_service or not self.ndh_service.asset_servants:
            return {}
        
        groups = defaultdict(list)
        for servant in self.ndh_service.asset_servants.values():
            asset_type_name = servant.asset_definition.name
            groups[asset_type_name].append(servant)
        
        return dict(groups)
    
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

