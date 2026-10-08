"""Dialog for editing action parameters and testing single actions."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from ...core.actions import Action, ActionType


class EditActionDialog(QDialog):
    """Modal dialog to modify action details and insert variables."""

    def __init__(self, action: Action, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Edit Action - Flash Automator")
        self.setFixedSize(480, 420)
        self.action = action.clone()

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Modify Action Properties")
        title.setStyleSheet("font-size: 16px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)

        # Action Type
        self.combo_type = QComboBox()
        for t in ActionType:
            self.combo_type.addItem(t.value, t)
        curr_type = (
            self.action.action_type.value
            if isinstance(self.action.action_type, ActionType)
            else str(self.action.action_type)
        )
        self.combo_type.setCurrentText(curr_type)
        form.addRow("Action Type:", self.combo_type)

        # Pre-delay
        self.spin_delay = QDoubleSpinBox()
        self.spin_delay.setRange(0.0, 60.0)
        self.spin_delay.setSingleStep(0.1)
        self.spin_delay.setValue(self.action.delay_before)
        form.addRow("Delay Before (s):", self.spin_delay)

        # Coordinates
        coord_layout = QHBoxLayout()
        self.spin_x = QSpinBox()
        self.spin_x.setRange(-9999, 9999)
        self.spin_x.setValue(self.action.x if self.action.x is not None else 0)
        coord_layout.addWidget(QLabel("X:"))
        coord_layout.addWidget(self.spin_x)

        self.spin_y = QSpinBox()
        self.spin_y.setRange(-9999, 9999)
        self.spin_y.setValue(self.action.y if self.action.y is not None else 0)
        coord_layout.addWidget(QLabel("Y:"))
        coord_layout.addWidget(self.spin_y)
        form.addRow("Coordinates:", coord_layout)

        # Mouse Button
        self.combo_button = QComboBox()
        self.combo_button.addItems(["left", "right", "middle"])
        self.combo_button.setCurrentText(self.action.button or "left")
        form.addRow("Mouse Button:", self.combo_button)

        # Key (for Hotkey / Key Press)
        self.edit_key = QLineEdit(self.action.key)
        self.edit_key.setPlaceholderText("e.g. ctrl+p, enter, esc")
        form.addRow("Key / Hotkey:", self.edit_key)

        # Text input (for TYPE_TEXT)
        self.edit_text = QLineEdit(self.action.text)
        self.edit_text.setPlaceholderText("Text to type or {{STATEMENT_DATE}}")
        form.addRow("Type Text:", self.edit_text)

        layout.addLayout(form)

        # Quick variable insert chips
        var_chip_layout = QHBoxLayout()
        var_chip_layout.setSpacing(6)
        lbl_chips = QLabel("Insert Variable:")
        lbl_chips.setStyleSheet("color: #94a3b8; font-size: 11px;")
        var_chip_layout.addWidget(lbl_chips)

        for var_name in ["{{STATEMENT_DATE}}", "{{DATE_DD}}", "{{DATE_MM}}", "{{DATE_YYYY}}"]:
            btn = QPushButton(var_name)
            btn.setStyleSheet(
                "background-color: #312e81; color: #a5b4fc; font-size: 10px; padding: 3px 6px; border-radius: 4px;"
            )
            btn.clicked.connect(lambda checked=False, v=var_name: self._insert_var(v))
            var_chip_layout.addWidget(btn)

        var_chip_layout.addStretch()
        layout.addLayout(var_chip_layout)

        layout.addStretch()

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save Changes")
        self.btn_save.setProperty("class", "btn-primary")
        self.btn_save.clicked.connect(self._save_changes)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def _insert_var(self, var_token: str) -> None:
        self.edit_text.insert(var_token)

    def _save_changes(self) -> None:
        self.action.action_type = ActionType(self.combo_type.currentText())
        self.action.delay_before = self.spin_delay.value()
        self.action.x = self.spin_x.value()
        self.action.y = self.spin_y.value()
        self.action.button = self.combo_button.currentText()
        self.action.key = self.edit_key.text().strip()
        self.action.text = self.edit_text.text()
        self.accept()
