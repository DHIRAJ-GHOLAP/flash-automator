"""End-to-End integration test simulating the entire Bank Statement workflow for October 2026."""
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


def test_bank_statement_31_days_e2e():
    """
    Simulates the exact user journey:
    1. Recorded raw workflow with literal date '01/10/2026'
    2. Convert typed date to {{STATEMENT_DATE}}
    3. Convert saved filename to Statement_{{STATEMENT_DATE}}.pdf
    4. Set Date Engine for October 2026 (01/10/2026 - 31/10/2026)
    5. Run workflow 31 times
    6. Verify every single iteration receives the exact expected date and filename
    7. Verify database execution log has all 31 records
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        db = Database(Path(tmp_dir) / "e2e_test.db")
        pm = ProjectManager(db)
        safety = SafetyController()
        executor = WorkflowExecutor(safety=safety, project_manager=pm, dry_run=True)

        # Step 1: Raw recorded workflow
        wf = Workflow(name="Bank Statement Generation E2E")
        act_click_date = Action(action_type=ActionType.CLICK, x=742, y=381, delay_before=0.01)
        act_type_date = Action(action_type=ActionType.TYPE_TEXT, text="01/10/2026", delay_before=0.01)
        act_click_gen = Action(action_type=ActionType.CLICK, x=812, y=450, delay_before=0.01)
        act_hotkey_print = Action(action_type=ActionType.HOTKEY, key="ctrl+p", delay_before=0.01)
        act_type_file = Action(action_type=ActionType.TYPE_TEXT, text="Statement_01/10/2026.pdf", delay_before=0.01)
        act_click_save = Action(action_type=ActionType.CLICK, x=950, y=700, delay_before=0.01)

        wf.add_action(act_click_date)
        wf.add_action(act_type_date)
        wf.add_action(act_click_gen)
        wf.add_action(act_hotkey_print)
        wf.add_action(act_type_file)
        wf.add_action(act_click_save)

        # Step 2: Convert literal date to {{STATEMENT_DATE}}
        assert wf.convert_action_to_variable(act_type_date.id, "STATEMENT_DATE") is True
        assert wf.actions[1].text == "{{STATEMENT_DATE}}"

        # Step 3: Parameterize filename to Statement_{{STATEMENT_DATE}}.pdf
        wf.actions[4].text = "Statement_{{STATEMENT_DATE}}.pdf"

        # Step 4: Configure independent Date Engine for October 2026
        start_date = datetime.date(2026, 10, 1)
        end_date = datetime.date(2026, 10, 31)
        date_cfg = DateEngineConfig(
            start_date=start_date,
            end_date=end_date,
            date_format="DD/MM/YYYY",
            rule=DateRule.EVERY_DAY,
        )
        date_engine = DateEngine(date_cfg)

        dates = date_engine.generate_dates()
        assert len(dates) == 31

        # Track runtime execution events
        executed_dates = []
        action_payloads = []

        def on_iter_start(idx, total, d_str):
            executed_dates.append(d_str)

        def on_act_progress(act_idx, total_acts, act):
            if act.action_type == ActionType.TYPE_TEXT:
                action_payloads.append(act.text)

        executor.on_iteration_start = on_iter_start
        executor.on_action_progress = on_act_progress

        # Step 5: Execute 31 iterations
        stats = executor.run(wf, date_engine)

        # Step 6: Verify results
        assert stats.total_iterations == 31
        assert stats.completed_iterations == 31
        assert stats.failed_iterations == 0
        assert stats.skipped_iterations == 0

        # Verify all 31 dates were executed in chronological order
        assert len(executed_dates) == 31
        assert executed_dates[0] == "01/10/2026"
        assert executed_dates[14] == "15/10/2026"
        assert executed_dates[30] == "31/10/2026"

        # Verify each date substituted the variables accurately
        # Each iteration has 2 TYPE_TEXT actions: date and filename
        assert len(action_payloads) == 31 * 2
        for i in range(31):
            day_str = f"{i + 1:02d}/10/2026"
            date_text = action_payloads[i * 2]
            file_text = action_payloads[i * 2 + 1]
            assert date_text == day_str
            assert file_text == f"Statement_{day_str}.pdf"

        # Step 7: Verify SQLite execution audit logs
        logs = pm.get_execution_logs()
        assert len(logs) == 31
        for log in logs:
            assert log.status == "SUCCESS"
            assert "10/2026" in log.date_value
