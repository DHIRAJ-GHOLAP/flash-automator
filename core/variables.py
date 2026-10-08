"""Variable engine for resolving template expressions and placeholders in actions."""
from __future__ import annotations

import re
from typing import Any, Mapping

from .actions import Action


class VariableEngine:
    """
    Substitutes {{VARIABLE}} expressions using context dictionaries.
    """

    VAR_PATTERN = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")

    def __init__(self, global_variables: Mapping[str, str] | None = None) -> None:
        self.global_variables: dict[str, str] = dict(global_variables or {})

    def set_global(self, key: str, value: str) -> None:
        self.global_variables[key] = value

    def resolve_text(self, text: str, context: Mapping[str, str] | None = None) -> str:
        """
        Replace all {{VAR_NAME}} in text with values from context or global_variables.
        Leaves unknown variables intact if not found.
        """
        if not text:
            return ""

        merged: dict[str, str] = dict(self.global_variables)
        if context:
            merged.update(context)

        def replacer(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name in merged:
                return str(merged[var_name])
            return match.group(0)

        return self.VAR_PATTERN.sub(replacer, text)

    def resolve_action(self, action: Action, context: Mapping[str, str] | None = None) -> Action:
        """
        Create an evaluated copy of the action with variables substituted
        in text and string metadata fields.
        """
        resolved = action.clone()
        resolved.text = self.resolve_text(action.text, context)

        # Also resolve any string fields in metadata (e.g., filename templates)
        if action.metadata:
            new_metadata: dict[str, Any] = {}
            for k, v in action.metadata.items():
                if isinstance(v, str):
                    new_metadata[k] = self.resolve_text(v, context)
                else:
                    new_metadata[k] = v
            resolved.metadata = new_metadata

        return resolved

    def resolve_actions(
        self, actions: list[Action], context: Mapping[str, str] | None = None
    ) -> list[Action]:
        """Resolve variables across a list of actions."""
        return [self.resolve_action(act, context) for act in actions]

    @staticmethod
    def extract_variables(text: str) -> set[str]:
        """Extract all variable names found in a template string."""
        if not text:
            return set()
        return set(VariableEngine.VAR_PATTERN.findall(text))

    @staticmethod
    def get_supported_builtins() -> list[dict[str, str]]:
        """Return metadata for known standard variables for UI documentation."""
        return [
            {"name": "STATEMENT_DATE", "desc": "Current iteration formatted date (e.g. 01/10/2026)"},
            {"name": "DATE_DD", "desc": "Two-digit day of month (01-31)"},
            {"name": "DATE_MM", "desc": "Two-digit month of year (01-12)"},
            {"name": "DATE_YYYY", "desc": "Four-digit year (e.g. 2026)"},
            {"name": "DATE_YY", "desc": "Two-digit year (e.g. 26)"},
            {"name": "DAY", "desc": "Alias for DATE_DD"},
            {"name": "MONTH", "desc": "Alias for DATE_MM"},
            {"name": "YEAR", "desc": "Alias for DATE_YYYY"},
            {"name": "MONTH_NAME", "desc": "Full month name (e.g. October)"},
            {"name": "MONTH_SHORT", "desc": "Short month name (e.g. Oct)"},
            {"name": "DAY_NAME", "desc": "Full weekday name (e.g. Monday)"},
            {"name": "DAY_SHORT", "desc": "Short weekday name (e.g. Mon)"},
            {"name": "ITERATION", "desc": "Current iteration count (1, 2, ...)"},
            {"name": "COUNTER", "desc": "Current sequence index"},
            {"name": "TOTAL_ITERATIONS", "desc": "Total count of iterations in run"},
        ]
