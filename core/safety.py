"""Safety controls, fail-safe monitoring, and global emergency abort."""
from __future__ import annotations

import threading
from typing import Callable, Optional

import pyautogui
from pynput import keyboard

from ..utils.config import get_config
from ..utils.logger import get_logger

logger = get_logger("safety")


class SafetyController:
    """
    Manages emergency abort listeners (F12) and PyAutoGUI failsafe states.
    """

    def __init__(self, on_emergency_stop: Optional[Callable[[], None]] = None) -> None:
        self.config = get_config()
        self.stop_requested = threading.Event()
        self.pause_requested = threading.Event()
        self.on_emergency_stop_callback = on_emergency_stop
        self._listener: Optional[keyboard.Listener] = None
        self._setup_pyautogui_failsafe()

    def _setup_pyautogui_failsafe(self) -> None:
        """Configure PyAutoGUI built-in failsafe."""
        try:
            pyautogui.FAILSAFE = self.config.pyautogui_failsafe
            pyautogui.PAUSE = 0.05
        except Exception as e:
            logger.warning(f"Could not configure PyAutoGUI failsafe: {e}")

    def start_global_hotkey_listener(self) -> None:
        """Start global keyboard listener for emergency stop key (default F12)."""
        if self._listener is not None:
            return

        emergency_key_name = self.config.key_emergency_stop.lower()

        def on_press(key: keyboard.Key | keyboard.KeyCode) -> None:
            try:
                # Check function keys (F1-F12)
                key_name = ""
                if isinstance(key, keyboard.Key):
                    key_name = key.name.lower()
                elif isinstance(key, keyboard.KeyCode) and key.char:
                    key_name = key.char.lower()

                if key_name == emergency_key_name:
                    logger.warning(
                        f"EMERGENCY STOP TRIGGERED VIA GLOBAL HOTKEY: {emergency_key_name.upper()}!"
                    )
                    self.trigger_emergency_stop()
            except Exception as e:
                logger.error(f"Error in emergency key handler: {e}")

        try:
            self._listener = keyboard.Listener(on_press=on_press)
            self._listener.daemon = True
            self._listener.start()
            logger.info(f"Emergency stop listener active (Hotkey: {emergency_key_name.upper()})")
        except Exception as e:
            logger.warning(f"Failed to start global keyboard listener: {e}")

    def stop_global_hotkey_listener(self) -> None:
        """Stop global keyboard listener."""
        if self._listener is not None:
            try:
                self._listener.stop()
            except Exception:
                pass
            self._listener = None

    def trigger_emergency_stop(self) -> None:
        """Immediately flag stop and invoke callback."""
        self.stop_requested.set()
        if self.on_emergency_stop_callback:
            try:
                self.on_emergency_stop_callback()
            except Exception as e:
                logger.error(f"Error in emergency callback: {e}")

    def reset(self) -> None:
        """Clear stop and pause flags."""
        self.stop_requested.clear()
        self.pause_requested.clear()

    def is_stopped(self) -> bool:
        return self.stop_requested.is_set()

    def is_paused(self) -> bool:
        return self.pause_requested.is_set()

    def set_paused(self, paused: bool) -> None:
        if paused:
            self.pause_requested.set()
        else:
            self.pause_requested.clear()
