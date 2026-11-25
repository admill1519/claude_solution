"""Layer 3 fork: copy hot state into an isolated working directory per hypothesis.

`fork_session` here is the application-side framing: the SDK / CLI primitive lives at
Layer 2; here we reproduce the *semantics* (shared baseline, isolated scratchpads,
no cross-contamination) using state-file copies.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterable
from pathlib import Path

from .scratchpad import Scratchpad


def fork_for_hypothesis(
    base_hot_state_path: Path,
    hypothesis_id: str,
    forks_root: Path,
) -> Path:
    # Create fork directory for this hypothesis
    fork_dir = forks_root / hypothesis_id
    fork_dir.mkdir(parents=True, exist_ok=True)

    # Copy base hot state without mutating the original
    fork_hot_state = fork_dir / "hot_state.json"
    shutil.copyfile(base_hot_state_path, fork_hot_state)

    return fork_dir


def merge_findings(scratchpad_paths: Iterable[Path], main_scratchpad: Path) -> None:
    # Create main scratchpad accessor
    main = Scratchpad(main_scratchpad)

    # Process each fork scratchpad
    for fork_path in scratchpad_paths:
        # Skip paths that don't exist
        if not fork_path.exists():
            continue

        # Read all entries from this fork
        fork = Scratchpad(fork_path)
        fork_entries = fork.read()

        # Append each entry to main scratchpad via the durable append mechanism
        for entry in fork_entries:
            main.append(entry)
