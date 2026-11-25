---
name: review
description: Codified PR review checklist for the e-commerce monorepo
argument-hint: "<pr-ref>"
allowed-tools:
  - Glob
  - Grep
  - Read
---

# /review: PR review checklist

Reviews a pull request against the e-commerce team's coding standards and architecture. Run as `/review <pr-ref>` where `<pr-ref>` is a Git ref (branch name, commit hash, or `HEAD`).

## Must-report vs. skip criteria

**Report these findings** (block merge if critical):
- Violations of the shared standards in `.claude/standards/` (React hooks rules, API error handling, database transaction boundaries)
- Mismatch between the PR intent and code changes (e.g., a "performance fix" that doesn't actually benchmark anything)
- Unvalidated or inadequately tested new code paths (especially in API handlers or sensitive data flow)
- Database migrations that are not forward-only or lack proper rollback documentation

**Skip these** (mention but don't block):
- Nit-picking whitespace or comment style (let the auto-formatter handle it)
- Speculation about future performance without data
- Requests to refactor code that works and has tests, unless the refactor fixes a specific problem
- Pre-existing code smells in unchanged files

## Examples

### Example 1: React component PR

**Input:** `--pr-ref feature/cart-summary-v2`

**Review sections to generate:**
1. **Component shape check:** Does each component export a named default? Are props in an interface?
2. **Hook usage:** Are hooks top-level and in dependency arrays exhaustive?
3. **Imports:** Any relative imports that should be `@/` alias paths?
4. **Accessibility:** Images have `alt`? Interactive elements use semantic tags?
5. **Testing:** Are there unit tests for the new components? Do they test rendered output, not internal state?

**Output:**
- If React standards are met, mark sections ✓.
- If a component uses `dangerouslySetInnerHTML`, report as critical.
- If hooks lack dependency arrays or are conditionally called, report as critical.

### Example 2: API handler PR

**Input:** `--pr-ref bugfix/order-status-sync`

**Review sections to generate:**
1. **Handler signature:** Is the handler `async (req) => Promise<{ status, body }>`?
2. **Error handling:** Are all expected errors thrown as `ApiError` with descriptive codes?
3. **Repository boundary:** Imports from `src/db/*Repository`, not raw SQL?
4. **Response schema:** Does the response match `src/api/_schemas/responses/`?
5. **Testing:** Are API handlers tested by calling them directly, not spinning up HTTP?

**Output:**
- If error codes are non-descriptive (e.g., just `'ERROR'`), report as critical.
- If handlers write directly to `res` object instead of returning `{ status, body }`, report as critical.

## Interview pattern subsection

When reviewing, probe deeper on:
1. **Why this change?** Ask about the business or technical driver. If the PR doesn't document it, ask in the review.
2. **Tradeoffs:** What alternatives were considered? Why is this the right choice?
3. **Testing strategy:** Beyond unit tests, have you validated the happy path end-to-end?
4. **Future debt:** Does this change constrain or enable future work?

## Interacting vs. independent guidance

**Bundle these findings together** (interacting issues):
- A React component that violates hook rules AND lacks tests — both stem from incomplete refactoring.
- An API handler that returns the wrong status code AND has an undescriptive error code — both are error-handling problems.

**Review these sequentially** (independent issues):
- An unrelated typo fix in a constant.
- A new test file with good coverage but a minor import-ordering nit.
- A database migration and an unrelated frontend component update.

If interacting issues are present, group them and suggest a single cohesive fix. If issues are independent, they can be addressed in separate commits or follow-ups.
