import json
from pathlib import Path
from datetime import datetime
from retail_context import (
    Transcript, 
    extract, 
    compress, 
    build,
    tokens
)

# Load transcript
transcript = Transcript.load(Path("fixtures/transcript_48turns.json"))

# Extract case facts
print("Extracting case facts...")
case_facts = extract(transcript)
print(f"  ✓ Extracted: {case_facts.customer_id}, {case_facts.refund_order_id}")

# Compress
print("Compressing transcript...")
compressed = compress(transcript)
print(f"  ✓ Compressed: {len(compressed.summaries)} resolved segments, active={compressed.active_issue_id}")

# Assemble
print("Assembling context...")
assembled = build(case_facts, compressed)
assembled_text = assembled.markdown

# Token accounting
print("\nToken accounting:")
run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
budget = {
    "run_id": run_id,
    "baseline": tokens.count(transcript.full_text),
    "case_facts": tokens.count(assembled.case_facts_block),
    "resolved_refund": tokens.count(assembled.resolved_blocks.get("refund", "")),
    "resolved_subscription": tokens.count(assembled.resolved_blocks.get("subscription", "")),
    "active": tokens.count(assembled.active_block),
    "assembled": tokens.count(assembled_text),
}
budget["reduction_percent"] = round(100 * (1 - budget["assembled"] / budget["baseline"]), 2)

for k, v in budget.items():
    if k not in ["run_id", "reduction_percent"]:
        print(f"  {k}: {v} tokens")
print(f"  REDUCTION: {budget['reduction_percent']}%")

# Save budget
runs_dir = Path("runs") / run_id
runs_dir.mkdir(parents=True, exist_ok=True)
(runs_dir / "budget.json").write_text(json.dumps(budget, indent=2))
print(f"\n✓ Saved budget to runs/{run_id}/budget.json")

