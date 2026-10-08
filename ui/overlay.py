"""Floating recording indicator overlay."""
from __future__ import annotations

import time
from typing import Callable, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class RecordingOverlay(QWidget):
    """
    Floating, non-intrusive HUD widget displayed during recording.
    Stays on top and does not steal focus.
    """

    def __init__(
        self,
        on_stop_requested: Optional[Callable[[], None]] = None,
        on_pause_toggle: Optional[Callable[[], None]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(
            parent,
            Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowDoesNotAcceptFocus,
        )

        self.on_stop_requested = on_stop_requested
        self.on_pause_toggle = on_pause_toggle

        self.start_time: float = time.time()
        self.action_count: int = 0
        self.is_paused: bool = False

        self._init_ui()

        # Update timer (1 second interval)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update_time)

    def _init_ui(self) -> None:
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setStyleSheet(
            """
            QWidget {
                background-color: rgba(18, 20, 28, 230);
                border: 1px solid #dc2626;
                border-radius: 8px;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel {
                border: none;
                background: transparent;
            }
            QPushButton {
                background-color: #242938;
                border: 1px solid #3d4660;
                border-radius: 4px;
                color: #e2e8f0;
                padding: 3px 8px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #31384d;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)

        header_layout = QHBoxLayout()
        self.status_label = QLabel("● RECORDING")
        self.status_label.setStyleSheet("color: #ef4444; font-weight: 800; font-size: 12px;")
        header_layout.addWidget(self.status_label)

        self.time_label = QLabel("00:00")
        self.time_label.setStyleSheet("color: #94a3b8; font-weight: 600; font-size: 12px;")
        header_layout.addWidget(self.time_label, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header_layout)

        info_layout = QHBoxLayout()
        self.count_label = QLabel("Actions: 0")
        self.count_label.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 12px;")
        info_layout.addWidget(self.count_label)

        hint_label = QLabel("(F9 to Stop)")
        hint_label.setStyleSheet("color: #64748b; font-size: 10px;")
        info_layout.addWidget(hint_label, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(info_layout)

        # Reposition to top-right
        self.resize(190, 68)
        self.move(20, 20)

    def start_overlay(self) -> None:
        """Reset and display the overlay."""
        self.start_time = time.time()
        self.action_count = 0
        self.is_paused = False
        self.status_label.setText("● RECORDING")
        self.status_label.setStyleSheet("color: #ef4444; font-weight: 800; font-size: 12px;")
        self.count_label.setText("Actions: 0")
        self.time_label.setText("00:00")
        self.timer.start(1000)
        self.show()

    def stop_overlay(self) -> None:
        """Stop and hide the overlay."""
        self.timer.stop()
        self.hide()

    def set_action_count(self, count: int) -> None:
        self.action_count = count
        self.count_label.setText(f"Actions: {count}")

    def set_paused(self, paused: bool) -> None:
        self.is_paused = paused
        if paused:
            self.status_label.setText("❚❚ PAUSED")
            self.status_label.setStyleSheet("color: #f59e0b; font-weight: 800; font-size: 12px;")
        else:
            self.status_label.setText("● RECORDING")
            self.status_label.setStyleSheet("color: #ef4444; font-weight: 800; font-size: 12px;")

    def _update_time(self) -> None:
        if not self.is_paused:
            elapsed = int(time.time() - self.start_time)
            mins = elapsed // 60
            secs = elapsed % 60
            self.time_label.setText(f"{mins:02d}:{secs:02d}")
