"""Incremental crash-recovery manifest backed by JSON lines + fsync."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

InvocationShape = Literal["thin", "rich", "resumed"]


class Step(BaseModel):
    model_config = ConfigDict(frozen=True)

    step_id: str
    name: str
    ts: datetime
    invocation_shape: InvocationShape
    payload: dict[str, Any]


class ManifestState(BaseModel):
    complete: bool
    steps: list[Step]


class Manifest:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append_step(self, step: Step) -> None:
        # Ensure parent directory exists
        self.path.parent.mkdir(parents=True, exist_ok=True)

        # Open in binary append mode for durability
        with open(self.path, "ab") as f:
            # Encode step as JSON line
            line = step.model_dump_json() + "\n"
            f.write(line.encode("utf-8"))
            # Flush and fsync to ensure bytes hit disk before returning
            f.flush()
            os.fsync(f.fileno())

    @classmethod
    def load(cls, path: Path) -> ManifestState:
        # Return empty state if file doesn't exist
        if not path.exists():
            return ManifestState(complete=False, steps=[])

        # Read and parse all steps
        steps: list[Step] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    step = Step.model_validate_json(line)
                    steps.append(step)

        # Determine if complete: last step must exist and be named "complete"
        complete = len(steps) > 0 and steps[-1].name == "complete"

        return ManifestState(complete=complete, steps=steps)
