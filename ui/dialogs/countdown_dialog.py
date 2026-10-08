"""Pre-execution countdown modal dialog."""
from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class CountdownDialog(QDialog):
    """3-second safety countdown before starting long automations."""

    def __init__(
        self,
        iterations_count: int,
        date_range_str: str,
        dry_run: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Preparing Execution - Flash Automator")
        self.setFixedSize(420, 240)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.remaining_seconds = 3
        self.confirmed = False

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Execution Arming" if not dry_run else "Dry Run Arming")
        title.setStyleSheet("font-size: 16px; font-weight: 800; color: #38bdf8;")
        layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

        msg = QLabel(
            f"Ready to execute <b>{iterations_count} iterations</b>.<br>"
            f"Date Range: {date_range_str}<br>"
            f"<i>Emergency stop: Press F12 at any time.</i>"
        )
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(msg)

        self.countdown_label = QLabel(str(self.remaining_seconds))
        self.countdown_label.setStyleSheet("font-size: 36px; font-weight: 900; color: #f59e0b;")
        layout.addWidget(self.countdown_label, alignment=Qt.AlignmentFlag.AlignCenter)

        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("CANCEL")
        self.btn_cancel.setStyleSheet("background-color: #334155; color: #ffffff;")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_start = QPushButton("START IMMEDIATELY")
        self.btn_start.setProperty("class", "btn-primary")
        self.btn_start.clicked.connect(self._on_start_now)
        btn_layout.addWidget(self.btn_start)

        layout.addLayout(btn_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(1000)

    def _tick(self) -> None:
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self.timer.stop()
            self.confirmed = True
            self.accept()
        else:
            self.countdown_label.setText(str(self.remaining_seconds))

    def _on_start_now(self) -> None:
        self.timer.stop()
        self.confirmed = True
        self.accept()
