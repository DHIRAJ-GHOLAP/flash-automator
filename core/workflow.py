"""Workflow model containing ordered actions and metadata."""
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Optional

from .actions import Action, ActionType


@dataclass
class Workflow:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = "Untitled Workflow"
    description: str = ""
    actions: list[Action] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def add_action(self, action: Action, index: Optional[int] = None) -> None:
        """Append or insert an action into the workflow."""
        if index is None or index < 0 or index >= len(self.actions):
            self.actions.append(action)
        else:
            self.actions.insert(index, action)
        self.updated_at = time.time()

    def remove_action(self, action_id: str) -> bool:
        """Remove action by its identifier."""
        orig_len = len(self.actions)
        self.actions = [a for a in self.actions if a.id != action_id]
        if len(self.actions) != orig_len:
            self.updated_at = time.time()
            return True
        return False

    def get_action_index(self, action_id: str) -> Optional[int]:
        """Find the 0-based index of an action."""
        for i, a in enumerate(self.actions):
            if a.id == action_id:
                return i
        return None

    def move_action(self, from_index: int, to_index: int) -> bool:
        """Move an action to a new position in the timeline."""
        if 0 <= from_index < len(self.actions) and 0 <= to_index < len(self.actions):
            action = self.actions.pop(from_index)
            self.actions.insert(to_index, action)
            self.updated_at = time.time()
            return True
        return False

    def duplicate_action(self, action_id: str) -> Optional[Action]:
        """Duplicate an action right after itself."""
        idx = self.get_action_index(action_id)
        if idx is not None:
            cloned = self.actions[idx].clone()
            self.actions.insert(idx + 1, cloned)
            self.updated_at = time.time()
            return cloned
        return None

    def convert_action_to_variable(
        self, action_id: str, variable_name: str = "STATEMENT_DATE"
    ) -> bool:
        """
        Convert a recorded text action into a variable placeholder: {{variable_name}}.
        The workflow no longer contains the literal string.
        """
        idx = self.get_action_index(action_id)
        if idx is not None:
            action = self.actions[idx]
            # Replace text with the variable placeholder
            var_token = f"{{{{{variable_name}}}}}"
            action.metadata["original_recorded_text"] = action.text
            action.text = var_token
            # Ensure action type is TYPE_TEXT
            action.action_type = ActionType.TYPE_TEXT
            self.updated_at = time.time()
            return True
        return False

    def get_referenced_variables(self) -> set[str]:
        """Extract all variable names {{VAR_NAME}} referenced in this workflow."""
        pattern = re.compile(r"\{\{([a-zA-Z0-9_]+)\}\}")
        vars_found: set[str] = set()
        for a in self.actions:
            if a.text:
                for match in pattern.finditer(a.text):
                    vars_found.add(match.group(1))
            for v in a.metadata.values():
                if isinstance(v, str):
                    for match in pattern.finditer(v):
                        vars_found.add(match.group(1))
        return vars_found

    def to_dict(self) -> dict[str, Any]:
        """Convert workflow to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "actions": [a.to_dict() for a in self.actions],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Workflow:
        """Create workflow from dictionary."""
        actions_raw = data.get("actions", [])
        actions = [Action.from_dict(a) for a in actions_raw]
        return cls(
            id=data.get("id", uuid.uuid4().hex[:12]),
            name=data.get("name", "Untitled Workflow"),
            description=data.get("description", ""),
            actions=actions,
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
        )

    def to_json(self, indent: int = 2) -> str:
        """Serialize workflow to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_json(cls, json_str: str) -> Workflow:
        """Deserialize workflow from JSON string."""
        return cls.from_dict(json.loads(json_str))
