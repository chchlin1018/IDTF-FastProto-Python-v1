"""
Realtime Tag Monitor Widget - Display real-time tag values from TSDB
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QGroupBox, QSpinBox, QHeaderView
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QColor
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from ...core.tsdb.interfaces import ITSDB
from ...core.runtime.ndh_service import NDHService


class RealtimeTagMonitorWidget(QWidget):
    """
    Realtime Tag Monitor Widget.
    
    Displays real-time tag values from TSDB for a configurable number of tags.
    Features:
    - Select number of tags to display (default: 10)
    - Auto-refresh from TSDB
    - Show tag name, current value, timestamp, and update rate
    - Color-coded status indicators
    """
    
    def __init__(self, ndh_service: Optional[NDHService] = None, 
                 tsdb: Optional[ITSDB] = None, parent=None):
        super().__init__(parent)
        self.ndh_service = ndh_service
        self.tsdb = tsdb
        self.max_tags = 10
        self.monitored_tags: List[str] = []
        self.last_values: Dict[str, Any] = {}
        self.update_counts: Dict[str, int] = {}
        
        self._init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_tag_values)
        self.refresh_timer.start(1000)  # Refresh every second
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Control panel
        control_group = QGroupBox("Monitor Controls")
        control_layout = QHBoxLayout()
        
        # Number of tags selector
        control_layout.addWidget(QLabel("Number of Tags:"))
        self.tag_count_spin = QSpinBox()
        self.tag_count_spin.setMinimum(1)
        self.tag_count_spin.setMaximum(100)
        self.tag_count_spin.setValue(10)
        self.tag_count_spin.valueChanged.connect(self._on_tag_count_changed)
        control_layout.addWidget(self.tag_count_spin)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Now")
        self.refresh_btn.clicked.connect(self._refresh_tag_values)
        control_layout.addWidget(self.refresh_btn)
        
        # Auto-refresh toggle
        self.auto_refresh_btn = QPushButton("Stop Auto-Refresh")
        self.auto_refresh_btn.setCheckable(True)
        self.auto_refresh_btn.clicked.connect(self._toggle_auto_refresh)
        control_layout.addWidget(self.auto_refresh_btn)
        
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Status info
        info_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Waiting for data...")
        self.last_update_label = QLabel("Last Update: N/A")
        info_layout.addWidget(self.status_label)
        info_layout.addWidget(self.last_update_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Tag table
        self.tag_table = QTableWidget()
        self.tag_table.setColumnCount(6)
        self.tag_table.setHorizontalHeaderLabels([
            "Tag ID", "Tag Name", "Current Value", "Unit", 
            "Last Update", "Update Count"
        ])
        
        # Set column widths
        header = self.tag_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.tag_table.setAlternatingRowColors(True)
        layout.addWidget(self.tag_table)
    
    def set_ndh_service(self, ndh_service: NDHService):
        """Set NDH service"""
        self.ndh_service = ndh_service
        self._update_monitored_tags()
    
    def set_tsdb(self, tsdb: ITSDB):
        """Set TSDB"""
        self.tsdb = tsdb
    
    def _on_tag_count_changed(self, value: int):
        """Handle tag count change"""
        self.max_tags = value
        self._update_monitored_tags()
        self._refresh_tag_values()
    
    def _toggle_auto_refresh(self, checked: bool):
        """Toggle auto-refresh"""
        if checked:
            self.refresh_timer.stop()
            self.auto_refresh_btn.setText("Start Auto-Refresh")
        else:
            self.refresh_timer.start(1000)
            self.auto_refresh_btn.setText("Stop Auto-Refresh")
    
    def _update_monitored_tags(self):
        """Update the list of monitored tags"""
        if not self.ndh_service:
            self.monitored_tags = []
            return
        
        # Get all tag servants
        all_tag_servants = self.ndh_service.get_all_tag_servants()
        
        # Select up to max_tags
        self.monitored_tags = []
        for tag_servant in all_tag_servants[:self.max_tags]:
            # Create a unique tag ID
            tag_id = f"{tag_servant.asset_instance_id}_{tag_servant.tag_definition.tag_id}"
            self.monitored_tags.append(tag_id)
            
            # Initialize tracking
            if tag_id not in self.update_counts:
                self.update_counts[tag_id] = 0
        
        # Update table row count
        self.tag_table.setRowCount(len(self.monitored_tags))
        
        # Update status
        self.status_label.setText(f"Status: Monitoring {len(self.monitored_tags)} tags")
    
    def _refresh_tag_values(self):
        """Refresh tag values from TSDB"""
        if not self.tsdb or not self.ndh_service:
            return
        
        if not self.monitored_tags:
            self._update_monitored_tags()
            if not self.monitored_tags:
                return
        
        # Get all tag servants for lookup
        all_tag_servants = self.ndh_service.get_all_tag_servants()
        tag_servant_map = {}
        for tag_servant in all_tag_servants:
            tag_id = f"{tag_servant.asset_instance_id}_{tag_servant.tag_definition.tag_id}"
            tag_servant_map[tag_id] = tag_servant
        
        # Query TSDB for each monitored tag
        current_time = datetime.utcnow()
        time_window = timedelta(seconds=5)  # Look back 5 seconds
        
        for row, tag_id in enumerate(self.monitored_tags):
            if tag_id not in tag_servant_map:
                continue
            
            tag_servant = tag_servant_map[tag_id]
            
            try:
                # Query TSDB for recent values
                start_time = current_time - time_window
                results = self.tsdb.query_tag_values(
                    tag_id=tag_id,
                    start_time=start_time,
                    end_time=current_time
                )
                
                # Get the most recent value
                if results:
                    latest = results[-1]
                    value = latest.value
                    timestamp = latest.timestamp
                    
                    # Check if value changed
                    if tag_id not in self.last_values or self.last_values[tag_id] != value:
                        self.last_values[tag_id] = value
                        self.update_counts[tag_id] = self.update_counts.get(tag_id, 0) + 1
                else:
                    # No data in TSDB, get from servant directly
                    value = tag_servant.get_value()
                    timestamp = datetime.utcnow().isoformat() + "Z"
                    
                    if value is not None:
                        if tag_id not in self.last_values or self.last_values[tag_id] != value:
                            self.last_values[tag_id] = value
                            self.update_counts[tag_id] = self.update_counts.get(tag_id, 0) + 1
                
                # Update table
                self._update_table_row(
                    row, 
                    tag_id,
                    tag_servant.tag_definition.name,
                    value,
                    tag_servant.tag_definition.unit or "",
                    timestamp,
                    self.update_counts.get(tag_id, 0)
                )
                
            except Exception as e:
                print(f"Error querying tag {tag_id}: {e}")
                self._update_table_row(
                    row,
                    tag_id,
                    tag_servant.tag_definition.name,
                    "Error",
                    "",
                    "N/A",
                    self.update_counts.get(tag_id, 0)
                )
        
        # Update last update time
        self.last_update_label.setText(
            f"Last Update: {datetime.now().strftime('%H:%M:%S')}"
        )
    
    def _update_table_row(self, row: int, tag_id: str, tag_name: str, 
                          value: Any, unit: str, timestamp: str, update_count: int):
        """Update a single table row"""
        # Tag ID
        id_item = QTableWidgetItem(tag_id)
        id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
        self.tag_table.setItem(row, 0, id_item)
        
        # Tag Name
        name_item = QTableWidgetItem(tag_name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        self.tag_table.setItem(row, 1, name_item)
        
        # Current Value
        value_str = str(value) if value is not None else "N/A"
        value_item = QTableWidgetItem(value_str)
        value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
        
        # Color code based on value type
        if value == "Error":
            value_item.setBackground(QColor(255, 200, 200))  # Light red
        elif value is not None and value != "N/A":
            value_item.setBackground(QColor(200, 255, 200))  # Light green
        
        self.tag_table.setItem(row, 2, value_item)
        
        # Unit
        unit_item = QTableWidgetItem(unit)
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
        self.tag_table.setItem(row, 3, unit_item)
        
        # Last Update
        if isinstance(timestamp, str):
            # Parse ISO format timestamp
            try:
                if timestamp.endswith('Z'):
                    timestamp = timestamp[:-1]
                dt = datetime.fromisoformat(timestamp)
                timestamp_str = dt.strftime('%H:%M:%S')
            except:
                timestamp_str = str(timestamp)
        else:
            timestamp_str = str(timestamp)
        
        timestamp_item = QTableWidgetItem(timestamp_str)
        timestamp_item.setFlags(timestamp_item.flags() & ~Qt.ItemIsEditable)
        self.tag_table.setItem(row, 4, timestamp_item)
        
        # Update Count
        count_item = QTableWidgetItem(str(update_count))
        count_item.setFlags(count_item.flags() & ~Qt.ItemIsEditable)
        self.tag_table.setItem(row, 5, count_item)

