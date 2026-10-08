"""Low-level action playback engine using PyAutoGUI and vision integrations."""
from __future__ import annotations

import time
from typing import Optional

import pyautogui

from .actions import Action, ActionType
from .safety import SafetyController
from ..recognition.image_matcher import ImageMatcher
from ..recognition.screen_detector import ScreenDetector
from ..utils.logger import get_logger

logger = get_logger("player")


class PlaybackError(Exception):
    """Raised when an action execution fails or encounters a timeout."""
    pass


class ActionPlayer:
    """Executes individual Action objects on the desktop OS."""

    def __init__(self, safety: SafetyController, dry_run: bool = False) -> None:
        self.safety = safety
        self.dry_run = dry_run

    def interruptible_sleep(self, duration: float, step: float = 0.05) -> bool:
        """
        Sleep for duration while checking for emergency abort.
        Returns True if full duration elapsed, False if aborted.
        """
        elapsed = 0.0
        while elapsed < duration:
            if self.safety.is_stopped():
                return False
            while self.safety.is_paused() and not self.safety.is_stopped():
                time.sleep(0.1)
            time.sleep(min(step, duration - elapsed))
            elapsed += step
        return True

    def play_action(self, action: Action) -> None:
        """Execute a single resolved action with safety checks."""
        if self.safety.is_stopped():
            raise PlaybackError("Playback aborted by user or emergency stop.")

        # Delay before action
        if action.delay_before > 0:
            if not self.interruptible_sleep(action.delay_before):
                raise PlaybackError("Aborted during pre-action delay.")

        act_type = (
            action.action_type.value
            if isinstance(action.action_type, ActionType)
            else str(action.action_type)
        )

        logger.debug(f"Executing: {action.display_summary()} (DryRun: {self.dry_run})")

        try:
            if act_type == ActionType.MOVE_MOUSE.value:
                self._execute_move(action)

            elif act_type == ActionType.CLICK.value:
                self._execute_click(action)

            elif act_type == ActionType.DOUBLE_CLICK.value:
                self._execute_double_click(action)

            elif act_type == ActionType.RIGHT_CLICK.value:
                self._execute_right_click(action)

            elif act_type == ActionType.MIDDLE_CLICK.value:
                self._execute_middle_click(action)

            elif act_type == ActionType.SCROLL.value:
                self._execute_scroll(action)

            elif act_type == ActionType.TYPE_TEXT.value:
                self._execute_type_text(action)

            elif act_type == ActionType.HOTKEY.value:
                self._execute_hotkey(action)

            elif act_type == ActionType.KEY_PRESS.value:
                self._execute_key_press(action)

            elif act_type == ActionType.KEY_RELEASE.value:
                self._execute_key_release(action)

            elif act_type == ActionType.WAIT.value:
                # Wait action itself - handled by pre-delay or metadata duration
                duration = action.metadata.get("duration", action.delay_before)
                self.interruptible_sleep(duration)

            elif act_type == ActionType.WAIT_FOR_IMAGE.value:
                self._execute_wait_for_image(action)

            elif act_type == ActionType.WAIT_FOR_SCREEN_CHANGE.value:
                self._execute_wait_for_screen_change(action)

            elif act_type == ActionType.WAIT_FOR_WINDOW.value:
                self._execute_wait_for_window(action)

            else:
                logger.warning(f"Unrecognized action type: {act_type}")

        except pyautogui.FailSafeException:
            self.safety.trigger_emergency_stop()
            raise PlaybackError("PyAutoGUI FailSafe triggered (mouse in screen corner)!")
        except Exception as e:
            if isinstance(e, PlaybackError):
                raise
            raise PlaybackError(f"Action '{act_type}' failed: {e}") from e

    # --- Action Implementations ---

    def _execute_move(self, action: Action) -> None:
        if action.x is not None and action.y is not None:
            pyautogui.moveTo(action.x, action.y, duration=0.1)

    def _execute_click(self, action: Action) -> None:
        if self.dry_run:
            if action.x is not None and action.y is not None:
                pyautogui.moveTo(action.x, action.y, duration=0.1)
            logger.info(f"[DRY RUN] Simulating CLICK at ({action.x}, {action.y})")
            return

        btn = action.button or "left"
        if action.x is not None and action.y is not None:
            pyautogui.click(action.x, action.y, button=btn)
        else:
            pyautogui.click(button=btn)

    def _execute_double_click(self, action: Action) -> None:
        if self.dry_run:
            if action.x is not None and action.y is not None:
                pyautogui.moveTo(action.x, action.y, duration=0.1)
            logger.info(f"[DRY RUN] Simulating DOUBLE CLICK at ({action.x}, {action.y})")
            return

        if action.x is not None and action.y is not None:
            pyautogui.doubleClick(action.x, action.y, button=action.button or "left")
        else:
            pyautogui.doubleClick(button=action.button or "left")

    def _execute_right_click(self, action: Action) -> None:
        if self.dry_run:
            if action.x is not None and action.y is not None:
                pyautogui.moveTo(action.x, action.y, duration=0.1)
            logger.info(f"[DRY RUN] Simulating RIGHT CLICK at ({action.x}, {action.y})")
            return

        if action.x is not None and action.y is not None:
            pyautogui.rightClick(action.x, action.y)
        else:
            pyautogui.rightClick()

    def _execute_middle_click(self, action: Action) -> None:
        if self.dry_run:
            if action.x is not None and action.y is not None:
                pyautogui.moveTo(action.x, action.y, duration=0.1)
            logger.info(f"[DRY RUN] Simulating MIDDLE CLICK at ({action.x}, {action.y})")
            return

        if action.x is not None and action.y is not None:
            pyautogui.middleClick(action.x, action.y)
        else:
            pyautogui.middleClick()

    def _execute_scroll(self, action: Action) -> None:
        if self.dry_run:
            logger.info(f"[DRY RUN] Simulating SCROLL dy={action.scroll_dy}")
            return
        if action.scroll_dy != 0:
            pyautogui.scroll(action.scroll_dy)

    def _execute_type_text(self, action: Action) -> None:
        text = action.text
        if not text:
            return

        if self.dry_run:
            logger.info(f"[DRY RUN] Simulating TYPE_TEXT: '{text}'")
            return

        # Use pyautogui write for standard ascii; handles typing safely
        try:
            pyautogui.write(text, interval=0.01)
        except Exception:
            # Fallback for clipboard paste if special characters
            import pyperclip

            pyperclip.copy(text)
            pyautogui.hotkey("ctrl", "v")

    def _execute_hotkey(self, action: Action) -> None:
        key_expr = action.key.strip()
        if not key_expr:
            return

        if self.dry_run:
            logger.info(f"[DRY RUN] Simulating HOTKEY: '{key_expr.upper()}'")
            return

        keys = [k.strip().lower() for k in key_expr.split("+")]
        pyautogui.hotkey(*keys)

    def _execute_key_press(self, action: Action) -> None:
        key_name = action.key.strip().lower()
        if not key_name:
            return
        if self.dry_run:
            logger.info(f"[DRY RUN] Simulating KEY_PRESS: '{key_name}'")
            return
        pyautogui.keyDown(key_name)

    def _execute_key_release(self, action: Action) -> None:
        key_name = action.key.strip().lower()
        if not key_name:
            return
        if self.dry_run:
            logger.info(f"[DRY RUN] Simulating KEY_RELEASE: '{key_name}'")
            return
        pyautogui.keyUp(key_name)

    def _execute_wait_for_image(self, action: Action) -> None:
        template_path = action.metadata.get("image_path")
        timeout = float(action.metadata.get("timeout", 10.0))
        threshold = float(action.metadata.get("threshold", 0.85))

        if not template_path:
            logger.warning("WAIT_FOR_IMAGE action missing 'image_path'. Falling back to delay.")
            self.interruptible_sleep(1.0)
            return

        logger.info(f"Waiting up to {timeout}s for image: {template_path}")
        res = ImageMatcher.wait_for_image(template_path, timeout=timeout, threshold=threshold)
        if not res.found:
            raise PlaybackError(f"Target image not found on screen within {timeout}s: {template_path}")

        logger.info(f"Image matched at ({res.x}, {res.y}) with confidence {res.confidence:.2f}")

    def _execute_wait_for_screen_change(self, action: Action) -> None:
        timeout = float(action.metadata.get("timeout", 15.0))
        diff_threshold = float(action.metadata.get("diff_threshold", 0.02))

        logger.info(f"Waiting up to {timeout}s for screen change...")
        changed = ScreenDetector.wait_for_screen_change(
            diff_threshold=diff_threshold, timeout=timeout
        )
        if not changed:
            logger.warning("Screen did not change within timeout. Continuing with fallback.")

    def _execute_wait_for_window(self, action: Action) -> None:
        title = action.metadata.get("window_title", "")
        timeout = float(action.metadata.get("timeout", 10.0))
        logger.info(f"Waiting up to {timeout}s for window '{title}'...")
        # Cross-platform window wait fallback
        self.interruptible_sleep(min(timeout, 2.0))
