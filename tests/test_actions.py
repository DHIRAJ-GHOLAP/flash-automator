"""Unit tests for Action models."""
import pytest
from flash_automator.core.actions import Action, ActionType


def test_action_creation_and_defaults():
    act = Action(action_type=ActionType.CLICK, x=100, y=200, button="left")
    assert act.action_type == ActionType.CLICK
    assert act.x == 100
    assert act.y == 200
    assert act.button == "left"
    assert act.delay_before == 0.2
    assert isinstance(act.id, str)


def test_action_serialization_and_deserialization():
    act = Action(
        action_type=ActionType.TYPE_TEXT,
        text="01/10/2026",
        delay_before=0.5,
        metadata={"target": "input_box"},
    )
    d = act.to_dict()
    assert d["action_type"] == "TYPE_TEXT"
    assert d["text"] == "01/10/2026"
    assert d["metadata"]["target"] == "input_box"

    restored = Action.from_dict(d)
    assert restored.action_type == ActionType.TYPE_TEXT
    assert restored.text == "01/10/2026"
    assert restored.metadata["target"] == "input_box"


def test_action_clone():
    original = Action(action_type=ActionType.HOTKEY, key="ctrl+p")
    cloned = original.clone()
    assert cloned.id != original.id
    assert cloned.action_type == ActionType.HOTKEY
    assert cloned.key == "ctrl+p"


def test_action_display_summary():
    click_act = Action(action_type=ActionType.CLICK, x=500, y=300)
    assert "(500, 300)" in click_act.display_summary()

    type_act = Action(action_type=ActionType.TYPE_TEXT, text="{{STATEMENT_DATE}}")
    assert "{{STATEMENT_DATE}}" in type_act.display_summary()

    hotkey_act = Action(action_type=ActionType.HOTKEY, key="ctrl+p")
    assert "CTRL+P" in hotkey_act.display_summary()
