---
name: deploy-check
description: Pre-deployment validation and readiness checks (runs in an isolated fork)
context: fork
allowed-tools:
  - Glob
  - Grep
  - Read
  - Bash(git status:*)
  - Bash(git diff:*)
  - Bash(git log:*)
  - Bash(gh pr view:*)
  - Bash(gh pr checks:*)
---

# /deploy-check

Runs the team's pre-deployment validation checklist against the current working tree and the branch you're about to ship. Read-only by design — this skill never modifies files, never pushes, never deploys. It returns a single structured summary so the calling session can decide whether to proceed.

## Why this is a skill (not a CLAUDE.md addition)

**Use a skill (like deploy-check) when:** the task is on-demand and produces verbose output you want isolated from the main session. **Use CLAUDE.md when:** the guidance always applies and belongs in every session. Deploy checks are on-demand (only run them right before shipping) and forked, so they live as a skill.

## Why `context: fork`

This skill walks the repository, inspects diffs, and runs several enumeration passes to check deployment readiness. All that intermediate output has zero value to the calling session once the verdict is known. `context: fork` runs the skill in an isolated sub-agent, keeping verbose discovery output out of the main conversation. Only the structured summary returns. This mirrors the *Branching Reality* pattern: establish a shared starting point (the repo state), branch into isolated exploration (the fork), and return only actionable results to the parent context.

## Checks

Run all three. Each check produces a pass-or-fail verdict; if any fails, the overall summary is **fail**.

### 1. No uncommitted changes

**Detect:**
- Run `git status --porcelain` to check for untracked or modified files in the working tree.

**Pass:**
- The command returns empty. All changes are committed and ready to ship.

**Fail:**
- The command returns file paths. Report: `"Uncommitted changes found: X files modified, Y files untracked."` List the file paths so the author can decide whether to commit, stash, or investigate.

### 2. Migrations are forward-only

**Detect:**
- Scan `src/db/migrations/` for all `.sql` files in the current branch.
- Check filenames follow `NNNN__description.sql` format (four-digit zero-padded sequence).
- Verify no migration contains `DROP TABLE`, `DROP COLUMN`, or `TRUNCATE` without a documented forward-migration rollback.

**Pass:**
- All migrations follow the naming convention and contain only forward-compatible operations.

**Fail:**
- A migration file doesn't follow naming convention, or a destructive operation found without documented rollback. Report the offending file and the specific violation.

### 3. CI checks are green

**Detect:**
- Run `gh pr view --json statusCheckRollup` to fetch the status of all required checks on the current/open PR.
- Parse the result for all "REQUIRED" checks.

**Pass:**
- All required checks report status "SUCCESS".

**Fail:**
- One or more required checks report status "PENDING", "FAILURE", or other non-SUCCESS. Report which checks are not green and their current status.

## Output format

Return exactly this shape to the main session:

```
verdict: pass | fail
checks:
  - name: <check-name>
    status: pass | fail
    detail: <one line or empty>
```

Do not include the raw `git status`, raw diff hunks, or full check logs in the returned summary — those stay in the fork. If the author wants to investigate a failed check, they can re-invoke the skill targeting that single check or run the underlying command themselves.

## Personalization

This skill is project-scoped (`.claude/skills/deploy-check/`), so the whole team runs the same checks before every deploy. If a teammate wants a stricter personal variant — say, one that additionally fails when the diff exceeds 500 lines without an adequate PR description — they can create `~/.claude/skills/deploy-check-strict/SKILL.md` with a different name. Their variant will not be committed to the repo and will not affect teammates.

## What this skill deliberately does not do

- It never pushes, deploys, or runs migrations. The `allowed-tools` allowlist is read-only by construction; even if a future maintainer adds `Write` here, the team's `/review` command should catch the change.
- It does not run the test suite. Tests have their own pre-merge gate in CI; duplicating that here would slow every deploy check without adding signal.
- It does not check for secrets in code. That's the job of the `gitleaks` pre-commit hook, which fails the commit, not the deploy.
