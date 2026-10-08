"""Configuration management for Flash Automator."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AppConfig:
    # Hotkeys
    key_record_start: str = "f8"
    key_record_stop: str = "f9"
    key_record_pause: str = "f10"
    key_record_resume: str = "f11"
    key_emergency_stop: str = "f12"

    # Playback & Safety
    pyautogui_failsafe: bool = True
    countdown_seconds: int = 3
    default_delay_before: float = 0.2
    mouse_move_duration: float = 0.1

    # Recorder settings
    coalesce_typing: bool = True
    record_mouse_moves: bool = False
    mouse_move_sample_rate: float = 0.05
    filter_app_window: bool = True

    # Vision & OCR
    template_match_threshold: float = 0.85
    screen_change_diff_threshold: float = 0.02
    tesseract_cmd: str = ""

    # Paths & Storage
    base_dir: str = field(default_factory=lambda: str(Path.home() / ".flash_automator"))
    db_file: str = "flash_automator.db"
    default_output_dir: str = field(
        default_factory=lambda: str(Path.home() / "Documents" / "FlashAutomatorOutput")
    )

    @property
    def config_file_path(self) -> Path:
        return Path(self.base_dir) / "config.json"

    @property
    def db_file_path(self) -> Path:
        return Path(self.base_dir) / self.db_file

    def save(self) -> None:
        """Persist settings to disk."""
        target = self.config_file_path
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, indent=2)

    @classmethod
    def load(cls) -> AppConfig:
        """Load configuration from disk, falling back to defaults."""
        config = cls()
        path = config.config_file_path
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data: dict[str, Any] = json.load(f)
                    for k, v in data.items():
                        if hasattr(config, k):
                            setattr(config, k, v)
            except Exception:
                pass
        return config


_global_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Retrieve global cached config instance."""
    global _global_config
    if _global_config is None:
        _global_config = AppConfig.load()
    return _global_config
