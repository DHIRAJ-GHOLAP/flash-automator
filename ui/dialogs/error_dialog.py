"""Modal error dialog providing Retry / Skip / Stop recovery actions."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ...core.actions import Action


class ErrorRecoveryDialog(QDialog):
    """
    Pause dialog presented when an action fails or times out.
    Enables human-in-the-loop decisions: RETRY, SKIP THIS DATE, STOP AUTOMATION.
    """

    def __init__(
        self,
        iteration_index: int,
        date_str: str,
        action: Action,
        error_reason: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Automation Paused - Flash Automator")
        self.setFixedSize(500, 320)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.decision: str = "STOP"

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        header = QLabel("⚠️ Automation Paused")
        header.setStyleSheet("font-size: 18px; font-weight: 800; color: #f59e0b;")
        layout.addWidget(header)

        # Card container with details
        card = QFrame()
        card.setStyleSheet(
            "background-color: #1a1e2b; border: 1px solid #2d354a; border-radius: 8px; padding: 12px;"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)

        lbl_date = QLabel(f"<b>Iteration / Date:</b> #{iteration_index} &nbsp;|&nbsp; {date_str}")
        lbl_date.setTextFormat(Qt.TextFormat.RichText)
        lbl_date.setStyleSheet("color: #e2e8f0; font-size: 13px;")
        card_layout.addWidget(lbl_date)

        lbl_action = QLabel(f"<b>Action:</b> {action.display_summary()}")
        lbl_action.setTextFormat(Qt.TextFormat.RichText)
        lbl_action.setStyleSheet("color: #38bdf8; font-size: 13px;")
        card_layout.addWidget(lbl_action)

        lbl_reason = QLabel(f"<b>Reason:</b> <span style='color: #ef4444;'>{error_reason}</span>")
        lbl_reason.setTextFormat(Qt.TextFormat.RichText)
        lbl_reason.setWordWrap(True)
        lbl_reason.setStyleSheet("font-size: 12px;")
        card_layout.addWidget(lbl_reason)

        layout.addWidget(card)

        help_text = QLabel("Choose how to proceed:")
        help_text.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(help_text)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.btn_retry = QPushButton("RETRY")
        self.btn_retry.setStyleSheet("background-color: #2563eb; color: #ffffff; font-weight: 700;")
        self.btn_retry.clicked.connect(self._on_retry)
        btn_layout.addWidget(self.btn_retry)

        self.btn_skip = QPushButton("SKIP THIS DATE")
        self.btn_skip.setStyleSheet("background-color: #d97706; color: #ffffff; font-weight: 700;")
        self.btn_skip.clicked.connect(self._on_skip)
        btn_layout.addWidget(self.btn_skip)

        self.btn_stop = QPushButton("STOP AUTOMATION")
        self.btn_stop.setStyleSheet("background-color: #dc2626; color: #ffffff; font-weight: 700;")
        self.btn_stop.clicked.connect(self._on_stop)
        btn_layout.addWidget(self.btn_stop)

        layout.addLayout(btn_layout)

    def _on_retry(self) -> None:
        self.decision = "RETRY"
        self.accept()

    def _on_skip(self) -> None:
        self.decision = "SKIP"
        self.accept()

    def _on_stop(self) -> None:
        self.decision = "STOP"
        self.reject()
