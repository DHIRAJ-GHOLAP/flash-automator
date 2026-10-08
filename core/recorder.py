"""Mouse and keyboard recording engine with smart typing coalescer."""
from __future__ import annotations

import time
from enum import Enum
from typing import Callable, Optional

from pynput import keyboard, mouse

from .actions import Action, ActionType
from ..utils.config import get_config
from ..utils.logger import get_logger

logger = get_logger("recorder")


class RecorderState(str, Enum):
    IDLE = "IDLE"
    RECORDING = "RECORDING"
    PAUSED = "PAUSED"


class ActionRecorder:
    """Captures desktop mouse and keyboard events into structured Action objects."""

    def __init__(
        self,
        on_action_added: Optional[Callable[[Action], None]] = None,
        on_state_changed: Optional[Callable[[RecorderState], None]] = None,
    ) -> None:
        self.config = get_config()
        self.state = RecorderState.IDLE
        self.recorded_actions: list[Action] = []
        self.on_action_added = on_action_added
        self.on_state_changed = on_state_changed

        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._last_event_time: float = 0.0

        # Smart typing buffer
        self._typing_buffer: list[str] = []
        self._typing_start_delay: float = 0.2
        self._active_modifiers: set[str] = set()

        # App window exclusion bounds (x, y, w, h)
        self.ignored_rect: Optional[tuple[int, int, int, int]] = None

    def set_ignored_rect(self, rect: Optional[tuple[int, int, int, int]]) -> None:
        """Set window bounds where clicks should be ignored (e.g. app UI)."""
        self.ignored_rect = rect

    def _is_inside_ignored_rect(self, x: int, y: int) -> bool:
        if not self.config.filter_app_window or not self.ignored_rect:
            return False
        rx, ry, rw, rh = self.ignored_rect
        return rx <= x <= rx + rw and ry <= y <= ry + rh

    def _change_state(self, new_state: RecorderState) -> None:
        self.state = new_state
        logger.info(f"Recorder state: {new_state.value}")
        if self.on_state_changed:
            self.on_state_changed(new_state)

    def start(self) -> None:
        """Start listening to mouse and keyboard events."""
        if self.state == RecorderState.RECORDING:
            return

        self.recorded_actions = []
        self._typing_buffer.clear()
        self._active_modifiers.clear()
        self._last_event_time = time.time()

        self._mouse_listener = mouse.Listener(
            on_click=self._on_click,
            on_scroll=self._on_scroll,
            on_move=self._on_move if self.config.record_mouse_moves else None,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )

        self._mouse_listener.daemon = True
        self._keyboard_listener.daemon = True
        self._mouse_listener.start()
        self._keyboard_listener.start()

        self._change_state(RecorderState.RECORDING)

    def pause(self) -> None:
        """Pause recording events without clearing recorded history."""
        if self.state == RecorderState.RECORDING:
            self._flush_typing_buffer()
            self._change_state(RecorderState.PAUSED)

    def resume(self) -> None:
        """Resume recording events."""
        if self.state == RecorderState.PAUSED:
            self._last_event_time = time.time()
            self._change_state(RecorderState.RECORDING)

    def stop(self) -> list[Action]:
        """Stop recording and return captured actions."""
        self._flush_typing_buffer()

        if self._mouse_listener is not None:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None

        if self._keyboard_listener is not None:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass
            self._keyboard_listener = None

        self._change_state(RecorderState.IDLE)
        return list(self.recorded_actions)

    def _record_action(self, action: Action) -> None:
        """Register action, calculate delay, and notify observers."""
        self.recorded_actions.append(action)
        logger.debug(f"Recorded: {action.display_summary()}")
        if self.on_action_added:
            self.on_action_added(action)

    def _flush_typing_buffer(self) -> None:
        """Convert collected characters in buffer to a single TYPE_TEXT action."""
        if not self._typing_buffer:
            return

        buffered_text = "".join(self._typing_buffer)
        self._typing_buffer.clear()

        if not buffered_text:
            return

        act = Action(
            action_type=ActionType.TYPE_TEXT,
            text=buffered_text,
            delay_before=max(0.1, round(self._typing_start_delay, 2)),
        )
        self._record_action(act)

    # --- Mouse Event Handlers ---

    def _on_click(
        self, x: int, y: int, button: mouse.Button, pressed: bool
    ) -> None:
        if self.state != RecorderState.RECORDING or not pressed:
            return

        if self._is_inside_ignored_rect(x, y):
            logger.debug(f"Ignored click inside application UI at ({x}, {y})")
            return

        self._flush_typing_buffer()

        now = time.time()
        delay = max(0.05, now - self._last_event_time)
        self._last_event_time = now

        btn_str = "left"
        if button == mouse.Button.right:
            btn_str = "right"
            act_type = ActionType.RIGHT_CLICK
        elif button == mouse.Button.middle:
            btn_str = "middle"
            act_type = ActionType.MIDDLE_CLICK
        else:
            act_type = ActionType.CLICK

        act = Action(
            action_type=act_type,
            x=int(x),
            y=int(y),
            button=btn_str,
            delay_before=round(delay, 2),
        )
        self._record_action(act)

    def _on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if self.state != RecorderState.RECORDING:
            return

        if self._is_inside_ignored_rect(x, y):
            return

        self._flush_typing_buffer()

        now = time.time()
        delay = max(0.05, now - self._last_event_time)
        self._last_event_time = now

        act = Action(
            action_type=ActionType.SCROLL,
            x=int(x),
            y=int(y),
            scroll_dx=dx,
            scroll_dy=dy,
            delay_before=round(delay, 2),
        )
        self._record_action(act)

    def _on_move(self, x: int, y: int) -> None:
        if self.state != RecorderState.RECORDING:
            return

        if self._is_inside_ignored_rect(x, y):
            return

        now = time.time()
        if now - self._last_event_time < self.config.mouse_move_sample_rate:
            return

        delay = now - self._last_event_time
        self._last_event_time = now

        act = Action(
            action_type=ActionType.MOVE_MOUSE,
            x=int(x),
            y=int(y),
            delay_before=round(delay, 2),
        )
        self._record_action(act)

    # --- Keyboard Event Handlers ---

    def _on_key_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        # Check global recording hotkeys first
        k_str = self._key_to_str(key)

        if k_str == self.config.key_record_stop:
            logger.info("Hotkey stop requested.")
            self.stop()
            return
        elif k_str == self.config.key_record_pause and self.state == RecorderState.RECORDING:
            logger.info("Hotkey pause requested.")
            self.pause()
            return
        elif k_str == self.config.key_record_resume and self.state == RecorderState.PAUSED:
            logger.info("Hotkey resume requested.")
            self.resume()
            return

        if self.state != RecorderState.RECORDING:
            return

        # Track modifiers
        if k_str in ("ctrl", "alt", "shift", "cmd", "windows"):
            self._active_modifiers.add(k_str)
            return

        now = time.time()
        delay = max(0.05, now - self._last_event_time)

        # Check for Hotkeys (e.g. ctrl+p, ctrl+s, etc.)
        if self._active_modifiers:
            self._flush_typing_buffer()
            self._last_event_time = now
            combo = "+".join(sorted(self._active_modifiers)) + f"+{k_str}"
            act = Action(
                action_type=ActionType.HOTKEY,
                key=combo,
                delay_before=round(delay, 2),
            )
            self._record_action(act)
            return

        # Smart typing: coalesce printable characters
        char = getattr(key, "char", None)
        if self.config.coalesce_typing and char is not None and char.isprintable():
            if not self._typing_buffer:
                self._typing_start_delay = delay
            self._typing_buffer.append(char)
            self._last_event_time = now
            return

        # Non-printable or special keys (Enter, Tab, Esc, Backspace, etc.)
        self._flush_typing_buffer()
        self._last_event_time = now

        act = Action(
            action_type=ActionType.KEY_PRESS,
            key=k_str,
            delay_before=round(delay, 2),
        )
        self._record_action(act)

    def _on_key_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        k_str = self._key_to_str(key)
        if k_str in self._active_modifiers:
            self._active_modifiers.discard(k_str)

    @staticmethod
    def _key_to_str(key: keyboard.Key | keyboard.KeyCode) -> str:
        """Normalize key representation to clean string."""
        if isinstance(key, keyboard.Key):
            name = key.name
            if name.startswith("ctrl"):
                return "ctrl"
            if name.startswith("alt"):
                return "alt"
            if name.startswith("shift"):
                return "shift"
            if name.startswith("cmd"):
                return "cmd"
            return name.lower()
        if isinstance(key, keyboard.KeyCode):
            if key.char:
                return key.char.lower()
            return f"code_{key.vk}"
        return str(key).lower()
