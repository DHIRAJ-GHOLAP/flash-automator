"""Main application window for Flash Automator with sidebar navigation."""
from __future__ import annotations

import time
from typing import Optional

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from .dialogs.countdown_dialog import CountdownDialog
from .dialogs.error_dialog import ErrorRecoveryDialog
from .overlay import RecordingOverlay
from .styles import DARK_THEME_QSS
from .views.automation_view import AutomationView
from .views.dashboard_view import DashboardView
from .views.editor_view import WorkflowEditorView
from .views.history_view import HistoryView
from .views.recorder_view import RecorderView
from .views.settings_view import SettingsView
from .views.variables_view import VariablesView
from ..core.actions import Action
from ..core.date_engine import DateEngine
from ..core.executor import ExecutionStats, WorkflowExecutor
from ..core.recorder import ActionRecorder
from ..core.safety import SafetyController
from ..core.workflow import Workflow
from ..storage.project_manager import ProjectManager
from ..utils.logger import get_logger

logger = get_logger("main_window")


class ExecutionWorker(QObject):
    """Background worker executing iterative workflow without blocking the Qt event loop."""

    iteration_started = Signal(int, int, str)
    action_progress = Signal(int, int, str)
    iteration_completed = Signal(int, str, bool, str)
    execution_completed = Signal(object)
    request_error_decision = Signal(int, str, object, str)

    def __init__(
        self,
        executor: WorkflowExecutor,
        workflow: Workflow,
        date_engine: DateEngine,
    ) -> None:
        super().__init__()
        self.executor = executor
        self.workflow = workflow
        self.date_engine = date_engine
        self._user_decision: str = "STOP"
        self._waiting_decision: bool = False

    def provide_decision(self, decision: str) -> None:
        """Called by main GUI thread with human-in-the-loop decision."""
        self._user_decision = decision
        self._waiting_decision = False

    def _error_resolver(self, idx: int, date_val: str, action: Action, err_msg: str) -> str:
        self._waiting_decision = True
        self.request_error_decision.emit(idx, date_val, action, err_msg)
        while self._waiting_decision and not self.executor.safety.is_stopped():
            time.sleep(0.1)
        return self._user_decision

    def run(self) -> None:
        """Entry point executed on background QThread."""
        self.executor.on_iteration_start = (
            lambda idx, total, d_str: self.iteration_started.emit(idx, total, d_str)
        )
        self.executor.on_action_progress = (
            lambda idx, total, act: self.action_progress.emit(idx, total, act.display_summary())
        )
        self.executor.on_iteration_finish = (
            lambda idx, d_str, success, err: self.iteration_completed.emit(idx, d_str, success, err)
        )
        self.executor.error_resolver = self._error_resolver

        stats = self.executor.run(self.workflow, self.date_engine)
        self.execution_completed.emit(stats)


class MainWindow(QMainWindow):
    """Root application window with sidebar, stacked panels, and orchestration."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Flash Automator - Desktop RPA & Date Macro Engine")
        self.resize(1180, 780)
        self.setMinimumSize(960, 640)

        # Apply dark theme
        self.setStyleSheet(DARK_THEME_QSS)

        # Core subsystems
        self.project_manager = ProjectManager()
        self.safety = SafetyController(on_emergency_stop=self._on_emergency_stop)
        self.recorder = ActionRecorder()

        # Recording overlay HUD
        self.overlay = RecordingOverlay(
            on_stop_requested=self._on_overlay_stop,
            on_pause_toggle=self._on_overlay_pause_toggle,
        )

        # Active state
        self._active_thread: Optional[QThread] = None
        self._active_worker: Optional[ExecutionWorker] = None

        self._init_ui()

    def _init_ui(self) -> None:
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QHBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar
        sidebar = self._create_sidebar()
        root_layout.addWidget(sidebar)

        # 2. Main Stacked Pages
        self.stack = QStackedWidget()

        # Instantiate View panels
        self.view_dashboard = DashboardView(
            on_record_clicked=lambda: self._switch_to_tab(2),
            on_run_clicked=self._start_automation_from_dashboard,
            on_dry_run_clicked=self._start_dry_run_from_dashboard,
        )
        self.view_editor = WorkflowEditorView(
            project_manager=self.project_manager,
            on_workflow_saved=self._on_workflow_saved,
        )
        self.view_recorder = RecorderView(
            recorder=self.recorder,
            on_recording_finished=self._on_recording_transferred,
            on_toggle_overlay=self._toggle_overlay,
        )
        self.view_automation = AutomationView(
            on_run_triggered=self._start_automation,
        )
        self.view_variables = VariablesView()
        self.view_history = HistoryView(project_manager=self.project_manager)
        self.view_settings = SettingsView()

        self.stack.addWidget(self.view_dashboard)   # Index 0
        self.stack.addWidget(self.view_editor)      # Index 1
        self.stack.addWidget(self.view_recorder)    # Index 2
        self.stack.addWidget(self.view_automation)  # Index 3
        self.stack.addWidget(self.view_variables)   # Index 4
        self.stack.addWidget(self.view_history)     # Index 5
        self.stack.addWidget(self.view_settings)    # Index 6

        root_layout.addWidget(self.stack)

        # Update initial dashboard cards
        self._sync_dashboard_info()

    def _create_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("SidebarWidget")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 16)
        layout.setSpacing(4)

        # Brand header
        title = QLabel("⚡ FLASH AUTOMATOR")
        title.setObjectName("AppTitleLabel")
        layout.addWidget(title)

        subtitle = QLabel("Desktop RPA & Date Iteration Engine")
        subtitle.setObjectName("AppSubtitleLabel")
        layout.addWidget(subtitle)

        # Navigation buttons
        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        nav_items = [
            ("⚡  Dashboard", 0),
            ("📋  Workflow Editor", 1),
            ("🔴  Recorder", 2),
            ("📅  Date Automation", 3),
            ("🔤  Variables", 4),
            ("📜  Execution History", 5),
            ("⚙️  Settings & Safety", 6),
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            if index == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, idx=index: self._switch_to_tab(idx))
            self.nav_group.addButton(btn, index)
            layout.addWidget(btn)

        layout.addStretch()

        # Emergency stop indicator in sidebar footer
        safety_box = QFrame()
        safety_box.setStyleSheet(
            "background-color: #261616; border: 1px solid #7f1d1d; border-radius: 6px; margin: 10px; padding: 10px;"
        )
        s_layout = QVBoxLayout(safety_box)
        s_layout.setContentsMargins(6, 6, 6, 6)
        s_layout.setSpacing(2)
        lbl_f12 = QLabel("EMERGENCY ABORT")
        lbl_f12.setStyleSheet("color: #ef4444; font-weight: 800; font-size: 11px;")
        lbl_f12_sub = QLabel("Press F12 anytime to stop")
        lbl_f12_sub.setStyleSheet("color: #94a3b8; font-size: 10px;")
        s_layout.addWidget(lbl_f12)
        s_layout.addWidget(lbl_f12_sub)
        layout.addWidget(safety_box)

        return sidebar

    def _switch_to_tab(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        btn = self.nav_group.button(index)
        if btn and not btn.isChecked():
            btn.setChecked(True)

        if index == 0:
            self._sync_dashboard_info()
        elif index == 5:
            self.view_history.refresh_logs()

    def _sync_dashboard_info(self) -> None:
        """Update dashboard overview cards from editor and automation views."""
        wf = self.view_editor.current_workflow
        self.view_dashboard.update_workflow_info(wf)

        engine = self.view_automation.get_date_engine()
        dates = engine.generate_dates()
        if dates:
            start_str = engine.format_date(dates[0])
            end_str = engine.format_date(dates[-1])
            self.view_dashboard.update_date_info(
                start_str=start_str,
                end_str=end_str,
                total_count=len(dates),
                format_str=self.view_automation.combo_format.currentText(),
            )

    def _on_workflow_saved(self, workflow: Workflow) -> None:
        self._sync_dashboard_info()

    def _on_recording_transferred(self, actions: list[Action]) -> None:
        """When recording finishes, load actions into editor and switch tab."""
        self.view_editor.set_actions_from_recorder(actions)
        self._switch_to_tab(1)
        QMessageBox.information(
            self,
            "Actions Transferred",
            f"Successfully transferred {len(actions)} actions to the Workflow Editor.\n"
            f"Select your typed date action and click 'Convert to {{STATEMENT_DATE}}'!",
        )

    def _toggle_overlay(self, show: bool) -> None:
        if show:
            self.overlay.start_overlay()
        else:
            self.overlay.stop_overlay()

    def _on_overlay_stop(self) -> None:
        self.view_recorder._stop_recording()

    def _on_overlay_pause_toggle(self) -> None:
        self.view_recorder._toggle_pause()

    # --- Execution Launch Controls ---

    def _start_automation_from_dashboard(self) -> None:
        engine = self.view_automation.get_date_engine()
        self._start_automation(engine, dry_run=False)

    def _start_dry_run_from_dashboard(self) -> None:
        engine = self.view_automation.get_date_engine()
        self._start_automation(engine, dry_run=True)

    def _start_automation(self, date_engine: DateEngine, dry_run: bool = False) -> None:
        """Initiate 3-second countdown and start background worker."""
        if self._active_thread and self._active_thread.isRunning():
            QMessageBox.warning(self, "Execution Busy", "An automation workflow is already running!")
            return

        workflow = self.view_editor.current_workflow
        if not workflow.actions:
            QMessageBox.warning(
                self, "Empty Workflow", "The current workflow has no actions to execute. Please record or add actions first."
            )
            return

        dates = date_engine.generate_dates()
        if not dates:
            QMessageBox.warning(
                self, "No Dates", "The configured date range produced 0 dates. Please check start/end date and rules."
            )
            return

        start_str = date_engine.format_date(dates[0])
        end_str = date_engine.format_date(dates[-1])
        range_str = f"{start_str} → {end_str}"

        # 3-Second Safety Countdown Dialog
        dlg = CountdownDialog(
            iterations_count=len(dates),
            date_range_str=range_str,
            dry_run=dry_run,
            parent=self,
        )
        if not dlg.exec() or not dlg.confirmed:
            logger.info("Execution cancelled by user during countdown.")
            return

        # Switch to dashboard so user sees progress
        self._switch_to_tab(0)

        executor = WorkflowExecutor(
            safety=self.safety,
            project_manager=self.project_manager,
            dry_run=dry_run,
        )

        self._active_thread = QThread(self)
        self._active_worker = ExecutionWorker(executor, workflow, date_engine)
        self._active_worker.moveToThread(self._active_thread)

        # Worker signals
        self._active_thread.started.connect(self._active_worker.run)
        self._active_worker.iteration_started.connect(self._on_worker_iter_start)
        self._active_worker.action_progress.connect(self._on_worker_action_progress)
        self._active_worker.iteration_completed.connect(self._on_worker_iter_completed)
        self._active_worker.request_error_decision.connect(self._on_worker_error_request)
        self._active_worker.execution_completed.connect(self._on_worker_finished)

        self._active_thread.start()

    def _on_worker_iter_start(self, idx: int, total: int, date_str: str) -> None:
        self.view_dashboard.update_progress(
            current_idx=idx - 1,
            total_count=total,
            current_date_str=date_str,
            current_action_name="Starting workflow...",
            is_running=True,
        )

    def _on_worker_action_progress(self, act_idx: int, total_acts: int, summary: str) -> None:
        self.view_dashboard.lbl_current_action.setText(f"Step {act_idx}/{total_acts}: <b>{summary}</b>")

    def _on_worker_iter_completed(self, idx: int, date_str: str, success: bool, err_msg: str) -> None:
        engine = self.view_automation.get_date_engine()
        total = len(engine.generate_dates())
        self.view_dashboard.update_progress(
            current_idx=idx,
            total_count=total,
            current_date_str=date_str,
            current_action_name="Iteration finished",
            is_running=True,
        )

    def _on_worker_error_request(self, idx: int, date_val: str, action: Action, err_msg: str) -> None:
        """Prompt user with the Pause on error dialog."""
        dlg = ErrorRecoveryDialog(
            iteration_index=idx,
            date_str=date_val,
            action=action,
            error_reason=err_msg,
            parent=self,
        )
        dlg.exec()
        if self._active_worker:
            self._active_worker.provide_decision(dlg.decision)

    def _on_worker_finished(self, stats: ExecutionStats) -> None:
        if self._active_thread:
            self._active_thread.quit()
            self._active_thread.wait()
            self._active_thread = None
            self._active_worker = None

        self.view_dashboard.update_progress(
            current_idx=stats.completed_iterations,
            total_count=stats.total_iterations,
            current_date_str="Complete",
            current_action_name="All iterations finished",
            is_running=False,
        )
        self.view_history.refresh_logs()

        mode_str = "Dry Run" if stats.is_dry_run else "Automation"
        QMessageBox.information(
            self,
            f"{mode_str} Finished",
            f"{mode_str} completed!\n"
            f"Total: {stats.total_iterations}\n"
            f"Succeeded: {stats.completed_iterations}\n"
            f"Failed: {stats.failed_iterations}\n"
            f"Skipped: {stats.skipped_iterations}",
        )

    def _on_emergency_stop(self) -> None:
        logger.warning("Emergency stop signaled to UI!")
