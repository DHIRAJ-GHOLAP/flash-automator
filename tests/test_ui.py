"""Automated tests for PySide6 GUI views and window navigation."""
import os
import pytest
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QApplication

# Ensure headless offscreen platform for Qt tests
os.environ["QT_QPA_PLATFORM"] = "offscreen"

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_main_window_instantiation_and_navigation(qapp):
    from flash_automator.ui.main_window import MainWindow

    window = MainWindow()
    assert window.windowTitle().startswith("Flash Automator")

    # Verify 7 sidebar panels exist in the stack
    assert window.stack.count() == 7

    # Test navigating through all tabs
    for idx in range(7):
        window._switch_to_tab(idx)
        assert window.stack.currentIndex() == idx

    # Test Dashboard view contents
    assert window.view_dashboard.lbl_wf_name.text() == "Bank Statement"
    assert "01/10/2026" in window.view_dashboard.lbl_date_range.text()


def test_editor_view_convert_to_variable(qapp):
    from flash_automator.ui.views.editor_view import WorkflowEditorView
    from flash_automator.core.workflow import Workflow
    from flash_automator.core.actions import Action, ActionType

    editor = WorkflowEditorView()
    wf = Workflow(name="Custom Bank Test")
    wf.add_action(Action(action_type=ActionType.CLICK, x=100, y=100))
    wf.add_action(Action(action_type=ActionType.TYPE_TEXT, text="01/10/2026"))
    editor.set_workflow(wf)

    assert editor.table.rowCount() == 2
    assert editor.table.item(1, 4).text() == "01/10/2026"

    # Convert action #2 directly to variable
    wf.convert_action_to_variable(wf.actions[1].id, "STATEMENT_DATE")
    editor.refresh_table()

    assert editor.table.item(1, 4).text() == "{{STATEMENT_DATE}}"


def test_automation_view_date_sequence_preview(qapp):
    from flash_automator.ui.views.automation_view import AutomationView

    auto_view = AutomationView()
    auto_view.date_start.setDate(QDate(2026, 10, 1))
    auto_view.date_end.setDate(QDate(2026, 10, 31))
    auto_view.refresh_preview()

    # 31 days generated in preview table
    assert auto_view.table_preview.rowCount() == 31
    assert "31 Iterations" in auto_view.lbl_count_badge.text()

    # Check first row has 01/10/2026 and last has 31/10/2026
    first_date = auto_view.table_preview.item(0, 2).text()
    last_date = auto_view.table_preview.item(30, 2).text()
    assert first_date == "01/10/2026"
    assert last_date == "31/10/2026"
