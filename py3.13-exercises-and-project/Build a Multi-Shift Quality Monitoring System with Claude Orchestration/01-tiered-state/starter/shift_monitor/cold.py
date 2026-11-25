"""Cold tier: monthly Markdown summaries derived deterministically from the warm tier."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .warm import WarmStore


@dataclass
class ColdStore:
    store: WarmStore
    cold_dir: Path

    def write_monthly_summary(self, year: int, month: int) -> Path:
        # Create output directory if needed
        self.cold_dir.mkdir(parents=True, exist_ok=True)

        # Build filename and path
        filename = f"{year:04d}-{month:02d}.md"
        path = self.cold_dir / filename

        # Get counts
        total_count = self.store.count_for_month(year, month)
        top_components = self.store.top_components_for_month(year, month)

        # Build Markdown content
        lines = [
            f"# {year:04d}-{month:02d}",
            "",
            f"Total defects: {total_count}",
        ]

        # Add top components section
        if top_components:
            lines.extend([
                "",
                "## Top components",
            ])
            for component, count in top_components:
                lines.append(f"- {component}: {count} defect{'s' if count != 1 else ''}")

        # Write to file
        content = "\n".join(lines) + "\n"
        path.write_text(content, encoding="utf-8")

        return path
