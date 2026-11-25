# Plan mode vs. direct execution — team decision guide

Choosing between Claude Code's **plan mode** (investigate and propose before changing anything) and **direct execution** (change code immediately) is the single biggest leverage point in how the team uses the harness day-to-day. The wrong mode at either extreme costs us: plan mode for trivial fixes is friction; direct execution for architectural changes burns context and produces rework.

> **Anchor talk:** Knight-Webb, "SWE Is Becoming Plan and Review" — a curriculum module highlighting the shift from raw coding velocity to structured problem-solving (plan, review, iterate).

This doc walks four concrete decisions against our codebase: one plan-mode example, one direct-execution example, one Explore-subagent example, and one combined-workflow example.

---

## 1. Plan-mode example

**Scenario:** "Extract a shared `useCart(userId)` hook across three components (`src/components/Cart/Cart.tsx`, `src/components/Checkout/Checkout.tsx`, `src/components/MiniCart/MiniCart.tsx`) that all duplicate the same cart-fetching and cache-invalidation logic."

**Why plan mode:**
- Touching 3+ files across the component layer.
- Multiple valid approaches: composition vs. custom hook vs. context wrapper.
- Architectural decision: once the hook is extracted, all future cart UI should use it, so getting the shape right is critical.
- If the hook signature is wrong, all three components will need rewriting. Plan mode prevents costly rework by exploring the current duplication, proposing a hook shape that fits all three callers, and documenting cache-invalidation edge cases before we commit to any changes.

**Workflow:**
1. Run `/plan` and explore: "What's the current duplication pattern? How do Cart.tsx, Checkout.tsx, and MiniCart.tsx differ in their cart-fetching logic? What cache-invalidation triggers exist?"
2. Use the Explore subagent to map the three patterns side-by-side.
3. Design: "Here's the `useCart(userId)` signature. Here's the cache strategy. Here's how each component will call it."
4. Exit plan mode and execute the extraction.

---

## 2. Direct-execution example

**Scenario:** "Add a `min: 0` validation to the `quantity` field in `src/api/_schemas/orders.ts` to prevent negative order quantities."

**Why direct execution:**
- One file: `src/api/_schemas/orders.ts`.
- One line to change: add the `min: 0` validation to the quantity schema.
- You already know the diff: "Find the quantity field, add the constraint, done."
- Low risk: validations never break existing code paths; they only reject invalid inputs that should have been rejected anyway.

**Decision bar:** If you can describe the change in one sentence and predict the patch before invoking Claude, skip planning and use direct execution.

---

## 3. Explore-subagent example

**Scenario:** "Find every place we call `processRefund()` in this codebase. I want to understand the call sites before proposing a schema change to the refund request."

**Why Explore subagent:**
- Grep/Glob searches will produce lots of intermediate output (file lists, false positives, diff context).
- Using Explore **isolates verbose discovery output** from the main conversation.
- The Explore sub-agent uses the **scratchpad pattern**: it writes its findings to a scratchpad file (e.g., `tmp/refund-call-sites.md`) so the inventory survives long sessions without consuming main conversation tokens.

**Expected result:** "processRefund is called in `src/api/orders/refund.ts`, `src/api/billing/issue.ts`, and `src/services/payment.ts`. Here's the scratchpad: [tmp/refund-call-sites.md](tmp/refund-call-sites.md)." You now have a clean summary to decide: do I need plan mode to propose the schema change, or direct execution?

---

## 4. Combined workflow — plan mode for investigation, then direct execution

**Scenario:** "Rename `ordersRepo.findById` → `ordersRepo.getById` in `src/db/orders.ts` to align with our naming convention: `get*` for single-row reads, `find*` for multi-row or filtered queries."

**Investigation question:** Where is `findById` called, and are any of them dynamic (e.g., constructed string lookups that grep would miss)?

**Workflow:**
1. **Plan mode (investigation):** Run `/plan` and ask: "What calls `ordersRepo.findById`? Are any call sites dynamic or unusual?"
2. **Review the plan:** The plan proposes a list of call sites and a rename strategy. You review and approve.
3. **Direct execution (implementation):** Rename the function in `src/db/orders.ts`, then update the three call sites. This is now purely mechanical — keystrokes.
4. **Verify:** Run the test suite.

**Why combined:** Investigation (plan mode) is free; mistakes in direct execution here are expensive because you'd miss dynamic call sites. Once you have the call-site list, the rename itself is mechanical and low-risk — perfect for direct execution.

---

## Quick reference

| Situation | Mode |
|-----------|------|
| Single function, fix is obvious, you can predict the diff | Direct execution |
| Multi-file refactor, API shape is debatable | Plan mode |
| Discovery / inventory across the codebase, you'll throw away the intermediate steps | Explore subagent |
| Investigation-then-mechanical-change | Plan mode → direct execution |
| Architectural decision (which database, which queue) | Plan mode, possibly with a fork to compare options |

When in doubt: plan mode is recoverable (you can switch to execution), but direct execution on a complex change is not. Default to plan when uncertain.
