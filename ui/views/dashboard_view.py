"""Dashboard view presenting overview cards, status, and quick launch actions."""
from __future__ import annotations

from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...core.workflow import Workflow


class DashboardView(QWidget):
    """Modern dashboard summarizing active workflow, date range, and execution progress."""

    def __init__(
        self,
        on_record_clicked: Optional[Callable[[], None]] = None,
        on_run_clicked: Optional[Callable[[], None]] = None,
        on_dry_run_clicked: Optional[Callable[[], None]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.on_record_clicked = on_record_clicked
        self.on_run_clicked = on_run_clicked
        self.on_dry_run_clicked = on_dry_run_clicked

        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(20)

        # Header Title
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        page_title = QLabel("Dashboard")
        page_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc;")
        page_desc = QLabel("Overview of active RPA workflow and batch date automation.")
        page_desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(page_title)
        title_box.addWidget(page_desc)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Quick action buttons
        self.btn_quick_record = QPushButton("● Record Workflow")
        self.btn_quick_record.setStyleSheet("background-color: #dc2626; color: #ffffff; font-weight: 700; padding: 10px 18px;")
        if self.on_record_clicked:
            self.btn_quick_record.clicked.connect(self.on_record_clicked)
        header_layout.addWidget(self.btn_quick_record)

        self.btn_quick_dry_run = QPushButton("🔍 Dry Run")
        self.btn_quick_dry_run.setStyleSheet("background-color: #334155; color: #f1f5f9; font-weight: 700; padding: 10px 18px;")
        if self.on_dry_run_clicked:
            self.btn_quick_dry_run.clicked.connect(self.on_dry_run_clicked)
        header_layout.addWidget(self.btn_quick_dry_run)

        self.btn_quick_run = QPushButton("▶ Run Automation")
        self.btn_quick_run.setProperty("class", "btn-primary")
        self.btn_quick_run.setStyleSheet("font-weight: 700; padding: 10px 22px;")
        if self.on_run_clicked:
            self.btn_quick_run.clicked.connect(self.on_run_clicked)
        header_layout.addWidget(self.btn_quick_run)

        main_layout.addLayout(header_layout)

        # 3 Top Summary Cards
        cards_layout = QGridLayout()
        cards_layout.setSpacing(16)

        # Card 1: Active Workflow
        self.card_workflow = QFrame()
        self.card_workflow.setProperty("class", "card")
        cw_layout = QVBoxLayout(self.card_workflow)
        lbl_w_title = QLabel("ACTIVE WORKFLOW")
        lbl_w_title.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 700;")
        cw_layout.addWidget(lbl_w_title)

        self.lbl_wf_name = QLabel("Bank Statement")
        self.lbl_wf_name.setStyleSheet("color: #38bdf8; font-size: 20px; font-weight: 800; margin-top: 4px;")
        cw_layout.addWidget(self.lbl_wf_name)

        self.lbl_wf_details = QLabel("10 actions recorded • {{STATEMENT_DATE}} active")
        self.lbl_wf_details.setStyleSheet("color: #94a3b8; font-size: 12px;")
        cw_layout.addWidget(self.lbl_wf_details)
        cards_layout.addWidget(self.card_workflow, 0, 0)

        # Card 2: Date Range
        self.card_dates = QFrame()
        self.card_dates.setProperty("class", "card")
        cd_layout = QVBoxLayout(self.card_dates)
        lbl_d_title = QLabel("DATE AUTOMATION RANGE")
        lbl_d_title.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 700;")
        cd_layout.addWidget(lbl_d_title)

        self.lbl_date_range = QLabel("01/10/2026 → 31/10/2026")
        self.lbl_date_range.setStyleSheet("color: #f8fafc; font-size: 20px; font-weight: 800; margin-top: 4px;")
        cd_layout.addWidget(self.lbl_date_range)

        self.lbl_date_rules = QLabel("31 total iterations • Step: 1 day • Format: DD/MM/YYYY")
        self.lbl_date_rules.setStyleSheet("color: #94a3b8; font-size: 12px;")
        cd_layout.addWidget(self.lbl_date_rules)
        cards_layout.addWidget(self.card_dates, 0, 1)

        # Card 3: Execution Status
        self.card_status = QFrame()
        self.card_status.setProperty("class", "card")
        cs_layout = QVBoxLayout(self.card_status)
        lbl_s_title = QLabel("SYSTEM STATUS")
        lbl_s_title.setStyleSheet("color: #64748b; font-size: 11px; font-weight: 700;")
        cs_layout.addWidget(lbl_s_title)

        self.lbl_sys_status = QLabel("Ready")
        self.lbl_sys_status.setStyleSheet("color: #10b981; font-size: 20px; font-weight: 800; margin-top: 4px;")
        cs_layout.addWidget(self.lbl_sys_status)

        self.lbl_failsafe = QLabel("Safety Failsafe: Active (F12 Abort)")
        self.lbl_failsafe.setStyleSheet("color: #94a3b8; font-size: 12px;")
        cs_layout.addWidget(self.lbl_failsafe)
        cards_layout.addWidget(self.card_status, 0, 2)

        main_layout.addLayout(cards_layout)

        # Middle Execution Progress Card
        self.card_progress = QFrame()
        self.card_progress.setProperty("class", "card-highlight")
        prog_layout = QVBoxLayout(self.card_progress)
        prog_layout.setSpacing(12)

        prog_header = QHBoxLayout()
        prog_title = QLabel("Execution Progress")
        prog_title.setStyleSheet("color: #f8fafc; font-size: 16px; font-weight: 700;")
        prog_header.addWidget(prog_title)

        self.lbl_prog_counter = QLabel("0 / 0 Completed (0%)")
        self.lbl_prog_counter.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 13px;")
        prog_header.addWidget(self.lbl_prog_counter, alignment=Qt.AlignmentFlag.AlignRight)
        prog_layout.addLayout(prog_header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        prog_layout.addWidget(self.progress_bar)

        # Detail status row
        det_row = QHBoxLayout()
        self.lbl_current_date = QLabel("Current Date: —")
        self.lbl_current_date.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        det_row.addWidget(self.lbl_current_date)

        self.lbl_current_action = QLabel("Current Action: Idle")
        self.lbl_current_action.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        det_row.addWidget(self.lbl_current_action)

        self.lbl_remaining = QLabel("Remaining: —")
        self.lbl_remaining.setStyleSheet("color: #94a3b8; font-size: 12px;")
        det_row.addWidget(self.lbl_remaining, alignment=Qt.AlignmentFlag.AlignRight)
        prog_layout.addLayout(det_row)

        main_layout.addWidget(self.card_progress)

        main_layout.addStretch()

    def update_workflow_info(self, workflow: Workflow) -> None:
        """Update dashboard card with workflow information."""
        self.lbl_wf_name.setText(workflow.name)
        var_count = len(workflow.get_referenced_variables())
        has_date_var = "STATEMENT_DATE" in workflow.get_referenced_variables()
        var_str = "{{STATEMENT_DATE}} active" if has_date_var else f"{var_count} variables"
        self.lbl_wf_details.setText(f"{len(workflow.actions)} actions recorded • {var_str}")

    def update_date_info(self, start_str: str, end_str: str, total_count: int, format_str: str) -> None:
        """Update dashboard card with date automation settings."""
        self.lbl_date_range.setText(f"{start_str} → {end_str}")
        self.lbl_date_rules.setText(f"{total_count} total iterations • Format: {format_str}")

    def update_progress(
        self,
        current_idx: int,
        total_count: int,
        current_date_str: str,
        current_action_name: str,
        is_running: bool = True,
    ) -> None:
        """Update live execution progress."""
        if total_count <= 0:
            pct = 0
        else:
            pct = int((current_idx / total_count) * 100)

        self.progress_bar.setValue(pct)
        self.lbl_prog_counter.setText(f"{current_idx} / {total_count} Completed ({pct}%)")
        self.lbl_current_date.setText(f"Current Date: <b>{current_date_str}</b>")
        self.lbl_current_action.setText(f"Current Action: <b>{current_action_name}</b>")
        remaining = max(0, total_count - current_idx)
        self.lbl_remaining.setText(f"Remaining: {remaining}")

        if is_running:
            self.lbl_sys_status.setText("Running...")
            self.lbl_sys_status.setStyleSheet("color: #38bdf8; font-size: 20px; font-weight: 800;")
        else:
            self.lbl_sys_status.setText("Completed")
            self.lbl_sys_status.setStyleSheet("color: #10b981; font-size: 20px; font-weight: 800;")
