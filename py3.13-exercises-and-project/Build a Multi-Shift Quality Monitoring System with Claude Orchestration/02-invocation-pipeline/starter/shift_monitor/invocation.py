"""Three invocation shapes.

thin     — prompt only.
rich     — hot state + new defects.
resumed  — prior partial findings + new defects since the last manifest step.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from .state import HotState

InvocationShape = Literal["thin", "rich", "resumed"]


@dataclass(frozen=True)
class Invocation:
    shape: InvocationShape
    prompt: str


def thin(prompt: str) -> Invocation:
    return Invocation(shape="thin", prompt=prompt)


def rich(
    role: str, hot_state: HotState, new_defects: Sequence[Mapping[str, Any]]
) -> Invocation:
    lines = [
        f"You are the on-call {role} for Northridge Plant 3.",
        "",
        "## Current hot state",
        f"- Recent defect hashes: {', '.join(hot_state.recent_defect_hashes)}",
        f"- Current shift summary: {hot_state.current_shift_summary}",
        f"- Active alerts: {'; '.join(hot_state.active_alerts) if hot_state.active_alerts else '(none)'}",
        f"- Threshold statuses: {', '.join(f'{k}={v}' for k, v in hot_state.threshold_statuses.items()) if hot_state.threshold_statuses else '(none)'}",
        "",
        "## New defects since last shift",
    ]

    if new_defects:
        for d in new_defects:
            lines.append(
                f"- {d['id']} | {d['ts']} | shift={d['shift']} | "
                f"{d['component']} | severity={d['severity']} | {d['description']}"
            )
    else:
        lines.append("- (none)")

    lines.extend([
        "",
        "Please provide:",
        "1. Summary: A one-line recap of key findings.",
        "2. Findings: Detailed observations about the new defects and patterns.",
        "3. Recommended actions: Suggested next steps for quality improvements.",
        "4. Updated hot state: Propose an updated `current_shift_summary`, `active_alerts`, "
        "and `threshold_statuses` as a JSON block (```json { ... }```).",
    ])

    prompt = "\n".join(lines)
    return Invocation(shape="rich", prompt=prompt)


def resumed(
    session_id: str,
    summary: str,
    latest_message: str,
    prior_steps: Sequence[Mapping[str, Any]],
    new_defects: Sequence[Mapping[str, Any]],
) -> Invocation:
    lines = [
        "## Prior partial findings",
    ]

    if prior_steps:
        for step in prior_steps:
            name = step.get("name", "unknown")
            payload = step.get("payload", {})
            # Truncate payload representation
            payload_str = str(payload)[:100]
            lines.append(f"- {name}: {payload_str}")
    else:
        lines.append("- (none)")

    lines.extend([
        "",
        "## Prior summary",
        summary,
        "",
        "## New defects since last partial step",
    ])

    if new_defects:
        for d in new_defects:
            lines.append(
                f"- {d['id']} | {d['ts']} | {d['component']} | "
                f"severity={d['severity']} | {d['description']}"
            )
    else:
        lines.append("- (none)")

    lines.extend([
        "",
        "## Latest instruction",
        latest_message,
    ])

    prompt = "\n".join(lines)
    return Invocation(shape="resumed", prompt=prompt)
