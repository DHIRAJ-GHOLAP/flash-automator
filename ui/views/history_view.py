"""Execution history and audit logs view with CSV export capability."""
from __future__ import annotations

import time
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...storage.project_manager import ProjectManager


class HistoryView(QWidget):
    """View displaying historical execution logs and audit reports."""

    def __init__(self, project_manager: Optional[ProjectManager] = None, parent=None) -> None:
        super().__init__(parent)
        self.project_manager = project_manager or ProjectManager()

        self._init_ui()
        self.refresh_logs()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        page_title = QLabel("Execution History")
        page_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc;")
        page_desc = QLabel("Audit trail of all date iterations, generated files, and execution results.")
        page_desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(page_title)
        title_box.addWidget(page_desc)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Filter combo
        header_layout.addWidget(QLabel("Filter:"))
        self.combo_filter = QComboBox()
        self.combo_filter.addItems(["All Statuses", "SUCCESS", "FAILED", "SKIPPED"])
        self.combo_filter.currentTextChanged.connect(self.refresh_logs)
        header_layout.addWidget(self.combo_filter)

        self.btn_refresh = QPushButton("🔄 Refresh")
        self.btn_refresh.clicked.connect(self.refresh_logs)
        header_layout.addWidget(self.btn_refresh)

        self.btn_export_csv = QPushButton("📥 Export to CSV")
        self.btn_export_csv.setProperty("class", "btn-primary")
        self.btn_export_csv.clicked.connect(self._export_csv)
        header_layout.addWidget(self.btn_export_csv)

        main_layout.addLayout(header_layout)

        # Log Table
        self.table_logs = QTableWidget(0, 7)
        self.table_logs.setHorizontalHeaderLabels([
            "Iteration #",
            "Date Value",
            "Status",
            "Duration",
            "Generated File",
            "Details / Error Message",
            "Execution Timestamp",
        ])
        self.table_logs.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_logs.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_logs.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_logs.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table_logs.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.table_logs.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table_logs.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table_logs.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table_logs)

    def refresh_logs(self) -> None:
        """Fetch logs from SQLite and populate the table."""
        logs = self.project_manager.get_execution_logs(limit=500)
        filter_status = self.combo_filter.currentText()

        self.table_logs.setRowCount(0)

        for log in logs:
            if filter_status != "All Statuses" and log.status != filter_status:
                continue

            row = self.table_logs.rowCount()
            self.table_logs.insertRow(row)

            # Iteration
            item_iter = QTableWidgetItem(f"#{log.iteration:02d}")
            item_iter.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Date
            item_date = QTableWidgetItem(log.date_value)
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Status
            item_status = QTableWidgetItem(log.status)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if log.status == "SUCCESS":
                item_status.setForeground(Qt.GlobalColor.green)
            elif log.status == "FAILED":
                item_status.setForeground(Qt.GlobalColor.red)
            elif log.status == "SKIPPED":
                item_status.setForeground(Qt.GlobalColor.yellow)

            # Duration
            item_dur = QTableWidgetItem(f"{log.duration_sec:.2f}s")
            item_dur.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # File
            item_file = QTableWidgetItem(log.output_file)

            # Details
            item_details = QTableWidgetItem(log.details)

            # Timestamp
            ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(log.created_at))
            item_time = QTableWidgetItem(ts_str)

            self.table_logs.setItem(row, 0, item_iter)
            self.table_logs.setItem(row, 1, item_date)
            self.table_logs.setItem(row, 2, item_status)
            self.table_logs.setItem(row, 3, item_dur)
            self.table_logs.setItem(row, 4, item_file)
            self.table_logs.setItem(row, 5, item_details)
            self.table_logs.setItem(row, 6, item_time)

    def _export_csv(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Execution History", "execution_logs.csv", "CSV Files (*.csv)"
        )
        if file_path:
            self.project_manager.export_logs_to_csv(file_path)
            QMessageBox.information(self, "Export Successful", f"Audit logs exported to:\n{file_path}")
