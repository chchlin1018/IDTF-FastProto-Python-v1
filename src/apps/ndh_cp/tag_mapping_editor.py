from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit, QHeaderView, QMessageBox, QDialog, QFormLayout
from PySide6.QtCore import Signal, Qt
from typing import Optional, List, Dict, Any

from ...core.runtime.mapping_svc import MappingService, TagMapping

class TagMappingDialog(QDialog):
    def __init__(self, mapping: Optional[TagMapping] = None, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Tag Mapping" if mapping else "Add Tag Mapping")
        self.mapping = mapping
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.tag_id_input = QLineEdit(self.mapping.tag_id if self.mapping else "")
        self.tag_id_input.setPlaceholderText("Enter internal Tag ID (UUIDv7)")
        layout.addRow("Internal Tag ID:", self.tag_id_input)

        self.external_source_input = QLineEdit(self.mapping.external_source if self.mapping else "")
        self.external_source_input.setPlaceholderText("e.g., AVEVA, OPC-UA, MQTT")
        layout.addRow("External Source:", self.external_source_input)

        self.external_id_input = QLineEdit(self.mapping.external_id if self.mapping else "")
        self.external_id_input.setPlaceholderText("e.g., AVEVA.PISRV.TAGNAME")
        layout.addRow("External ID:", self.external_id_input)

        self.buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        self.buttons_layout.addWidget(self.cancel_button)

        layout.addRow(self.buttons_layout)

    def get_mapping(self) -> Optional[TagMapping]:
        if self.result() == QDialog.Accepted:
            tag_id = self.tag_id_input.text().strip()
            external_source = self.external_source_input.text().strip()
            external_id = self.external_id_input.text().strip()

            if not tag_id or not external_source or not external_id:
                QMessageBox.warning(self, "Input Error", "All fields must be filled.")
                return None
            
            return TagMapping(tag_id=tag_id, external_source=external_source, external_id=external_id)
        return None


class TagMappingEditorWidget(QWidget):
    def __init__(self, mapping_service: MappingService, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.mapping_service = mapping_service
        self._setup_ui()
        self._load_mappings()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        # --- Controls --- #
        control_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Mapping")
        self.add_button.clicked.connect(self._add_mapping)
        control_layout.addWidget(self.add_button)

        self.edit_button = QPushButton("Edit Mapping")
        self.edit_button.clicked.connect(self._edit_mapping)
        control_layout.addWidget(self.edit_button)

        self.remove_button = QPushButton("Remove Mapping")
        self.remove_button.clicked.connect(self._remove_mapping)
        control_layout.addWidget(self.remove_button)
        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # --- Mapping Table --- #
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(3)
        self.mapping_table.setHorizontalHeaderLabels(["Internal Tag ID", "External Source", "External ID"])
        self.mapping_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.mapping_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.mapping_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.mapping_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.mapping_table)

        self.setLayout(main_layout)

    def _load_mappings(self) -> None:
        self.mapping_table.setRowCount(0)
        mappings = self.mapping_service.get_all_mappings()
        for row, mapping in enumerate(mappings):
            self.mapping_table.insertRow(row)
            self.mapping_table.setItem(row, 0, QTableWidgetItem(mapping.tag_id))
            self.mapping_table.setItem(row, 1, QTableWidgetItem(mapping.external_source))
            self.mapping_table.setItem(row, 2, QTableWidgetItem(mapping.external_id))

    def _add_mapping(self) -> None:
        dialog = TagMappingDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            new_mapping = dialog.get_mapping()
            if new_mapping:
                try:
                    self.mapping_service.add_mapping(new_mapping)
                    self._load_mappings()
                except ValueError as e:
                    QMessageBox.warning(self, "Add Mapping Error", str(e))

    def _edit_mapping(self) -> None:
        selected_rows = self.mapping_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Edit Mapping", "Please select a mapping to edit.")
            return

        row = selected_rows[0].row()
        original_tag_id = self.mapping_table.item(row, 0).text()
        original_source = self.mapping_table.item(row, 1).text()
        original_external_id = self.mapping_table.item(row, 2).text()
        original_mapping = TagMapping(tag_id=original_tag_id, external_source=original_source, external_id=original_external_id)

        dialog = TagMappingDialog(mapping=original_mapping, parent=self)
        if dialog.exec() == QDialog.Accepted:
            updated_mapping = dialog.get_mapping()
            if updated_mapping:
                try:
                    self.mapping_service.update_mapping(original_tag_id, updated_mapping)
                    self._load_mappings()
                except ValueError as e:
                    QMessageBox.warning(self, "Update Mapping Error", str(e))

    def _remove_mapping(self) -> None:
        selected_rows = self.mapping_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Remove Mapping", "Please select a mapping to remove.")
            return

        reply = QMessageBox.question(self, "Remove Mapping", "Are you sure you want to remove the selected mapping?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            row = selected_rows[0].row()
            tag_id_to_remove = self.mapping_table.item(row, 0).text()
            try:
                self.mapping_service.remove_mapping(tag_id_to_remove)
                self._load_mappings()
            except ValueError as e:
                QMessageBox.warning(self, "Remove Mapping Error", str(e))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Demo Mapping Service
    from ...core.tsdb.sqlite_tsdb import SQLiteTSDB
    tsdb_for_mapping = SQLiteTSDB(":memory:")
    mapping_service_demo = MappingService(tsdb_for_mapping)
    mapping_service_demo.add_mapping(TagMapping(tag_id="018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e0f", external_source="AVEVA", external_id="PISRV.TAG1"))
    mapping_service_demo.add_mapping(TagMapping(tag_id="018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e10", external_source="OPC-UA", external_id="ns=1;s=Tag2"))

    window = QWidget()
    layout = QVBoxLayout(window)
    tag_mapping_editor = TagMappingEditorWidget(mapping_service_demo)
    layout.addWidget(tag_mapping_editor)
    window.setWindowTitle("Tag Mapping Editor Demo")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())
