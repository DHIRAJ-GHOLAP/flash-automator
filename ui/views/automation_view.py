"""Date automation panel for configuring date ranges, rules, and launch controls."""
from __future__ import annotations

import datetime
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.date_engine import DateEngine, DateEngineConfig, DateRule
from ...core.variables import VariableEngine
from ...utils.config import get_config


class AutomationView(QWidget):
    """Configuration panel for date generation rules, batch options, and execution triggers."""

    def __init__(
        self,
        on_run_triggered: Optional[Callable[[DateEngine, bool], None]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.on_run_triggered = on_run_triggered
        self.config = get_config()

        self._init_ui()
        self.refresh_preview()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(16)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        page_title = QLabel("Date Automation")
        page_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc;")
        page_desc = QLabel("Configure independent date sequences, calendar rules, and output templates.")
        page_desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(page_title)
        title_box.addWidget(page_desc)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Run action buttons
        self.btn_dry_run = QPushButton("🔍 Dry Run Mode")
        self.btn_dry_run.setStyleSheet("background-color: #334155; color: #f1f5f9; font-weight: 700; padding: 10px 18px;")
        self.btn_dry_run.clicked.connect(lambda: self._trigger_execution(dry_run=True))
        header_layout.addWidget(self.btn_dry_run)

        self.btn_run = QPushButton("▶ Run Automation")
        self.btn_run.setProperty("class", "btn-primary")
        self.btn_run.setStyleSheet("font-weight: 800; padding: 10px 24px;")
        self.btn_run.clicked.connect(lambda: self._trigger_execution(dry_run=False))
        header_layout.addWidget(self.btn_run)

        main_layout.addLayout(header_layout)

        # Date Rules Config Card
        config_card = QFrame()
        config_card.setProperty("class", "card")
        cfg_layout = QGridLayout(config_card)
        cfg_layout.setSpacing(14)

        # Start Date (default 01/10/2026 for primary use case)
        cfg_layout.addWidget(QLabel("<b>Start Date:</b>"), 0, 0)
        self.date_start = QDateEdit()
        self.date_start.setCalendarPopup(True)
        self.date_start.setDisplayFormat("dd/MM/yyyy")
        self.date_start.setDate(QDate(2026, 10, 1))
        self.date_start.dateChanged.connect(self.refresh_preview)
        cfg_layout.addWidget(self.date_start, 0, 1)

        # End Date (default 31/10/2026)
        cfg_layout.addWidget(QLabel("<b>End Date:</b>"), 0, 2)
        self.date_end = QDateEdit()
        self.date_end.setCalendarPopup(True)
        self.date_end.setDisplayFormat("dd/MM/yyyy")
        self.date_end.setDate(QDate(2026, 10, 31))
        self.date_end.dateChanged.connect(self.refresh_preview)
        cfg_layout.addWidget(self.date_end, 0, 3)

        # Date Format
        cfg_layout.addWidget(QLabel("<b>Date Format:</b>"), 1, 0)
        self.combo_format = QComboBox()
        self.combo_format.addItem("DD/MM/YYYY (with slashes: e.g. 10/06/2023)", "DD/MM/YYYY")
        self.combo_format.addItem("DDMMYYYY (8 digits, no slashes: e.g. 10062023 - For masked fields)", "DDMMYYYY")
        self.combo_format.addItem("DD-MM-YYYY (with hyphens: e.g. 10-06-2023)", "DD-MM-YYYY")
        self.combo_format.addItem("YYYY-MM-DD (ISO standard: e.g. 2023-06-10)", "YYYY-MM-DD")
        self.combo_format.addItem("MM/DD/YYYY (US slashes: e.g. 06/10/2023)", "MM/DD/YYYY")
        self.combo_format.addItem("MM-DD-YYYY (e.g. 06-10-2023)", "MM-DD-YYYY")
        self.combo_format.addItem("DD.MM.YYYY (e.g. 10.06.2023)", "DD.MM.YYYY")
        self.combo_format.addItem("YYYYMMDD (e.g. 20230610)", "YYYYMMDD")
        self.combo_format.currentIndexChanged.connect(self.refresh_preview)
        cfg_layout.addWidget(self.combo_format, 1, 1)

        # Step Days
        cfg_layout.addWidget(QLabel("<b>Step:</b>"), 1, 2)
        self.spin_step = QSpinBox()
        self.spin_step.setRange(1, 365)
        self.spin_step.setValue(1)
        self.spin_step.setSuffix(" day(s)")
        self.spin_step.valueChanged.connect(self.refresh_preview)
        cfg_layout.addWidget(self.spin_step, 1, 3)

        # Date Rules
        cfg_layout.addWidget(QLabel("<b>Date Rules:</b>"), 2, 0)
        self.combo_rules = QComboBox()
        self.combo_rules.addItem("Every day", DateRule.EVERY_DAY)
        self.combo_rules.addItem("Weekdays only (Mon-Fri)", DateRule.WEEKDAYS_ONLY)
        self.combo_rules.addItem("Skip Sundays", DateRule.SKIP_SUNDAYS)
        self.combo_rules.addItem("Skip Saturdays", DateRule.SKIP_SATURDAYS)
        self.combo_rules.addItem("Skip Weekends", DateRule.SKIP_WEEKENDS)
        self.combo_rules.currentIndexChanged.connect(self.refresh_preview)
        cfg_layout.addWidget(self.combo_rules, 2, 1)

        # Custom Excluded Dates
        cfg_layout.addWidget(QLabel("<b>Custom Excluded Dates:</b>"), 2, 2)
        self.edit_excluded = QLineEdit()
        self.edit_excluded.setPlaceholderText("e.g. 02/10/2026, 15/10/2026 (comma separated)")
        self.edit_excluded.textChanged.connect(self.refresh_preview)
        cfg_layout.addWidget(self.edit_excluded, 2, 3)

        main_layout.addWidget(config_card)

        # Output & Filename Card
        output_card = QFrame()
        output_card.setProperty("class", "card")
        out_layout = QGridLayout(output_card)
        out_layout.setSpacing(12)

        out_layout.addWidget(QLabel("<b>Output Directory:</b>"), 0, 0)
        dir_box = QHBoxLayout()
        self.edit_output_dir = QLineEdit(self.config.default_output_dir)
        dir_box.addWidget(self.edit_output_dir)
        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self._browse_dir)
        dir_box.addWidget(self.btn_browse)
        out_layout.addLayout(dir_box, 0, 1)

        out_layout.addWidget(QLabel("<b>Filename Template:</b>"), 1, 0)
        self.edit_filename_template = QLineEdit("BankStatement_{{STATEMENT_DATE}}.pdf")
        self.edit_filename_template.textChanged.connect(self.refresh_preview)
        out_layout.addWidget(self.edit_filename_template, 1, 1)

        main_layout.addWidget(output_card)

        # Generated Dates Table Card
        preview_header = QHBoxLayout()
        self.lbl_preview_title = QLabel("Generated Iteration Sequence")
        self.lbl_preview_title.setStyleSheet("font-size: 15px; font-weight: 700; color: #f8fafc;")
        preview_header.addWidget(self.lbl_preview_title)

        self.lbl_count_badge = QLabel("31 Iterations")
        self.lbl_count_badge.setStyleSheet(
            "background-color: #2563eb; color: #ffffff; font-weight: 700; padding: 4px 10px; border-radius: 4px;"
        )
        preview_header.addWidget(self.lbl_count_badge, alignment=Qt.AlignmentFlag.AlignRight)
        main_layout.addLayout(preview_header)

        self.table_preview = QTableWidget(0, 4)
        self.table_preview.setHorizontalHeaderLabels([
            "Iteration #",
            "Day of Week",
            "Resolved {{STATEMENT_DATE}}",
            "Target Output Filename Preview",
        ])
        self.table_preview.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table_preview.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table_preview.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table_preview.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table_preview.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table_preview)

    def _browse_dir(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Output Directory", self.edit_output_dir.text())
        if folder:
            self.edit_output_dir.setText(folder)

    def get_date_engine(self) -> DateEngine:
        """Construct the DateEngine using current UI configurations."""
        qd_start = self.date_start.date()
        qd_end = self.date_end.date()

        start_py = datetime.date(qd_start.year(), qd_start.month(), qd_start.day())
        end_py = datetime.date(qd_end.year(), qd_end.month(), qd_end.day())

        rule = self.combo_rules.currentData() or DateRule.EVERY_DAY
        fmt = self.combo_format.currentData() or self.combo_format.currentText()
        step = self.spin_step.value()

        # Parse excluded dates
        excluded: set[datetime.date] = set()
        raw_exc = self.edit_excluded.text().strip()
        if raw_exc:
            for item in raw_exc.split(","):
                token = item.strip()
                if token:
                    for test_fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
                        try:
                            parsed = datetime.datetime.strptime(token, test_fmt).date()
                            excluded.add(parsed)
                            break
                        except ValueError:
                            pass

        cfg = DateEngineConfig(
            start_date=start_py,
            end_date=end_py,
            date_format=fmt,
            step_days=step,
            rule=rule,
            excluded_dates=excluded,
        )
        return DateEngine(cfg)

    def refresh_preview(self) -> None:
        """Regenerate preview table based on active date parameters."""
        engine = self.get_date_engine()
        contexts = list(engine.iter_contexts())
        total = len(contexts)

        self.lbl_count_badge.setText(f"{total} Iterations")
        self.table_preview.setRowCount(0)

        fn_template = self.edit_filename_template.text()
        var_engine = VariableEngine()

        for idx, ctx in enumerate(contexts, start=1):
            row = self.table_preview.rowCount()
            self.table_preview.insertRow(row)

            # Iteration #
            item_iter = QTableWidgetItem(f"{idx:02d} / {total:02d}")
            item_iter.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Weekday
            item_day = QTableWidgetItem(ctx.get("DAY_NAME", ""))

            # Date value
            date_val = ctx.get("STATEMENT_DATE", "")
            item_date = QTableWidgetItem(date_val)
            item_date.setForeground(Qt.GlobalColor.cyan)

            # Resolved filename
            resolved_fn = var_engine.resolve_text(fn_template, ctx)
            item_fn = QTableWidgetItem(resolved_fn)

            self.table_preview.setItem(row, 0, item_iter)
            self.table_preview.setItem(row, 1, item_day)
            self.table_preview.setItem(row, 2, item_date)
            self.table_preview.setItem(row, 3, item_fn)

    def _trigger_execution(self, dry_run: bool) -> None:
        if self.on_run_triggered:
            engine = self.get_date_engine()
            self.on_run_triggered(engine, dry_run)
