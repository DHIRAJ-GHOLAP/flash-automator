"""Unit tests for the VariableEngine."""
import pytest
from flash_automator.core.actions import Action, ActionType
from flash_automator.core.variables import VariableEngine


def test_resolve_simple_variable():
    engine = VariableEngine()
    context = {"STATEMENT_DATE": "01/10/2026"}
    res = engine.resolve_text("Statement date is {{STATEMENT_DATE}}", context)
    assert res == "Statement date is 01/10/2026"


def test_resolve_multiple_variables():
    engine = VariableEngine()
    context = {
        "DATE_YYYY": "2026",
        "DATE_MM": "10",
        "DATE_DD": "08",
    }
    template = "Statement_{{DATE_YYYY}}_{{DATE_MM}}_{{DATE_DD}}.pdf"
    res = engine.resolve_text(template, context)
    assert res == "Statement_2026_10_08.pdf"


def test_resolve_unmatched_variables():
    engine = VariableEngine()
    context = {"STATEMENT_DATE": "15/10/2026"}
    # Unknown variable remains unchanged
    template = "{{STATEMENT_DATE}}_{{UNKNOWN_VAR}}"
    res = engine.resolve_text(template, context)
    assert res == "15/10/2026_{{UNKNOWN_VAR}}"


def test_resolve_action_text_and_metadata():
    engine = VariableEngine()
    context = {"STATEMENT_DATE": "05/10/2026"}
    action = Action(
        action_type=ActionType.TYPE_TEXT,
        text="{{STATEMENT_DATE}}",
        metadata={"save_as": "Doc_{{STATEMENT_DATE}}.pdf"},
    )
    resolved = engine.resolve_action(action, context)
    assert resolved.text == "05/10/2026"
    assert resolved.metadata["save_as"] == "Doc_05/10/2026.pdf"
    # Original should be untouched
    assert action.text == "{{STATEMENT_DATE}}"


def test_extract_variables():
    text = "Report_{{STATEMENT_DATE}}_{{COUNTER}}_{{USER}}.xlsx"
    extracted = VariableEngine.extract_variables(text)
    assert extracted == {"STATEMENT_DATE", "COUNTER", "USER"}
