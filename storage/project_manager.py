"""Project and workflow repository manager with JSON and CSV export/import."""
from __future__ import annotations

import csv
import json
import time
from pathlib import Path
from typing import Optional

from .database import Database, get_db
from .models import ExecutionLogRecord, ProjectRecord
from ..core.workflow import Workflow
from ..utils.logger import get_logger

logger = get_logger("project_manager")


class ProjectManager:
    """Manages project persistence, workflow versioning, and execution logs."""

    def __init__(self, db: Optional[Database] = None) -> None:
        self.db = db or get_db()

    # --- Project Management ---

    def create_project(self, name: str, description: str = "") -> ProjectRecord:
        """Create and store a new project."""
        project = ProjectRecord(name=name, description=description)
        conn = self.db.get_connection()
        with conn:
            conn.execute(
                "INSERT INTO projects (id, name, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (project.id, project.name, project.description, project.created_at, project.updated_at),
            )
        logger.info(f"Created project: {project.name} ({project.id})")
        return project

    def get_project(self, project_id: str) -> Optional[ProjectRecord]:
        """Fetch project by ID."""
        conn = self.db.get_connection()
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        if row:
            return ProjectRecord(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        return None

    def list_projects(self) -> list[ProjectRecord]:
        """List all projects ordered by updated_at descending."""
        conn = self.db.get_connection()
        rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
        return [
            ProjectRecord(
                id=r["id"],
                name=r["name"],
                description=r["description"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in rows
        ]

    def delete_project(self, project_id: str) -> bool:
        """Delete project and associated workflows/logs."""
        conn = self.db.get_connection()
        with conn:
            conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        return True

    # --- Workflow Management ---

    def save_workflow(self, workflow: Workflow, project_id: Optional[str] = None) -> None:
        """Insert or update a workflow in the database."""
        conn = self.db.get_connection()
        actions_json = json.dumps([a.to_dict() for a in workflow.actions])
        now = time.time()
        with conn:
            conn.execute(
                """
                INSERT INTO workflows (id, project_id, name, description, actions_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    project_id = excluded.project_id,
                    name = excluded.name,
                    description = excluded.description,
                    actions_json = excluded.actions_json,
                    updated_at = excluded.updated_at
                """,
                (
                    workflow.id,
                    project_id,
                    workflow.name,
                    workflow.description,
                    actions_json,
                    workflow.created_at,
                    now,
                ),
            )
        logger.info(f"Saved workflow: {workflow.name} ({workflow.id})")

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Load workflow by ID."""
        conn = self.db.get_connection()
        row = conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
        if row:
            data = {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
                "actions": json.loads(row["actions_json"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            return Workflow.from_dict(data)
        return None

    def list_workflows(self, project_id: Optional[str] = None) -> list[Workflow]:
        """List workflows, optionally filtering by project."""
        conn = self.db.get_connection()
        if project_id:
            rows = conn.execute(
                "SELECT * FROM workflows WHERE project_id = ? ORDER BY updated_at DESC",
                (project_id,),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM workflows ORDER BY updated_at DESC").fetchall()

        results: list[Workflow] = []
        for r in rows:
            data = {
                "id": r["id"],
                "name": r["name"],
                "description": r["description"],
                "actions": json.loads(r["actions_json"]),
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            results.append(Workflow.from_dict(data))
        return results

    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow by ID."""
        conn = self.db.get_connection()
        with conn:
            conn.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
        return True

    # --- Execution History ---

    def log_execution(self, record: ExecutionLogRecord) -> None:
        """Record an iteration's execution status in SQLite."""
        conn = self.db.get_connection()
        with conn:
            conn.execute(
                """
                INSERT INTO execution_logs
                (id, project_id, workflow_id, iteration, date_value, status, details, output_file, duration_sec, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.id,
                    record.project_id,
                    record.workflow_id,
                    record.iteration,
                    record.date_value,
                    record.status,
                    record.details,
                    record.output_file,
                    record.duration_sec,
                    record.created_at,
                ),
            )

    def get_execution_logs(
        self, workflow_id: Optional[str] = None, limit: int = 200
    ) -> list[ExecutionLogRecord]:
        """Retrieve recent execution logs."""
        conn = self.db.get_connection()
        if workflow_id:
            rows = conn.execute(
                "SELECT * FROM execution_logs WHERE workflow_id = ? ORDER BY created_at DESC LIMIT ?",
                (workflow_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM execution_logs ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()

        return [
            ExecutionLogRecord(
                id=r["id"],
                project_id=r["project_id"],
                workflow_id=r["workflow_id"],
                iteration=r["iteration"],
                date_value=r["date_value"],
                status=r["status"],
                details=r["details"],
                output_file=r["output_file"],
                duration_sec=r["duration_sec"],
                created_at=r["created_at"],
            )
            for r in rows
        ]

    # --- Portable Export & Import ---

    def export_workflow_to_file(self, workflow: Workflow, file_path: str | Path) -> None:
        """Export workflow to portable JSON file."""
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(workflow.to_json(indent=2))
        logger.info(f"Workflow exported to {target}")

    def import_workflow_from_file(self, file_path: str | Path) -> Workflow:
        """Import workflow from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        workflow = Workflow.from_json(content)
        return workflow

    def export_logs_to_csv(self, file_path: str | Path, workflow_id: Optional[str] = None) -> None:
        """Export execution logs to CSV for reporting and compliance."""
        logs = self.get_execution_logs(workflow_id=workflow_id, limit=5000)
        target = Path(file_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "ID",
                    "Iteration",
                    "Date",
                    "Status",
                    "Duration (s)",
                    "Output File",
                    "Details",
                    "Timestamp",
                ]
            )
            for log in logs:
                writer.writerow(
                    [
                        log.id,
                        log.iteration,
                        log.date_value,
                        log.status,
                        f"{log.duration_sec:.2f}",
                        log.output_file,
                        log.details,
                        time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(log.created_at)),
                    ]
                )
        logger.info(f"Exported {len(logs)} logs to CSV: {target}")
