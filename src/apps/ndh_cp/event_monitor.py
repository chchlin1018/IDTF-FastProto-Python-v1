from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QPushButton, QLabel, QHeaderView, QSizePolicy, QTextEdit
from PySide6.QtCore import Signal, Qt, QDateTime
from typing import Optional, List, Dict, Any
import json

from ...core.eventbus.interfaces import IEventBus, Event

class EventMonitorWidget(QWidget):
    event_received = Signal(Event)

    def __init__(self, event_bus: IEventBus, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.event_bus = event_bus
        self.events: List[Event] = []
        self.is_paused: bool = False
        self._setup_ui()
        self._subscribe_to_events()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        # --- Control Panel --- #
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Filter by Type:"))
        
        self.event_type_filter = QComboBox()
        self.event_type_filter.addItem("All")
        # Add more event types dynamically later
        self.event_type_filter.currentIndexChanged.connect(self._filter_events)
        control_layout.addWidget(self.event_type_filter)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self._toggle_pause)
        control_layout.addWidget(self.pause_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_events)
        control_layout.addWidget(self.clear_button)
        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # --- Event Table --- #
        self.event_table = QTableWidget()
        self.event_table.setColumnCount(4)
        self.event_table.setHorizontalHeaderLabels(["Timestamp", "Type", "Source", "Payload Summary"])
        self.event_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.event_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.event_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.event_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.event_table.itemSelectionChanged.connect(self._display_event_details)
        main_layout.addWidget(self.event_table)

        # --- Event Details --- #
        self.details_label = QLabel("Event Details:")
        main_layout.addWidget(self.details_label)
        self.event_details_text = QTextEdit()
        self.event_details_text.setReadOnly(True)
        self.event_details_text.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.event_details_text)

        self.setLayout(main_layout)

    def _subscribe_to_events(self) -> None:
        # Subscribe to all events initially
        self.event_bus.subscribe("*", self._on_event_received)
        self.event_received.connect(self._add_event_to_table)

    def _on_event_received(self, event: Event) -> None:
        if not self.is_paused:
            self.event_received.emit(event)

    def _add_event_to_table(self, event: Event) -> None:
        self.events.append(event)
        row_position = self.event_table.rowCount()
        self.event_table.insertRow(row_position)

        timestamp_item = QTableWidgetItem(QDateTime.fromSecsSinceEpoch(int(event.timestamp)).toString("yyyy-MM-dd hh:mm:ss.zzz"))
        type_item = QTableWidgetItem(event.event_type)
        source_item = QTableWidgetItem(event.source)
        payload_summary = json.dumps(event.payload, ensure_ascii=False, indent=2) # Display full payload for now
        payload_item = QTableWidgetItem(payload_summary) # Or a truncated version

        self.event_table.setItem(row_position, 0, timestamp_item)
        self.event_table.setItem(row_position, 1, type_item)
        self.event_table.setItem(row_position, 2, source_item)
        self.event_table.setItem(row_position, 3, payload_item)

        # Update filter combobox if new event type
        if self.event_type_filter.findText(event.event_type) == -1:
            self.event_type_filter.addItem(event.event_type)

    def _filter_events(self) -> None:
        selected_type = self.event_type_filter.currentText()
        self.event_table.setRowCount(0) # Clear table
        for event in self.events:
            if selected_type == "All" or event.event_type == selected_type:
                row_position = self.event_table.rowCount()
                self.event_table.insertRow(row_position)
                timestamp_item = QTableWidgetItem(QDateTime.fromSecsSinceEpoch(int(event.timestamp)).toString("yyyy-MM-dd hh:mm:ss.zzz"))
                type_item = QTableWidgetItem(event.event_type)
                source_item = QTableWidgetItem(event.source)
                payload_summary = json.dumps(event.payload, ensure_ascii=False, indent=2)
                payload_item = QTableWidgetItem(payload_summary)
                self.event_table.setItem(row_position, 0, timestamp_item)
                self.event_table.setItem(row_position, 1, type_item)
                self.event_table.setItem(row_position, 2, source_item)
                self.event_table.setItem(row_position, 3, payload_item)

    def _toggle_pause(self) -> None:
        self.is_paused = not self.is_paused
        self.pause_button.setText("Resume" if self.is_paused else "Pause")

    def _clear_events(self) -> None:
        self.events.clear()
        self.event_table.setRowCount(0)
        self.event_details_text.clear()
        self.event_type_filter.clear()
        self.event_type_filter.addItem("All")

    def _display_event_details(self) -> None:
        selected_rows = self.event_table.selectionModel().selectedRows()
        if selected_rows:
            row = selected_rows[0].row()
            payload_text = self.event_table.item(row, 3).text()
            self.event_details_text.setText(payload_text)
        else:
            self.event_details_text.clear()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Demo Event Bus
    event_bus_demo = InMemoryEventBus()
    
    # Simulate some events
    import time
    from threading import Thread
    
    def simulate_events():
        event_bus_demo.publish(Event(event_type="TagValueChanged", source="Sensor1", payload={"tag_id": "temp_001", "value": 25.5}))
        time.sleep(0.5)
        event_bus_demo.publish(Event(event_type="AlarmRaised", source="System", payload={"alarm_id": "high_temp", "level": "critical"}))
        time.sleep(1)
        event_bus_demo.publish(Event(event_type="TagValueChanged", source="Sensor2", payload={"tag_id": "pressure_001", "value": 10.2}))
        time.sleep(0.3)
        event_bus_demo.publish(Event(event_type="TagValueChanged", source="Sensor1", payload={"tag_id": "temp_001", "value": 26.0}))
        time.sleep(0.7)
        event_bus_demo.publish(Event(event_type="InstanceCreated", source="FDL", payload={"instance_id": "pump_001", "asset_id": "asset_pump_A"}))
    
    event_thread = Thread(target=simulate_events)
    event_thread.daemon = True
    event_thread.start()

    window = QWidget()
    layout = QVBoxLayout(window)
    event_monitor = EventMonitorWidget(event_bus_demo)
    layout.addWidget(event_monitor)
    window.setWindowTitle("Event Monitor Demo")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
