# Plan Mode vs. Direct Execution: Workflow Decision Guide

This guide helps the e-commerce team decide whether to use **plan mode** (explore → design → implement) or **direct execution** (code immediately) for a given task.

## Plan mode: When to use it (explore-first)

Use plan mode when the task **involves multiple files**, **impacts architecture**, or **risks costly rework**.

### Example: Refactoring the checkout flow

**Scenario:** "Move payment logic from a checkout UI to a new API handler, then update the React component to call the new API, adjusting error handling throughout. This touches frontend standards, API conventions, and database patterns."

**Files involved:**
- `.claude/standards/frontend.md` (UI update standards)
- `.claude/standards/api.md` (API handler standards)
- `.claude/standards/database.md` (database pattern standards)

**Why plan mode:**
- Touching 3+ files across different layers (pages, API, database).
- Reworking this later is expensive if the API signature is wrong or the transaction boundary is misplaced.
- **Plan mode prevents costly rework** by letting you explore the codebase, understand dependencies, and design the refactor before writing.

**Workflow:**
1. Run `/plan` and explore: "How is payment currently wired? What error cases exist? Where are orders persisted?"
2. Use the Explore subagent to map the payment flow end-to-end.
3. Design: "Here's the new handler signature. Here's how the React component will call it. Here's the error handling."
4. Exit plan mode and execute: implement the refactored checkout.

## Direct execution: When to use it (code immediately)

Use direct execution when the task is **well-scoped**, **touches one function or file**, and **implementation is straightforward**.

### Example: Add a utility function

**Scenario:** "Add a `formatPrice(cents: number): string` function to a currency utilities module."

**Scope:**
- Single file: currency utility module.
- Self-contained: no dependencies on other utility functions or APIs.
- Clear implementation: convert cents to dollars, format with locale-aware rounding.

**Why direct execution:**
- One file, one clear task.
- Low risk of architectural issues.
- If you get it slightly wrong, it's a 2-minute fix.

**Workflow:**
1. Read the existing currency utilities module to understand the style.
2. Implement `formatPrice()`.
3. Add a simple test.
4. Done.

## Explore: Using the Explore subagent for discovery

When you're **unsure about dependencies** or **the codebase is unfamiliar**, use the **Explore subagent** (or `/explore` within plan mode) to isolate verbose discovery.

### Example: Explore-driven investigation

**Scenario:** "I need to understand how state management is wired throughout the application. What components use it?"

**Why Explore:**
- Grep/Glob searches will produce lots of intermediate output (matches, dead-ends, false positives).
- Using Explore **isolates verbose discovery output**, keeping it out of the main session.
- Use the **scratchpad pattern**: Explore writes findings to a scratchpad (task notes), then returns a clean summary.

**Workflow:**
1. Run `/explore "How is state management structured and where is it used?"` in a fork context.
2. Explore searches, reads files, and builds a mental map (all output stays in the fork).
3. Returns a crisp summary: "State is defined in X. It's used in Y components and also in Z modules."
4. You now have clarity to decide: plan mode or direct execution?

## Combined workflow: Plan + Direct + Explore

Combine these patterns for real-world tasks:

### Example: "Add multi-currency support to the checkout"

1. **Explore:** Use `/explore` to understand the current currency handling (scope and dependencies).
2. **Plan:** Use `/plan` to design the multi-currency integration across API, React components, and database migrations.
3. **Direct execution:** Implement specific, well-scoped tasks that the plan identified (e.g., "Add `currency` column to Orders table").
4. **Explore again (if needed):** If you hit an unexpected dependency, fork off to explore it in isolation.

**Flow:**
```
Explore (understand current state)
  → Plan (design solution across 3+ files)
  → Direct (implement the specific, scoped tasks from the plan)
  → [Explore if needed for clarification]
```

This pattern keeps the main session clean, reduces rework, and maintains velocity.

## Citation: Knight-Webb curriculum

This workflow is inspired by **"SWE Is Becoming Plan and Review,"** a talk by Knight Webb highlighting the shift from raw coding to structured problem-solving in modern software engineering. The pattern—explore (understand), plan (design), direct (execute)—mirrors this evolution from the Knight-Webb curriculum.

## Reference files

The shared standards that guide this workflow live in:
- `.claude/standards/frontend.md` (React standards)
- `.claude/standards/api.md` (API standards)
