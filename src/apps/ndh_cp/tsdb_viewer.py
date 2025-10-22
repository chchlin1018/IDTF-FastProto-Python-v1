from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QComboBox, QPushButton, QLabel, QHeaderView, QDateTimeEdit, QLineEdit, QMessageBox
from PySide6.QtCore import Signal, Qt, QDateTime
from typing import Optional, List, Dict, Any

from ...core.tsdb.interfaces import ITSDB, TagValue

class TSDBViewerWidget(QWidget):
    def __init__(self, tsdb: ITSDB, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.tsdb = tsdb
        self._setup_ui()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        # --- Query Controls --- #
        query_layout = QHBoxLayout()
        query_layout.addWidget(QLabel("Tag ID:"))
        self.tag_id_input = QLineEdit()
        self.tag_id_input.setPlaceholderText("Enter Tag ID")
        query_layout.addWidget(self.tag_id_input)

        query_layout.addWidget(QLabel("Start Time:"))
        self.start_time_edit = QDateTimeEdit(QDateTime.currentDateTime().addDays(-1))
        self.start_time_edit.setCalendarPopup(True)
        query_layout.addWidget(self.start_time_edit)

        query_layout.addWidget(QLabel("End Time:"))
        self.end_time_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.end_time_edit.setCalendarPopup(True)
        query_layout.addWidget(self.end_time_edit)

        self.query_button = QPushButton("Query")
        self.query_button.clicked.connect(self._execute_query)
        query_layout.addWidget(self.query_button)
        query_layout.addStretch()
        main_layout.addLayout(query_layout)

        # --- TSDB Table --- #
        self.tsdb_table = QTableWidget()
        self.tsdb_table.setColumnCount(3)
        self.tsdb_table.setHorizontalHeaderLabels(["Timestamp", "Tag ID", "Value"])
        self.tsdb_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tsdb_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tsdb_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.tsdb_table)

        self.setLayout(main_layout)

    def _execute_query(self) -> None:
        tag_id = self.tag_id_input.text().strip()
        start_timestamp = self.start_time_edit.dateTime().toSecsSinceEpoch()
        end_timestamp = self.end_time_edit.dateTime().toSecsSinceEpoch()

        if not tag_id:
            QMessageBox.warning(self, "Input Error", "Please enter a Tag ID.")
            return

        try:
            tag_values: List[TagValue] = self.tsdb.query_tag_values(tag_id, start_timestamp, end_timestamp)
            self._display_results(tag_values)
        except Exception as e:
            QMessageBox.critical(self, "Query Error", f"Failed to query TSDB: {e}")

    def _display_results(self, tag_values: List[TagValue]) -> None:
        self.tsdb_table.setRowCount(0)
        for row, tag_value in enumerate(tag_values):
            self.tsdb_table.insertRow(row)
            timestamp_item = QTableWidgetItem(QDateTime.fromSecsSinceEpoch(int(tag_value.timestamp)).toString("yyyy-MM-dd hh:mm:ss.zzz"))
            tag_id_item = QTableWidgetItem(tag_value.tag_id)
            value_item = QTableWidgetItem(str(tag_value.value))

            self.tsdb_table.setItem(row, 0, timestamp_item)
            self.tsdb_table.setItem(row, 1, tag_id_item)
            self.tsdb_table.setItem(row, 2, value_item)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Demo TSDB
    tsdb_demo = SQLiteTSDB(":memory:") # Use in-memory DB for demo
    
    # Simulate some data
    import time
    tsdb_demo.write_tag_value(TagValue(tag_id="temp_001", timestamp=time.time() - 3600*24, value=25.0))
    tsdb_demo.write_tag_value(TagValue(tag_id="temp_001", timestamp=time.time() - 3600*12, value=25.5))
    tsdb_demo.write_tag_value(TagValue(tag_id="temp_001", timestamp=time.time() - 3600*6, value=26.0))
    tsdb_demo.write_tag_value(TagValue(tag_id="pressure_001", timestamp=time.time() - 3600*20, value=10.0))
    
    window = QWidget()
    layout = QVBoxLayout(window)
    tsdb_viewer = TSDBViewerWidget(tsdb_demo)
    layout.addWidget(tsdb_viewer)
    window.setWindowTitle("TSDB Viewer Demo")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
