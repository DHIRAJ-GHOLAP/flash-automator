"""Views package for Flash Automator."""
from .dashboard_view import DashboardView
from .recorder_view import RecorderView
from .editor_view import WorkflowEditorView
from .automation_view import AutomationView
from .variables_view import VariablesView
from .history_view import HistoryView
from .settings_view import SettingsView

__all__ = [
    "DashboardView",
    "RecorderView",
    "WorkflowEditorView",
    "AutomationView",
    "VariablesView",
    "HistoryView",
    "SettingsView",
]
