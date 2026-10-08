"""Action definitions and data structures for Flash Automator."""
from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Optional


class ActionType(str, Enum):
    MOVE_MOUSE = "MOVE_MOUSE"
    CLICK = "CLICK"
    DOUBLE_CLICK = "DOUBLE_CLICK"
    RIGHT_CLICK = "RIGHT_CLICK"
    MIDDLE_CLICK = "MIDDLE_CLICK"
    MOUSE_DOWN = "MOUSE_DOWN"
    MOUSE_UP = "MOUSE_UP"
    SCROLL = "SCROLL"
    KEY_PRESS = "KEY_PRESS"
    KEY_RELEASE = "KEY_RELEASE"
    HOTKEY = "HOTKEY"
    TYPE_TEXT = "TYPE_TEXT"
    WAIT = "WAIT"
    WAIT_FOR_IMAGE = "WAIT_FOR_IMAGE"
    WAIT_FOR_SCREEN_CHANGE = "WAIT_FOR_SCREEN_CHANGE"
    WAIT_FOR_WINDOW = "WAIT_FOR_WINDOW"


@dataclass
class Action:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    action_type: ActionType | str = ActionType.CLICK
    timestamp: float = field(default_factory=time.time)
    delay_before: float = 0.2  # Seconds
    x: Optional[int] = None
    y: Optional[int] = None
    button: str = "left"  # left, right, middle
    text: str = ""  # For TYPE_TEXT or variable references like {{STATEMENT_DATE}}
    key: str = ""  # For KEY_PRESS, KEY_RELEASE, or HOTKEY (e.g. 'ctrl+p', 'enter')
    scroll_dx: int = 0
    scroll_dy: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.action_type, str):
            try:
                self.action_type = ActionType(self.action_type)
            except ValueError:
                pass

    def to_dict(self) -> dict[str, Any]:
        """Serialize action to standard dictionary."""
        d = asdict(self)
        if isinstance(self.action_type, ActionType):
            d["action_type"] = self.action_type.value
        return d

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Action:
        """Deserialize action from dictionary."""
        raw = dict(data)
        # Handle backward compatibility / alternative key names
        if "type" in raw and "action_type" not in raw:
            raw["action_type"] = raw.pop("type")
        act_type = raw.get("action_type", ActionType.CLICK)
        if isinstance(act_type, str):
            try:
                act_type = ActionType(act_type)
            except ValueError:
                pass
        raw["action_type"] = act_type
        return cls(**raw)

    def clone(self) -> Action:
        """Create a deep copy of this action with a new ID."""
        d = self.to_dict()
        d["id"] = uuid.uuid4().hex[:12]
        return Action.from_dict(d)

    def display_summary(self) -> str:
        """Return a human-friendly string describing this action."""
        t = self.action_type.value if isinstance(self.action_type, ActionType) else str(self.action_type)

        if t in ("CLICK", "DOUBLE_CLICK", "RIGHT_CLICK", "MIDDLE_CLICK"):
            coords = f"({self.x}, {self.y})" if self.x is not None and self.y is not None else ""
            return f"{t:<12} {coords} [{self.button}]"

        if t == "MOVE_MOUSE":
            return f"MOVE         ({self.x}, {self.y})"

        if t == "TYPE_TEXT":
            display_txt = self.text if len(self.text) <= 35 else self.text[:32] + "..."
            return f"TYPE_TEXT    \"{display_txt}\""

        if t == "HOTKEY":
            return f"HOTKEY       {self.key.upper()}"

        if t in ("KEY_PRESS", "KEY_RELEASE"):
            return f"{t:<12} {self.key}"

        if t == "SCROLL":
            return f"SCROLL       dy={self.scroll_dy}, dx={self.scroll_dx}"

        if t == "WAIT":
            return f"WAIT         {self.delay_before:.2f}s"

        if t == "WAIT_FOR_IMAGE":
            target = self.metadata.get("image_name", "image")
            timeout = self.metadata.get("timeout", 10.0)
            return f"WAIT_IMAGE   \"{target}\" (timeout {timeout}s)"

        if t == "WAIT_FOR_SCREEN_CHANGE":
            timeout = self.metadata.get("timeout", 15.0)
            return f"WAIT_CHANGE  timeout {timeout}s"

        if t == "WAIT_FOR_WINDOW":
            title = self.metadata.get("window_title", "")
            return f"WAIT_WINDOW  \"{title}\""

        return f"{t}"
