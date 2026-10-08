"""Unit tests for high-level iterative workflow execution."""
import datetime
import tempfile
from pathlib import Path
import pytest

from flash_automator.core.actions import Action, ActionType
from flash_automator.core.date_engine import DateEngine, DateEngineConfig, DateRule
from flash_automator.core.executor import WorkflowExecutor
from flash_automator.core.safety import SafetyController
from flash_automator.core.variables import VariableEngine
from flash_automator.core.workflow import Workflow
from flash_automator.storage.database import Database
from flash_automator.storage.project_manager import ProjectManager


@pytest.fixture
def mock_setup():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db = Database(Path(tmp_dir) / "test.db")
        pm = ProjectManager(db)
        safety = SafetyController()
        yield pm, safety


def test_executor_dry_run_full_loop(mock_setup):
    pm, safety = mock_setup
    executor = WorkflowExecutor(safety=safety, project_manager=pm, dry_run=True)

    # Workflow with date typing and template saving
    wf = Workflow(name="Bank Statement Generation")
    wf.add_action(Action(action_type=ActionType.CLICK, x=200, y=150, delay_before=0.01))
    wf.add_action(Action(action_type=ActionType.TYPE_TEXT, text="{{STATEMENT_DATE}}", delay_before=0.01))
    wf.add_action(Action(action_type=ActionType.CLICK, x=300, y=250, delay_before=0.01))

    # Generate 5 days
    start = datetime.date(2026, 10, 1)
    end = datetime.date(2026, 10, 5)
    cfg = DateEngineConfig(start_date=start, end_date=end, rule=DateRule.EVERY_DAY)
    date_engine = DateEngine(cfg)

    recorded_dates = []
    def on_iter_start(idx, total, d_str):
        recorded_dates.append(d_str)

    executor.on_iteration_start = on_iter_start

    stats = executor.run(wf, date_engine)

    assert stats.total_iterations == 5
    assert stats.completed_iterations == 5
    assert stats.failed_iterations == 0
    assert len(recorded_dates) == 5
    assert recorded_dates[0] == "01/10/2026"
    assert recorded_dates[-1] == "05/10/2026"

    # Verify logs stored in SQLite
    logs = pm.get_execution_logs()
    assert len(logs) == 5
    for log in logs:
        assert log.status == "SUCCESS"


def test_executor_emergency_stop(mock_setup):
    pm, safety = mock_setup
    executor = WorkflowExecutor(safety=safety, project_manager=pm, dry_run=True)

    wf = Workflow(name="Aborting Workflow")
    wf.add_action(Action(action_type=ActionType.WAIT, delay_before=0.01))

    # 10 days
    start = datetime.date(2026, 10, 1)
    end = datetime.date(2026, 10, 10)
    cfg = DateEngineConfig(start_date=start, end_date=end)
    date_engine = DateEngine(cfg)

    # Trigger emergency stop after iteration 2
    def on_iter_start(idx, total, d_str):
        if idx == 3:
            safety.trigger_emergency_stop()

    executor.on_iteration_start = on_iter_start
    stats = executor.run(wf, date_engine)

    # Stopped early
    assert stats.completed_iterations == 2
    assert safety.is_stopped() is True
