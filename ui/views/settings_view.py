"""Settings view for application configuration, safety, and hotkeys."""
from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ...recognition.ocr import OCREngine
from ...utils.config import get_config


class SettingsView(QWidget):
    """View to adjust application preferences, hotkeys, and safety parameters."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.config = get_config()
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(18)

        # Header
        title_box = QVBoxLayout()
        page_title = QLabel("Settings & Safety")
        page_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc;")
        page_desc = QLabel("Configure global keyboard shortcuts, fail-safe corners, and OCR integrations.")
        page_desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(page_title)
        title_box.addWidget(page_desc)
        main_layout.addLayout(title_box)

        # Safety & Playback Card
        card_safety = QFrame()
        card_safety.setProperty("class", "card")
        cs_layout = QVBoxLayout(card_safety)
        cs_title = QLabel("PLAYBACK & SAFETY CONTROLS")
        cs_title.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 800;")
        cs_layout.addWidget(cs_title)

        form_safety = QFormLayout()
        form_safety.setSpacing(10)

        self.chk_failsafe = QCheckBox("Enable PyAutoGUI FailSafe (slam mouse to screen corner to abort)")
        self.chk_failsafe.setChecked(self.config.pyautogui_failsafe)
        form_safety.addRow("Corner FailSafe:", self.chk_failsafe)

        self.spin_countdown = QDoubleSpinBox()
        self.spin_countdown.setRange(0, 10)
        self.spin_countdown.setValue(self.config.countdown_seconds)
        self.spin_countdown.setSuffix(" seconds")
        form_safety.addRow("Pre-run Countdown:", self.spin_countdown)

        self.spin_default_delay = QDoubleSpinBox()
        self.spin_default_delay.setRange(0.01, 10.0)
        self.spin_default_delay.setValue(self.config.default_delay_before)
        self.spin_default_delay.setSuffix(" seconds")
        form_safety.addRow("Default Action Delay:", self.spin_default_delay)

        cs_layout.addLayout(form_safety)
        main_layout.addWidget(card_safety)

        # Hotkeys Card
        card_hotkeys = QFrame()
        card_hotkeys.setProperty("class", "card")
        chk_layout = QVBoxLayout(card_hotkeys)
        chk_title = QLabel("GLOBAL SHORTCUTS")
        chk_title.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 800;")
        chk_layout.addWidget(chk_title)

        form_hotkeys = QFormLayout()
        form_hotkeys.setSpacing(10)

        self.edit_k_record = QLineEdit(self.config.key_record_start.upper())
        form_hotkeys.addRow("Start Recording:", self.edit_k_record)

        self.edit_k_stop = QLineEdit(self.config.key_record_stop.upper())
        form_hotkeys.addRow("Stop Recording:", self.edit_k_stop)

        self.edit_k_pause = QLineEdit(self.config.key_record_pause.upper())
        form_hotkeys.addRow("Pause Recording:", self.edit_k_pause)

        self.edit_k_resume = QLineEdit(self.config.key_record_resume.upper())
        form_hotkeys.addRow("Resume Recording:", self.edit_k_resume)

        self.edit_k_abort = QLineEdit(self.config.key_emergency_stop.upper())
        form_hotkeys.addRow("Emergency Stop Abort:", self.edit_k_abort)

        chk_layout.addLayout(form_hotkeys)
        main_layout.addWidget(card_hotkeys)

        # Vision & OCR Card
        card_ocr = QFrame()
        card_ocr.setProperty("class", "card")
        cocr_layout = QVBoxLayout(card_ocr)
        cocr_title = QLabel("OCR & SCREEN RECOGNITION (OPTIONAL)")
        cocr_title.setStyleSheet("color: #38bdf8; font-size: 12px; font-weight: 800;")
        cocr_layout.addWidget(cocr_title)

        form_ocr = QFormLayout()
        form_ocr.setSpacing(10)

        ocr_row = QHBoxLayout()
        self.edit_tesseract_path = QLineEdit(self.config.tesseract_cmd)
        self.edit_tesseract_path.setPlaceholderText("Path to tesseract binary (optional)")
        ocr_row.addWidget(self.edit_tesseract_path)

        self.btn_browse_tess = QPushButton("Browse...")
        self.btn_browse_tess.clicked.connect(self._browse_tess)
        ocr_row.addWidget(self.btn_browse_tess)

        self.btn_check_ocr = QPushButton("Test Availability")
        self.btn_check_ocr.clicked.connect(self._test_ocr)
        ocr_row.addWidget(self.btn_check_ocr)
        form_ocr.addRow("Tesseract Executable:", ocr_row)

        cocr_layout.addLayout(form_ocr)
        main_layout.addWidget(card_ocr)

        # Save Button
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.btn_save_settings = QPushButton("💾 Save Preferences")
        self.btn_save_settings.setProperty("class", "btn-primary")
        self.btn_save_settings.clicked.connect(self._save_settings)
        btn_box.addWidget(self.btn_save_settings)

        main_layout.addLayout(btn_box)
        main_layout.addStretch()

    def _browse_tess(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Tesseract Executable")
        if path:
            self.edit_tesseract_path.setText(path)

    def _test_ocr(self) -> None:
        self.config.tesseract_cmd = self.edit_tesseract_path.text().strip()
        is_avail = OCREngine.check_availability()
        if is_avail:
            QMessageBox.information(self, "OCR Status", "✓ Tesseract OCR is installed and available!")
        else:
            QMessageBox.warning(
                self,
                "OCR Status",
                "Tesseract binary not detected. OCR features are optional and will remain disabled gracefully.",
            )

    def _save_settings(self) -> None:
        self.config.pyautogui_failsafe = self.chk_failsafe.isChecked()
        self.config.countdown_seconds = int(self.spin_countdown.value())
        self.config.default_delay_before = self.spin_default_delay.value()
        self.config.key_record_start = self.edit_k_record.text().strip().lower()
        self.config.key_record_stop = self.edit_k_stop.text().strip().lower()
        self.config.key_record_pause = self.edit_k_pause.text().strip().lower()
        self.config.key_record_resume = self.edit_k_resume.text().strip().lower()
        self.config.key_emergency_stop = self.edit_k_abort.text().strip().lower()
        self.config.tesseract_cmd = self.edit_tesseract_path.text().strip()
        self.config.save()
        QMessageBox.information(self, "Settings Saved", "Application settings saved successfully.")
