"""Resume-vs-fresh decision logic for crash recovery.

The 30-minute threshold is ~1/16 of an 8-hour shift cycle: a resume inside this
window is still operating on the same shift's working set; anything older is
treated as a stale partial that should be re-started from scratch with whatever
findings the manifest already captured injected as a summary.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal

from .manifest import ManifestState

# Staleness threshold: ~1/16 of an 8-hour shift.
# Resumes within this window are still operating on the same shift's working set;
# anything older is treated as a stale partial that should be re-started from scratch.
STALE_RESUME_THRESHOLD_MINUTES = 30

Decision = Literal["resume", "fresh"]


def decide(state: ManifestState, now: datetime) -> Decision:
    # Case 1: Empty manifest is always fresh
    if not state.steps:
        return "fresh"

    # Case 2: Complete manifest is always fresh
    if state.complete:
        return "fresh"

    # Case 3: Incomplete manifest — check staleness
    # Get the last step's timestamp
    last_step = state.steps[-1]
    gap = now - last_step.ts

    # At exactly 30 minutes or less, resume; otherwise fresh
    if gap <= timedelta(minutes=STALE_RESUME_THRESHOLD_MINUTES):
        return "resume"
    else:
        return "fresh"
