"""Variables view providing variable inspection, sample evaluation, and documentation."""
from __future__ import annotations

import datetime
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDateEdit,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.date_engine import DateEngine, DateEngineConfig
from ...core.variables import VariableEngine


class VariablesView(QWidget):
    """Exploration and documentation panel for standard and dynamic variables."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._init_ui()
        self._refresh_evaluation()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(16)

        # Header
        title_box = QVBoxLayout()
        page_title = QLabel("Variable Engine & Reference")
        page_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc;")
        page_desc = QLabel("Dynamic placeholders replaced per iteration during automated execution.")
        page_desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(page_title)
        title_box.addWidget(page_desc)
        main_layout.addLayout(title_box)

        # Sample Evaluator Card
        eval_card = QFrame()
        eval_card.setProperty("class", "card")
        ev_layout = QHBoxLayout(eval_card)
        ev_layout.setSpacing(14)

        ev_layout.addWidget(QLabel("<b>Live Evaluation Sample Date:</b>"))
        self.sample_date_edit = QDateEdit()
        self.sample_date_edit.setCalendarPopup(True)
        self.sample_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.sample_date_edit.setDate(QDate(2026, 10, 8))
        self.sample_date_edit.dateChanged.connect(self._refresh_evaluation)
        ev_layout.addWidget(self.sample_date_edit)

        ev_layout.addStretch()
        lbl_hint = QLabel("Select any date above to inspect the rendered variable values below.")
        lbl_hint.setStyleSheet("color: #64748b; font-size: 12px;")
        ev_layout.addWidget(lbl_hint)

        main_layout.addWidget(eval_card)

        # Table of Variables
        self.table_vars = QTableWidget(0, 3)
        self.table_vars.setHorizontalHeaderLabels([
            "Variable Token",
            "Evaluated Value for Sample Date",
            "Description & Typical Usage",
        ])
        self.table_vars.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_vars.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_vars.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table_vars.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table_vars)

    def _refresh_evaluation(self) -> None:
        qd = self.sample_date_edit.date()
        sample_date = datetime.date(qd.year(), qd.month(), qd.day())

        cfg = DateEngineConfig(start_date=sample_date, end_date=sample_date, date_format="DD/MM/YYYY")
        engine = DateEngine(cfg)
        context = engine.build_context_for_date(sample_date, iteration_index=8, total_iterations=31)

        builtins = VariableEngine.get_supported_builtins()

        self.table_vars.setRowCount(0)
        for item in builtins:
            row = self.table_vars.rowCount()
            self.table_vars.insertRow(row)

            token_name = f"{{{{{item['name']}}}}}"
            eval_value = context.get(item["name"], "—")
            desc = item["desc"]

            item_token = QTableWidgetItem(token_name)
            item_token.setForeground(Qt.GlobalColor.cyan)
            item_token.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_val = QTableWidgetItem(eval_value)
            item_val.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            item_desc = QTableWidgetItem(desc)

            self.table_vars.setItem(row, 0, item_token)
            self.table_vars.setItem(row, 1, item_val)
            self.table_vars.setItem(row, 2, item_desc)
