"""
Queue Monitor Widget - Monitor message queues
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTreeWidget, QTreeWidgetItem, QComboBox, QGroupBox
)
from PySide6.QtCore import QTimer, Qt
from typing import Optional

from ...core.queue.interfaces import QueueManager


class QueueMonitorWidget(QWidget):
    """
    Queue Monitor Widget.
    
    Displays:
    - List of all queues
    - Queue sizes
    - Recent messages in each queue
    """
    
    def __init__(self, queue_manager: Optional[QueueManager] = None, parent=None):
        super().__init__(parent)
        self.queue_manager = queue_manager
        self._init_ui()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_queues)
        self.refresh_timer.start(1000)  # Refresh every second
    
    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        
        # Control buttons
        control_group = QGroupBox("Queue Controls")
        control_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_queues)
        control_layout.addWidget(self.refresh_btn)
        
        self.clear_btn = QPushButton("Clear Selected Queue")
        self.clear_btn.clicked.connect(self._clear_selected_queue)
        control_layout.addWidget(self.clear_btn)
        
        control_layout.addStretch()
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Queue selector
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("Select Queue:"))
        self.queue_combo = QComboBox()
        self.queue_combo.currentTextChanged.connect(self._on_queue_selected)
        selector_layout.addWidget(self.queue_combo)
        selector_layout.addStretch()
        layout.addLayout(selector_layout)
        
        # Queue info
        info_layout = QHBoxLayout()
        self.queue_size_label = QLabel("Size: 0")
        info_layout.addWidget(self.queue_size_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
        # Message tree
        self.message_tree = QTreeWidget()
        self.message_tree.setHeaderLabels(["Timestamp", "Message"])
        self.message_tree.setColumnWidth(0, 200)
        layout.addWidget(self.message_tree)
    
    def set_queue_manager(self, queue_manager: QueueManager):
        """Set queue manager"""
        self.queue_manager = queue_manager
        self._refresh_queues()
    
    def _refresh_queues(self):
        """Refresh queue list"""
        if not self.queue_manager:
            return
        
        # Get current selection
        current_queue = self.queue_combo.currentText()
        
        # Update queue list
        self.queue_combo.clear()
        queues = self.queue_manager.list_queues()
        self.queue_combo.addItems(queues)
        
        # Restore selection
        if current_queue and current_queue in queues:
            self.queue_combo.setCurrentText(current_queue)
        elif queues:
            self.queue_combo.setCurrentIndex(0)
        
        # Update queue info
        self._on_queue_selected(self.queue_combo.currentText())
    
    def _on_queue_selected(self, queue_name: str):
        """Handle queue selection"""
        if not self.queue_manager or not queue_name:
            self.queue_size_label.setText("Size: 0")
            self.message_tree.clear()
            return
        
        try:
            queue = self.queue_manager.get_queue(queue_name)
            
            # Update size
            size = queue.size()
            self.queue_size_label.setText(f"Size: {size}")
            
            # Update message history
            self.message_tree.clear()
            history = queue.get_history()
            
            # Show last 100 messages
            for msg in history[-100:]:
                timestamp = msg.get("timestamp", "N/A")
                # Format message for display
                msg_str = str(msg)
                if len(msg_str) > 100:
                    msg_str = msg_str[:100] + "..."
                
                item = QTreeWidgetItem([timestamp, msg_str])
                self.message_tree.addTopLevelItem(item)
            
            # Scroll to bottom
            self.message_tree.scrollToBottom()
        
        except Exception as e:
            print(f"Error loading queue {queue_name}: {e}")
    
    def _clear_selected_queue(self):
        """Clear selected queue"""
        queue_name = self.queue_combo.currentText()
        if not self.queue_manager or not queue_name:
            return
        
        try:
            queue = self.queue_manager.get_queue(queue_name)
            queue.clear()
            self._on_queue_selected(queue_name)
        except Exception as e:
            print(f"Error clearing queue {queue_name}: {e}")

