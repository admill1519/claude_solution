---
name: review
description: Codified PR review checklist for the e-commerce monorepo
argument-hint: "<pr-ref>"
allowed-tools:
  - Glob
  - Grep
  - Read
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(git show:*)
  - Bash(gh pr view:*)
  - Bash(gh pr checks:*)
---

# /review — team PR review

You are reviewing the diff identified by `$ARGUMENTS` against this repository's conventions. Apply the path-scoped rules in `.claude/rules/` (they auto-load based on the files touched) and the shared standards in `.claude/standards/`.

## Phase 1 — Interview pattern

Before reporting, ask clarifying questions when the author's intent is ambiguous. Ambiguous intent often leads to confidently-wrong verdicts — e.g., flagging "no test coverage" on a refactor when the behavior is already tested upstream and the PR didn't change that behavior.

**Trigger conditions to interview first:**
1. **Dependency changes** — Does this shift in dependencies (package.json, pyproject.toml) unlock new capabilities or retire old ones? Ask if the author tested the upgrade path.
2. **Public API or schema changes** — Are response shapes or DB columns modified? Ask if this is intentional (breaking change) or a correction. If intentional, ask if downstream consumers are aware.
3. **Refactors with no test changes** — Did the PR refactor code without touching test files? Ask: "Was the behavior already covered by tests upstream?" If yes, the lack of new tests is correct. If no, it's a coverage gap.

## Phase 2 — Review criteria

**Must report** (block merge if critical):
- **Bugs**: Logic errors, missing `await`, race conditions, off-by-one errors, or unhandled error cases.
- **Security**: Raw SQL with user input, missing authentication checks, secrets in code, `dangerouslySetInnerHTML`, or exposed private data.
- **Convention violations**: Violations of the standards in `.claude/standards/` (React hooks rules, API error handling, database transaction boundaries) or the rules in `.claude/rules/`.
- **Breaking changes**: Public API shape changes, database schema changes, or dependency removals without deprecation warnings.
- **Migration safety**: Database migrations that are not forward-only or lack proper documentation.
- **Test gaps**: New code paths without test coverage (unless already covered upstream, per the interview pattern).

**Skip** (mention but don't block):
- **Minor formatting**: Prettier, ESLint, and auto-formatters handle this. Don't nitpick whitespace.
- **Naming bikesheds**: If the name is clear and consistent with the codebase, don't block on a "better" alternative.
- **Personal stylistic preferences**: Code that works and follows standards but differs from your style. The rules/standards are authoritative; personal taste is not.
- **TODOs with tickets**: `// TODO: implement X` is fine if issue #123 exists and is tracked.
- **Pre-existing code smells**: Don't report issues in unchanged files or unrelated code.

## Phase 3 — Bundling: interacting vs. independent findings

**Interacting findings** share a single fix. Bundle them into ONE message with all context. Example: a handler with a missing `await` AND no transaction wrapper AND wrong ordering of writes — all three issues are fixed by rewriting the same function. Report all three together.

**Independent findings** have no shared fix. Report them SEQUENTIALLY as separate items so each piece of feedback is actionable. Example: a React component that violates hook rules AND an unrelated API handler that needs error handling — fix the component, then separately fix the handler.

**Heuristic**: If fixing issue A requires changing code that issue B depends on, they are interacting. Bundle them. If they affect different functions or files and have independent fixes, report them separately.

## Phase 4 — Output format

For each finding, produce:

```
[severity] path/to/file.ts:line
finding: <one-sentence description>
fix: <one-sentence recommendation>
```

Severity is `bug` | `security` | `convention` | `breaking`. End with a one-line verdict: `approve`, `comment`, or `request-changes`.

## Examples

### Example 1 — Independent findings

**Input:**
```
src/api/orders/cancel.ts (file is modified)
- Handler does not throw ApiError; returns { status: 404 } directly
- Handler calls db.query() directly instead of using OrderRepository
```

**Output:**
```
[convention] src/api/orders/cancel.ts:15
finding: Handler returns `{ status: 404 }` directly instead of throwing `ApiError`.
fix: Throw `ApiError(404, 'ORDER_NOT_FOUND', 'Order does not exist')` and let middleware handle the response.

[convention] src/api/orders/cancel.ts:22
finding: Handler calls raw SQL `db.query()` instead of repository function.
fix: Use `OrderRepository.findById(id)` and `OrderRepository.update(...)` to maintain the repository boundary.
```

**Verdict:** `request-changes`. Each issue can be fixed independently; report them as separate findings.

### Example 2 — Interacting findings

**Input:**
```
src/api/orders/refund.ts (file is modified)
- Missing `await` on paymentService.refund()
- No transaction wrapper around multi-statement write
- Order cancellation happens before payment refund (wrong order)
```

**Output:**
```
[bug] src/api/orders/refund.ts:18-32
finding: Multiple interacting issues in refund logic:
  1. Missing `await` on `paymentService.refund()` at line 20 — will return before refund completes.
  2. No transaction wrapper — if payment succeeds but DB write fails, they're out of sync.
  3. Wrong order: order cancelled at line 18, then payment refunded at line 20 — if payment fails, order is already marked cancelled.
fix: Wrap in `withTransaction(async (tx) => {...})`, add `await` to `paymentService.refund()`, and move `OrderRepository.cancel()` after the payment succeeds.
```

**Verdict:** `request-changes`. These three issues share a single fix (reordering and wrapping the function); bundle them together.

## Notes

- This command is project-scoped (`.claude/commands/review.md`) so everyone on the team gets the same review. If you want to layer personal preferences (e.g. a stricter accessibility check on your own PRs), put a `~/.claude/commands/review-strict.md` in your home directory — it will not affect teammates.
- If a finding requires running code or modifying files to verify, ask the author to run a specific check rather than attempting it from the review session. This command's `allowed-tools` are read-only by design.
