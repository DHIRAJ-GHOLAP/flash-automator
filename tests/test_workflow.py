"""Unit tests for Workflow management and variable conversion."""
import pytest
from flash_automator.core.actions import Action, ActionType
from flash_automator.core.workflow import Workflow


def test_workflow_actions_manipulation():
    wf = Workflow(name="Bank Test")
    act1 = Action(action_type=ActionType.CLICK, x=100, y=100)
    act2 = Action(action_type=ActionType.TYPE_TEXT, text="01/10/2026")
    act3 = Action(action_type=ActionType.CLICK, x=200, y=200)

    wf.add_action(act1)
    wf.add_action(act2)
    wf.add_action(act3)

    assert len(wf.actions) == 3
    assert wf.actions[1].text == "01/10/2026"

    # Move action
    wf.move_action(0, 2)
    assert wf.actions[0].id == act2.id
    assert wf.actions[2].id == act1.id

    # Duplicate action
    cloned = wf.duplicate_action(act2.id)
    assert cloned is not None
    assert len(wf.actions) == 4

    # Remove action
    assert wf.remove_action(act1.id)
    assert len(wf.actions) == 3


def test_convert_action_to_variable():
    wf = Workflow(name="Statement Export")
    act = Action(action_type=ActionType.TYPE_TEXT, text="01/10/2026")
    wf.add_action(act)

    success = wf.convert_action_to_variable(act.id, "STATEMENT_DATE")
    assert success is True

    converted_act = wf.actions[0]
    assert converted_act.text == "{{STATEMENT_DATE}}"
    assert converted_act.metadata.get("original_recorded_text") == "01/10/2026"

    vars_found = wf.get_referenced_variables()
    assert "STATEMENT_DATE" in vars_found


def test_workflow_json_roundtrip():
    wf = Workflow(name="Roundtrip Test", description="Testing JSON")
    wf.add_action(Action(action_type=ActionType.CLICK, x=300, y=400))
    wf.add_action(Action(action_type=ActionType.TYPE_TEXT, text="{{STATEMENT_DATE}}"))

    json_data = wf.to_json()
    reconstructed = Workflow.from_json(json_data)

    assert reconstructed.name == wf.name
    assert reconstructed.description == wf.description
    assert len(reconstructed.actions) == 2
    assert reconstructed.actions[1].text == "{{STATEMENT_DATE}}"
