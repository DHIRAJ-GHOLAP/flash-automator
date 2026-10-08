"""Workflow timeline editor with 'Convert to Variable' capability."""
from __future__ import annotations

import time
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..dialogs.edit_action_dialog import EditActionDialog
from ...core.actions import Action, ActionType
from ...core.player import ActionPlayer
from ...core.safety import SafetyController
from ...core.workflow import Workflow
from ...storage.project_manager import ProjectManager


class WorkflowEditorView(QWidget):
    """Interactive visual timeline editor for actions and variable assignments."""

    def __init__(
        self,
        project_manager: Optional[ProjectManager] = None,
        on_workflow_saved: Optional[Callable[[Workflow], None]] = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.project_manager = project_manager or ProjectManager()
        self.on_workflow_saved = on_workflow_saved

        self.current_workflow = Workflow(name="Bank Statement")
        self._load_sample_template()

        self._init_ui()
        self.refresh_table()

    def _load_sample_template(self) -> None:
        """Initialize with a sample bank statement workflow if empty."""
        if not self.current_workflow.actions:
            self.current_workflow.actions = [
                Action(action_type=ActionType.CLICK, x=742, y=381, delay_before=0.35),
                Action(action_type=ActionType.TYPE_TEXT, text="{{STATEMENT_DATE}}", delay_before=0.5),
                Action(action_type=ActionType.CLICK, x=812, y=450, delay_before=0.35),
                Action(action_type=ActionType.WAIT, delay_before=2.0),
                Action(action_type=ActionType.CLICK, x=920, y=620, delay_before=0.35),
                Action(action_type=ActionType.WAIT, delay_before=3.0),
                Action(action_type=ActionType.HOTKEY, key="ctrl+p", delay_before=0.5),
                Action(action_type=ActionType.WAIT, delay_before=2.0),
                Action(action_type=ActionType.TYPE_TEXT, text="Statement_{{STATEMENT_DATE}}.pdf", delay_before=0.5),
                Action(action_type=ActionType.CLICK, x=950, y=700, delay_before=0.5),
            ]

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(16)

        # Header with workflow name and file actions
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        page_title = QLabel("Workflow Editor")
        page_title.setStyleSheet("font-size: 24px; font-weight: 800; color: #f8fafc;")
        page_desc = QLabel("Edit recorded steps, reorder timeline, and convert typed values to variables.")
        page_desc.setStyleSheet("color: #94a3b8; font-size: 13px;")
        title_box.addWidget(page_title)
        title_box.addWidget(page_desc)
        header_layout.addLayout(title_box)

        header_layout.addStretch()

        # Name edit
        header_layout.addWidget(QLabel("Name:"))
        self.edit_wf_name = QLineEdit(self.current_workflow.name)
        self.edit_wf_name.setFixedWidth(200)
        self.edit_wf_name.textChanged.connect(self._on_name_changed)
        header_layout.addWidget(self.edit_wf_name)

        # Save & File buttons
        self.btn_save = QPushButton("💾 Save")
        self.btn_save.setProperty("class", "btn-primary")
        self.btn_save.clicked.connect(self._save_workflow)
        header_layout.addWidget(self.btn_save)

        self.btn_export = QPushButton("📤 Export JSON")
        self.btn_export.clicked.connect(self._export_json)
        header_layout.addWidget(self.btn_export)

        self.btn_import = QPushButton("📥 Import JSON")
        self.btn_import.clicked.connect(self._import_json)
        header_layout.addWidget(self.btn_import)

        main_layout.addLayout(header_layout)

        # Primary Action Toolbar (Convert to Variable is highlighted!)
        toolbar_card = QFrame()
        toolbar_card.setProperty("class", "card")
        tb_layout = QHBoxLayout(toolbar_card)
        tb_layout.setSpacing(10)

        # THE STAR FEATURE: Convert to Variable
        self.btn_convert_var = QPushButton("✨ Convert to {{STATEMENT_DATE}}")
        self.btn_convert_var.setProperty("class", "btn-variable")
        self.btn_convert_var.setStyleSheet(
            "background-color: #7c3aed; color: #ffffff; font-weight: 800; padding: 9px 18px; border-radius: 6px;"
        )
        self.btn_convert_var.setToolTip("Convert the selected text typing action into a dynamic {{STATEMENT_DATE}} variable.")
        self.btn_convert_var.clicked.connect(self._convert_selected_to_variable)
        tb_layout.addWidget(self.btn_convert_var)

        self.btn_edit = QPushButton("✏️ Edit")
        self.btn_edit.clicked.connect(self._edit_selected)
        tb_layout.addWidget(self.btn_edit)

        self.btn_add_wait = QPushButton("⏱ Add Wait")
        self.btn_add_wait.clicked.connect(self._add_wait_action)
        tb_layout.addWidget(self.btn_add_wait)

        self.btn_duplicate = QPushButton("📋 Duplicate")
        self.btn_duplicate.clicked.connect(self._duplicate_selected)
        tb_layout.addWidget(self.btn_duplicate)

        self.btn_move_up = QPushButton("⬆️ Up")
        self.btn_move_up.clicked.connect(self._move_up)
        tb_layout.addWidget(self.btn_move_up)

        self.btn_move_down = QPushButton("⬇️ Down")
        self.btn_move_down.clicked.connect(self._move_down)
        tb_layout.addWidget(self.btn_move_down)

        self.btn_test = QPushButton("🧪 Test Action")
        self.btn_test.clicked.connect(self._test_selected_action)
        tb_layout.addWidget(self.btn_test)

        self.btn_delete = QPushButton("🗑️ Delete")
        self.btn_delete.setStyleSheet("background-color: #7f1d1d; color: #fca5a5;")
        self.btn_delete.clicked.connect(self._delete_selected)
        tb_layout.addWidget(self.btn_delete)

        tb_layout.addStretch()

        self.lbl_step_count = QLabel("10 Steps")
        self.lbl_step_count.setStyleSheet("color: #38bdf8; font-weight: 700; font-size: 13px;")
        tb_layout.addWidget(self.lbl_step_count)

        main_layout.addWidget(toolbar_card)

        # Timeline Table
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["#", "Delay", "Action Type", "Target / Coords", "Text / Variable Expression"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.itemDoubleClicked.connect(lambda item: self._edit_selected())
        main_layout.addWidget(self.table)

    def set_workflow(self, workflow: Workflow) -> None:
        """Load an existing workflow into the editor."""
        self.current_workflow = workflow
        self.edit_wf_name.setText(workflow.name)
        self.refresh_table()

    def set_actions_from_recorder(self, actions: list[Action]) -> None:
        """Populate editor with actions captured by the recorder."""
        self.current_workflow.actions = actions
        self.refresh_table()

    def refresh_table(self) -> None:
        """Reload the table from the current workflow action list."""
        self.table.setRowCount(0)
        actions = self.current_workflow.actions
        self.lbl_step_count.setText(f"{len(actions)} Steps")

        for idx, act in enumerate(actions, start=1):
            row = self.table.rowCount()
            self.table.insertRow(row)

            # Column 0: Index
            item_idx = QTableWidgetItem(f"{idx:02d}")
            item_idx.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Column 1: Delay
            item_delay = QTableWidgetItem(f"{act.delay_before:.2f}s")
            item_delay.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            # Column 2: Action Type
            act_type_str = act.action_type.value if hasattr(act.action_type, "value") else str(act.action_type)
            item_type = QTableWidgetItem(act_type_str)

            # Column 3: Target
            target = ""
            if act.x is not None and act.y is not None:
                target = f"({act.x}, {act.y}) [{act.button}]"
            elif act.key:
                target = act.key.upper()
            item_target = QTableWidgetItem(target)

            # Column 4: Text / Variable
            item_text = QTableWidgetItem(act.text)
            if "{{" in act.text and "}}" in act.text:
                item_text.setForeground(Qt.GlobalColor.cyan)

            self.table.setItem(row, 0, item_idx)
            self.table.setItem(row, 1, item_delay)
            self.table.setItem(row, 2, item_type)
            self.table.setItem(row, 3, item_target)
            self.table.setItem(row, 4, item_text)

    def _get_selected_index(self) -> Optional[int]:
        selected = self.table.selectedItems()
        if not selected:
            return None
        return selected[0].row()

    def _convert_selected_to_variable(self) -> None:
        """Convert selected action's literal text into {{STATEMENT_DATE}}."""
        idx = self._get_selected_index()
        if idx is None or idx >= len(self.current_workflow.actions):
            QMessageBox.information(self, "Selection Required", "Please select an action in the timeline first.")
            return

        action = self.current_workflow.actions[idx]

        # Let user confirm or customize variable name
        var_name, ok = QInputDialog.getText(
            self,
            "Convert to Variable",
            "Variable token name:",
            QLineEdit.EchoMode.Normal,
            "STATEMENT_DATE",
        )
        if not ok or not var_name.strip():
            return

        var_name = var_name.strip().upper()
        self.current_workflow.convert_action_to_variable(action.id, var_name)
        self.refresh_table()
        self.table.selectRow(idx)
        QMessageBox.information(
            self,
            "Variable Converted",
            f"Action #{idx + 1} converted to {{{{{var_name}}}}}.\n"
            f"At runtime, this placeholder will be dynamically replaced for each date iteration.",
        )

    def _edit_selected(self) -> None:
        idx = self._get_selected_index()
        if idx is None or idx >= len(self.current_workflow.actions):
            return

        act = self.current_workflow.actions[idx]
        dlg = EditActionDialog(act, self)
        if dlg.exec():
            self.current_workflow.actions[idx] = dlg.action
            self.refresh_table()
            self.table.selectRow(idx)

    def _add_wait_action(self) -> None:
        idx = self._get_selected_index()
        insert_at = (idx + 1) if idx is not None else len(self.current_workflow.actions)
        new_wait = Action(action_type=ActionType.WAIT, delay_before=2.0)
        self.current_workflow.add_action(new_wait, index=insert_at)
        self.refresh_table()
        self.table.selectRow(insert_at)

    def _duplicate_selected(self) -> None:
        idx = self._get_selected_index()
        if idx is None:
            return
        act_id = self.current_workflow.actions[idx].id
        self.current_workflow.duplicate_action(act_id)
        self.refresh_table()
        self.table.selectRow(idx + 1)

    def _delete_selected(self) -> None:
        idx = self._get_selected_index()
        if idx is None:
            return
        act_id = self.current_workflow.actions[idx].id
        self.current_workflow.remove_action(act_id)
        self.refresh_table()

    def _move_up(self) -> None:
        idx = self._get_selected_index()
        if idx is not None and idx > 0:
            self.current_workflow.move_action(idx, idx - 1)
            self.refresh_table()
            self.table.selectRow(idx - 1)

    def _move_down(self) -> None:
        idx = self._get_selected_index()
        if idx is not None and idx < len(self.current_workflow.actions) - 1:
            self.current_workflow.move_action(idx, idx + 1)
            self.refresh_table()
            self.table.selectRow(idx + 1)

    def _test_selected_action(self) -> None:
        idx = self._get_selected_index()
        if idx is None:
            return
        act = self.current_workflow.actions[idx]

        # Inform user of 1-second safety delay before testing action
        safety = SafetyController()
        player = ActionPlayer(safety=safety, dry_run=False)
        try:
            time.sleep(1.0)
            player.play_action(act)
        except Exception as e:
            QMessageBox.warning(self, "Action Test", f"Action failed: {e}")

    def _on_name_changed(self, text: str) -> None:
        self.current_workflow.name = text.strip() or "Untitled Workflow"

    def _save_workflow(self) -> None:
        self.current_workflow.name = self.edit_wf_name.text().strip() or "Untitled Workflow"
        self.project_manager.save_workflow(self.current_workflow)
        if self.on_workflow_saved:
            self.on_workflow_saved(self.current_workflow)
        QMessageBox.information(self, "Saved", f"Workflow '{self.current_workflow.name}' saved to database.")

    def _export_json(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Workflow to JSON", f"{self.current_workflow.name}.json", "JSON Files (*.json)"
        )
        if file_path:
            self.project_manager.export_workflow_to_file(self.current_workflow, file_path)
            QMessageBox.information(self, "Exported", f"Exported successfully to:\n{file_path}")

    def _import_json(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Workflow from JSON", "", "JSON Files (*.json)"
        )
        if file_path:
            imported = self.project_manager.import_workflow_from_file(file_path)
            self.set_workflow(imported)
            QMessageBox.information(self, "Imported", f"Loaded workflow: {imported.name}")
