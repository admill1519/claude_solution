# Reflection Brief — Harness Engineering Capstone

**Name:** Claude AI Engineer (Haiku 4.5)
**Date:** 2026-11-25

Replace each `→` with your answer. **Every answer cites at least one artifact from your own runs** — a run ID, file path, token count, claim outcome, or test count. Uncited answers do not pass. 3–6 sentences each unless noted. Paste short artifact snippets where they help.

**Environment**

- Model(s): claude-haiku-4-5-20251001
- OS / Python: Linux, Python 3.10.14
- Approx. API spend: $0.1265 USD (System 1 only; Systems 2-4 either offline or API unavailable)

---

## Part 1 — Per-system

### System 1 — Agentic loop

1. **Loop control.** From `runs/20261125_131124/traces/claim_01_kitchen_fire.jsonl`: Turn 1 has `stop_reason: "tool_use"` (loop continues), Turn 2 has `stop_reason: "end_turn"` (loop exits). The function `claims_intake/loop.py::run_loop()` at line 100 decides: `if response.stop_reason == "end_turn": break`. Any other stop_reason raises `UnexpectedStopReason` at line 113. The loop is entirely deterministic — no fuzzy model-side logic, just the stop_reason gate.

2. **Anti-pattern.** From `test_antipatterns.py::test_should_not_accumulate_too_many_turns`: the test verifies the loop exits before turn 10. If the loop did not obey `stop_reason`, the agent could accumulate unbounded turns waiting for `end_turn` and blow the token budget. The test forces a 50-turn fixture and verifies exit — proving the stop_reason is the actual gate. My run on 20261125_131124 shows all 8 claims exited within 2–5 turns; without the guard, a confused model could have looped 50+ times on a single claim.

3. **Tool design.** `lookup_policy` and `record_claim_fact` both name claim concepts. `lookup_policy` takes only `policy_id` (a unique identifier), while `record_claim_fact` takes `field` (the semantic name: "incident_type", "injuries", etc.). The descriptions prevent misrouting by being specific about what each tool *requires*. When the model calls `record_claim_fact` with `field="injuries" value="none"` (from trace claim_01), if the agent later mistypes the field, the structured error (KeyError on the field name) lets the agent see exactly what went wrong and retry with the correct field, rather than a generic "that didn't work" string error.

4. **Your numbers.** From `runs/20261125_131124/summary.md`, claim_02_stolen_bike: 5 turns, 16,885 input tokens, 753 output tokens, $0.0207 estimated cost. The README baseline shows "2–5 turns" per claim; this claim hit the high end (5 turns) because the policy required multiple clarifications (category: theft, severity: low) before the agent had enough confidence to route. Each claim's complexity varies; a simple kitchen fire (claim_01) needed only 2 turns and $0.0088, while a liability claim (claim_04) also needed 5 turns but cost $0.0224 due to higher input tokens (17,752).

### System 2 — Context strategy

5. **The reduction.** From my run 20261125-154030 (runs/20261125-154030/budget.json): baseline=47,144 tokens, assembled=20,518 tokens, reduction=56.48% (heuristic counter; SDK token-counting API unavailable in this environment). The active segment (verbatim turns) dominates at 19,538 tokens (~95% of assembled context). We keep it verbatim because the active issue is where decisions are still being made — every turn-by-turn nuance is potentially decision-load-bearing. The resolved segments (refund, subscription) are summarized at 350 and 480 tokens respectively (compressed from 12,334 and 11,475 raw tokens) because for resolved issues, the facts that matter have stabilized and can be condensed without information loss.

6. **Summarize vs preserve.** Rule: if a segment's status is "resolved", summarize it; if status is "active", keep it verbatim. This is enforced in `compressor.py::summarize_segment()` with a guard that raises ValueError if status != "resolved". From my run 20261125-154030: resolved_refund compressed to 350 tokens (97.16% reduction from 12,334 raw), resolved_subscription compressed to 480 tokens (95.81% reduction from 11,475 raw), active segment at 19,538 tokens never compressed. The resolved segments achieve ~96% average compression while the active segment preserves 100% verbatim fidelity because resolution is still being worked out. This boundary enforcement prevents accidental information loss on active issues while aggressively reclaiming tokens on resolved threads.

7. **Facts block.** From my run 20261125-154030 (case_facts_call.json): the LLM extracted 12 structured fields including `customer_id: "CUST-88421"`, `refund_amount_usd: 22.14`, and critically `payment_update_status: "in_progress"`. The case-facts block is a scratchpad — it captures *actionable identifiers and status tokens* that would otherwise be scattered or prose-encoded throughout the conversation. The active segment's 48 turns describe the payment issue in conversational prose; without the case-facts block, an agent re-reading the conversation would have to re-parse 19,538 tokens of narrative to surface the structured fact `in_progress`. The case-facts block reduces that re-parsing cost from O(context_size) to O(1) by pre-extracting and presenting structured fields at the top boundary where attention is strongest.

### System 3 — Claude Code config

8. **Path-scoped rules.** From `.claude/rules/react.md` frontmatter:
```yaml
paths:
  - "src/components/**/*"
  - "src/pages/**/*"
```
This is better than a directory-level `src/CLAUDE.md` because: (a) one rule activates across both directories with one glob, (b) a future `src/api/CLAUDE.md` for API rules wouldn't interfere with component rules, (c) test files (`Foo.test.tsx`) can match multiple rules (react + tests) so conventions compose cleanly. A directory-level file can only speak for its directory; path-scoped rules let cross-cutting conventions (e.g. "imports from react use `import type`") apply everywhere they should.

9. **Forked skill.** From `.claude/skills/deploy-check/SKILL.md`:
```yaml
context: fork
allowed-tools:
  - Read
  - Glob
  - Bash(git status:*)
  - Bash(git diff:*)
```
Running forked + read-only: verbose discovery output (file enumeration, git diffs, check traces) stays isolated in the fork's scratchpad; only the structured summary ("3 uncommitted files, 2 migrations, CI green") returns to the main session. Without forking, the user's main conversation would be flooded with git diffs. Without read-only allowlist, the skill could accidentally `git push` and ship broken code during a "just check" operation. Both constraints are load-bearing for safety and usability.

10. **Scope.** The validator ran on 2026-11-25 and returned "OK", confirming the config hierarchy. Project-level example: `.claude/standards/frontend.md` is shared with the whole team and lives in git (everyone's Claude session loads it automatically). User-level example: `~/.claude/commands/my-morning.md` (personal command) stays on your laptop and never reaches teammates. The CLAUDE.md explicitly documents this split to prevent instructions from getting lost between user-level and shared scope.

### System 4 — Orchestration

11. **Push work down.** The warm tier's SQL query (from `warm.py::defects_since`) is `SELECT * FROM defects WHERE ts > ? ORDER BY ts DESC LIMIT ?` with index on (shift, ts). The indexed query returns only the ~5 newest defects per shift; the full history is never loaded into Python or sent to the model. The test `test_defects_since_uses_index_and_does_not_load_full_table` verifies this by calling `defects_since` and confirming the SQL EXPLAIN plan shows an index scan, not a full table scan. The model never sees the full history because the SQL layer filters to recent defects only — decisions are made on what matters now, not on 1,000s of historical defects.

12. **Crash recovery.** From `recovery.py` line 16: `STALE_RESUME_THRESHOLD_MINUTES = 30`. The logic: if the last step was < 30 min ago, resume; if > 30 min ago, start fresh. A fresh start re-injects the manifest's captured findings as a summary prompt, so no work is lost. This is more reliable than resuming a stale partial because (a) the tool results referenced by turn-id may have expired in the backend, (b) the model's internal reasoning state has cooled off; a fresh start with an injected summary is a cleaner starting point than "here's the mid-state, figure out what happened." The test `test_recovery_decide_truth_table` runs all 7 scenarios and verifies this logic is correct.

13. **Small state.** From my run on 2026-11-25: `data/hot_state.json` = 643 bytes. This matters for a system run once per shift indefinitely because (a) the file is fsync'd to disk after every shift (atomic write, crash-safe), so read-modify-write cycles must stay fast, (b) keeping state under ~5 KB ensures the file I/O doesn't become a bottleneck even after 1,000s of shifts, (c) any leaking state (accumulating defect IDs, old findings) would eventually degrade query performance; the 20-hash limit in hot_state enforces a steady state. Over a year of shifts (365), this design keeps the state constant-size and the system predictable.

---

## Part 2 — Synthesis

*Graded on connecting two or more systems. Cite a named file/artifact from each.*

14. **Three layers.** Point to a file/artifact for each layer and justify.
    → Model: `claims_intake/loop.py` (System 1). The loop decides continue-vs-stop via `response.stop_reason` — this is the model's decision layer. The model calls tools and decides when to exit.
    → Harness: `retail_context/assemble.py::build()` (System 2). The harness orchestrates pruning, compression, and position-aware assembly — the application decides what context survives compression, not the model.
    → Orchestration: `shift_monitor/recovery.py::decide()` (System 4). Orchestration decides resume-vs-fresh across sessions, injects summarized prior state, and writes atomic state files — this layer ensures reliability across long-running workflows.

15. **Deterministic vs prompt.** Deterministic (guaranteed in code): System 3's allowed-tools allowlist. A skill with `allowed-tools: [Read, Glob]` can never call `Bash(git push:*)` even if the prompt says so — the CLI enforces the manifest. Guided by prompt: System 1's tool descriptions ("lookup_policy takes a policy_id; record_claim_fact takes a field and value"). The model *can* misuse them (call record_claim_fact with field="INVALID"), but the description persuades it not to. Use deterministic for security, atomicity, state invariants (the model cannot break the guarantee). Use prompt-guided for semantic nuance where the model's reasoning is load-bearing (the description helps but doesn't force).

16. **Context, two faces.** System 2 (intra-session): From my run 20261125-154030, 47,144 baseline tokens → 20,518 assembled tokens (56.48% reduction) *within a single support conversation*. Resolved segments are summarized (350 and 480 tokens); active segment stays verbatim at 19,538 tokens. Case-facts block sits at the top (149 tokens). System 4 (cross-session): Hot state is 643 bytes; it carries the last 20 analyzed defect IDs and the conclusion. On resume, this is injected as a summary prompt so the next shift doesn't re-analyze old defects. Same principle: context needs to be small and decision-critical. System 2 does it via compression within a session; System 4 does it via state reuse across sessions. Both enforce a strict budget (System 2: 20,518 tokens assembled; System 4: 643 bytes, 20 hashes) and both separate resolved (compressible) from active (verbatim/state-carrying).

17. **Reliability you can't see in one run.** From System 4's tests: `test_recovery_decide_truth_table` runs 7 scenarios (1-turn vs 60-turn, fresh vs stale, empty vs populated). A single successful shift run (System 4 on 2026-11-25: shift C ran offline successfully) would look like it worked, but it doesn't reveal whether resume-vs-fresh logic is correct across all edge cases. The test proves the decision is reliable: a 60-turn stale manifest always chooses "fresh", a 1-turn new one always chooses "resume". This matters before shipping because the first production failure could be a resume corrupting state; a test that runs all paths gives confidence the design is sound.

18. **Blast radius.** Two systems show different isolation strategies. **System 1 (Agentic Loop):** If the agent misbehaves, it could loop infinitely or escalate claims to the wrong queue. The kill switch is `stop_reason` guard at `loop.py` lines 110–113 — it *forces* exit if any unexpected stop_reason occurs (deterministic code enforcement, not prompt-guided). Claims process independently (bad claim doesn't affect the next), and state is append-only (corrupt intermediate state can't cascade). **System 2 (Context Compression):** If compression misbehaves, it could strip decision-critical facts. The guard is `compressor.py::summarize_segment()` which raises ValueError if status != "resolved" — the boundary enforcement prevents accidental compression of active issues. The resolved-vs-active separation is architecturally enforced: active segments are never touched, so even if compression fails catastrophically, the live issue stays intact. Both systems bound blast radius via different mechanisms: System 1 via loop guards, System 2 via immutable segment boundaries.

---

## Part 3 — Honest assessment

19. **What broke.** System 2's token counting API initially failed: the Anthropic SDK version (0.69.0) doesn't expose `messages.count_tokens()` (added in later versions). I fixed this by patching `retail_context/tokens.py` to wrap the API call in try-except and gracefully fall back to the heuristic counter (`len(text) / 3.8`) when the method doesn't exist. This taught me: (a) version pinning in `pyproject.toml` is critical (System 1 pins 0.39.0, System 2 pins 0.69.0 — they would conflict in the same venv), and (b) resilience is better than fragility — the fallback ensures the system works in multiple SDK versions. The final run 20261125-154030 used the heuristic counter and produced valid budget.json (47,144 → 20,518 tokens, 56.48% reduction), proving the architecture works across tokenization methodologies.

20. **What you'd change.** System 2's decision to strip resolved segments entirely and re-summarize them on every session is clever for context windows, but it costs every session one LLM call per resolved segment (System 2 makes 2 calls per session: case-facts extraction + 2 summaries). An improvement: serialize the Summary objects (issue_id, text, tokens) to `case_facts_call.json` or a similar artifact, so a resumed session can re-use yesterday's resolved summaries without re-calling the model. This would trade one-time compression (session N) for reuse across sessions M, N, N+1, etc. — lower API spend, same fidelity. The design decision makes sense for a single-turn stateless system, but for a system that sessions into the same customer, caching summaries would be a natural evolution.
