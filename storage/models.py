"""Storage data models for projects, workflows, and execution history."""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ProjectRecord:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    name: str = "New Project"
    description: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


@dataclass
class ExecutionLogRecord:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    project_id: Optional[str] = None
    workflow_id: Optional[str] = None
    iteration: int = 1
    date_value: str = ""
    status: str = "SUCCESS"  # SUCCESS, FAILED, SKIPPED, PAUSED
    details: str = ""
    output_file: str = ""
    duration_sec: float = 0.0
    created_at: float = field(default_factory=time.time)
