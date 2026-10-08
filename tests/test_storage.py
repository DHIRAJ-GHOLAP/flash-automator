"""Unit tests for storage and persistence."""
import tempfile
from pathlib import Path
import pytest
from flash_automator.core.actions import Action, ActionType
from flash_automator.core.workflow import Workflow
from flash_automator.storage.database import Database
from flash_automator.storage.models import ExecutionLogRecord
from flash_automator.storage.project_manager import ProjectManager


@pytest.fixture
def temp_pm():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        db = Database(db_path)
        pm = ProjectManager(db)
        yield pm, tmp_dir


def test_project_crud(temp_pm):
    pm, _ = temp_pm
    proj = pm.create_project("Bank Statements", "Daily statement generator")
    assert proj.name == "Bank Statements"

    fetched = pm.get_project(proj.id)
    assert fetched is not None
    assert fetched.name == "Bank Statements"

    projects = pm.list_projects()
    assert len(projects) == 1

    pm.delete_project(proj.id)
    assert pm.get_project(proj.id) is None


def test_workflow_storage(temp_pm):
    pm, _ = temp_pm
    wf = Workflow(name="Oct Statements")
    wf.add_action(Action(action_type=ActionType.CLICK, x=50, y=50))
    wf.add_action(Action(action_type=ActionType.TYPE_TEXT, text="{{STATEMENT_DATE}}"))

    pm.save_workflow(wf)
    loaded = pm.get_workflow(wf.id)
    assert loaded is not None
    assert loaded.name == "Oct Statements"
    assert len(loaded.actions) == 2
    assert loaded.actions[1].text == "{{STATEMENT_DATE}}"


def test_execution_logging_and_csv_export(temp_pm):
    pm, tmp_dir = temp_pm
    rec1 = ExecutionLogRecord(
        iteration=1,
        date_value="01/10/2026",
        status="SUCCESS",
        output_file="Statement_01-10-2026.pdf",
        duration_sec=1.5,
    )
    rec2 = ExecutionLogRecord(
        iteration=2,
        date_value="02/10/2026",
        status="FAILED",
        details="Window timeout",
        duration_sec=2.0,
    )
    pm.log_execution(rec1)
    pm.log_execution(rec2)

    logs = pm.get_execution_logs()
    assert len(logs) == 2

    csv_path = Path(tmp_dir) / "export.csv"
    pm.export_logs_to_csv(csv_path)
    assert csv_path.exists()
    content = csv_path.read_text(encoding="utf-8")
    assert "01/10/2026" in content
    assert "02/10/2026" in content
    assert "FAILED" in content
