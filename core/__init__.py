"""Core package for Flash Automator."""
from .actions import Action, ActionType
from .workflow import Workflow
from .date_engine import DateEngine, DateEngineConfig, DateRule
from .variables import VariableEngine
from .safety import SafetyController
from .player import ActionPlayer, PlaybackError
from .recorder import ActionRecorder, RecorderState
from .executor import WorkflowExecutor, ExecutionStats

__all__ = [
    "Action",
    "ActionType",
    "Workflow",
    "DateEngine",
    "DateEngineConfig",
    "DateRule",
    "VariableEngine",
    "SafetyController",
    "ActionPlayer",
    "PlaybackError",
    "ActionRecorder",
    "RecorderState",
    "WorkflowExecutor",
    "ExecutionStats",
]
