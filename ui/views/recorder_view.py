"""Recorder view for capturing mouse and keyboard workflows."""
from __future__ import annotations

import time
from typing import Callable, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ...core.actions import Action
from ...core.recorder import ActionRecorder, RecorderState
from ...utils.config import get_config


class RecorderView(QWidget):
    """View managing the recording session with live action feed."""

    def __init__(
        self,
        recorder: ActionRecorder,
        on_recording_finished: Optional[Callable[[list[Action]], None]] = None,
        on_toggle_overlay: Optional[Callable[[bool], None]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.recorder = recorder
        self.on_recording_finished = on_recording_finished
        self.on_toggle_overlay = on_toggle_overlay
        self.config = get_config()

        self.start_timestamp: float = 0.0
        self.recorded_actions: list[Action] = []

        self._init_ui()

        # Connect recorder callbacks
        self.recorder.on_action_added = self._on_action_added
        self.recorder.on_state_changed = self._on_recorder_state_changed

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_timer)

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(18)

        # Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        page_title = QLabel("Workflow Recorder")
        page_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc;")
        page_desc = QLabel("Record human desktop interactions and automatically coalesce keystrokes.")
        page_desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(page_title)
        title_box.addWidget(page_desc)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Status Badge
        self.status_badge = QLabel("IDLE")
        self.status_badge.setStyleSheet(
            "background-color: #1e293b; color: #94a3b8; font-weight: 800; padding: 6px 14px; border-radius: 6px;"
        )
        header_layout.addWidget(self.status_badge)
        main_layout.addLayout(header_layout)

        # Control Strip Card
        strip_card = QFrame()
        strip_card.setProperty("class", "card")
        strip_layout = QHBoxLayout(strip_card)
        strip_layout.setSpacing(12)

        self.btn_record = QPushButton("● Start Recording (F8)")
        self.btn_record.setStyleSheet("background-color: #dc2626; color: #ffffff; font-weight: 700; padding: 10px 20px;")
        self.btn_record.clicked.connect(self._toggle_recording)
        strip_layout.addWidget(self.btn_record)

        self.btn_pause = QPushButton("❚❚ Pause (F10)")
        self.btn_pause.setEnabled(False)
        self.btn_pause.clicked.connect(self._toggle_pause)
        strip_layout.addWidget(self.btn_pause)

        self.btn_stop = QPushButton("■ Stop Recording (F9)")
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_recording)
        strip_layout.addWidget(self.btn_stop)

        self.btn_clear = QPushButton("Clear Feed")
        self.btn_clear.clicked.connect(self._clear_feed)
        strip_layout.addWidget(self.btn_clear)

        strip_layout.addStretch()

        # Stats in strip
        self.lbl_action_count = QLabel("Actions: 0")
        self.lbl_action_count.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 14px;")
        strip_layout.addWidget(self.lbl_action_count)

        self.lbl_elapsed_time = QLabel("Elapsed: 00:00")
        self.lbl_elapsed_time.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 14px;")
        strip_layout.addWidget(self.lbl_elapsed_time)

        main_layout.addWidget(strip_card)

        # Configuration Options Row
        options_layout = QHBoxLayout()
        self.chk_coalesce = QCheckBox("Smart Typing Coalescing (Converts letters into single text block)")
        self.chk_coalesce.setChecked(self.config.coalesce_typing)
        self.chk_coalesce.toggled.connect(self._on_coalesce_toggled)
        options_layout.addWidget(self.chk_coalesce)

        self.chk_mouse_moves = QCheckBox("Record Mouse Movement Trails")
        self.chk_mouse_moves.setChecked(self.config.record_mouse_moves)
        self.chk_mouse_moves.toggled.connect(self._on_mouse_moves_toggled)
        options_layout.addWidget(self.chk_mouse_moves)

        self.chk_overlay = QCheckBox("Show Floating HUD Overlay")
        self.chk_overlay.setChecked(True)
        self.chk_overlay.toggled.connect(self._on_overlay_toggled)
        options_layout.addWidget(self.chk_overlay)

        options_layout.addStretch()
        main_layout.addLayout(options_layout)

        # Live Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["#", "Delay", "Action Type", "Target / Coordinates", "Details"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        main_layout.addWidget(self.table)

        # Bottom Finish / Transfer button
        bottom_layout = QHBoxLayout()
        hint = QLabel("💡 Tip: Record typing a sample date like <b>01/10/2026</b>, then click <i>'Send to Workflow Editor'</i> to turn it into <b>{{STATEMENT_DATE}}</b>.")
        hint.setTextFormat(Qt.TextFormat.RichText)
        hint.setStyleSheet("color: #94a3b8; font-size: 12px;")
        bottom_layout.addWidget(hint)

        bottom_layout.addStretch()

        self.btn_send_to_editor = QPushButton("Transfer Actions to Workflow Editor ➔")
        self.btn_send_to_editor.setProperty("class", "btn-primary")
        self.btn_send_to_editor.clicked.connect(self._transfer_to_editor)
        bottom_layout.addWidget(self.btn_send_to_editor)

        main_layout.addLayout(bottom_layout)

    def _toggle_recording(self) -> None:
        if self.recorder.state == RecorderState.IDLE:
            self.recorded_actions.clear()
            self.table.setRowCount(0)
            self.start_timestamp = time.time()
            self.timer.start(1000)
            self.recorder.start()
            if self.on_toggle_overlay and self.chk_overlay.isChecked():
                self.on_toggle_overlay(True)
        elif self.recorder.state == RecorderState.RECORDING:
            self._stop_recording()

    def _toggle_pause(self) -> None:
        if self.recorder.state == RecorderState.RECORDING:
            self.recorder.pause()
        elif self.recorder.state == RecorderState.PAUSED:
            self.recorder.resume()

    def _stop_recording(self) -> None:
        actions = self.recorder.stop()
        self.recorded_actions = actions
        self.timer.stop()
        if self.on_toggle_overlay:
            self.on_toggle_overlay(False)

    def _clear_feed(self) -> None:
        self.recorded_actions.clear()
        self.table.setRowCount(0)
        self.lbl_action_count.setText("Actions: 0")
        self.lbl_elapsed_time.setText("Elapsed: 00:00")

    def _transfer_to_editor(self) -> None:
        if self.on_recording_finished and self.recorded_actions:
            self.on_recording_finished(self.recorded_actions)

    def _on_action_added(self, action: Action) -> None:
        self.recorded_actions.append(action)
        self.lbl_action_count.setText(f"Actions: {len(self.recorded_actions)}")

        row = self.table.rowCount()
        self.table.insertRow(row)

        item_idx = QTableWidgetItem(f"{row + 1:02d}")
        item_delay = QTableWidgetItem(f"{action.delay_before:.2f}s")
        item_type = QTableWidgetItem(str(action.action_type.value if hasattr(action.action_type, 'value') else action.action_type))

        target = ""
        if action.x is not None and action.y is not None:
            target = f"({action.x}, {action.y})"
        elif action.key:
            target = action.key.upper()
        item_target = QTableWidgetItem(target)

        details = ""
        if action.text:
            details = f"Text: \"{action.text}\""
        item_details = QTableWidgetItem(details)

        self.table.setItem(row, 0, item_idx)
        self.table.setItem(row, 1, item_delay)
        self.table.setItem(row, 2, item_type)
        self.table.setItem(row, 3, item_target)
        self.table.setItem(row, 4, item_details)
        self.table.scrollToBottom()

    def _on_recorder_state_changed(self, state: RecorderState) -> None:
        if state == RecorderState.RECORDING:
            self.status_badge.setText("● RECORDING")
            self.status_badge.setStyleSheet(
                "background-color: #ef4444; color: #ffffff; font-weight: 800; padding: 6px 14px; border-radius: 6px;"
            )
            self.btn_record.setText("■ Stop Recording (F9)")
            self.btn_pause.setEnabled(True)
            self.btn_stop.setEnabled(True)
            self.btn_pause.setText("❚❚ Pause (F10)")
        elif state == RecorderState.PAUSED:
            self.status_badge.setText("❚❚ PAUSED")
            self.status_badge.setStyleSheet(
                "background-color: #f59e0b; color: #ffffff; font-weight: 800; padding: 6px 14px; border-radius: 6px;"
            )
            self.btn_pause.setText("▶ Resume (F11)")
        else:
            self.status_badge.setText("IDLE")
            self.status_badge.setStyleSheet(
                "background-color: #1e293b; color: #94a3b8; font-weight: 800; padding: 6px 14px; border-radius: 6px;"
            )
            self.btn_record.setText("● Start Recording (F8)")
            self.btn_pause.setEnabled(False)
            self.btn_stop.setEnabled(False)

    def _update_timer(self) -> None:
        if self.recorder.state == RecorderState.RECORDING:
            elapsed = int(time.time() - self.start_timestamp)
            mins = elapsed // 60
            secs = elapsed % 60
            self.lbl_elapsed_time.setText(f"Elapsed: {mins:02d}:{secs:02d}")

    def _on_coalesce_toggled(self, checked: bool) -> None:
        self.config.coalesce_typing = checked
        self.config.save()

    def _on_mouse_moves_toggled(self, checked: bool) -> None:
        self.config.record_mouse_moves = checked
        self.config.save()

    def _on_overlay_toggled(self, checked: bool) -> None:
        if self.on_toggle_overlay:
            self.on_toggle_overlay(checked and self.recorder.state == RecorderState.RECORDING)
