"""Anti-pattern audit.

Verifies, by static AST analysis, that the agentic loop does NOT:
- use string-membership tests against text content to drive control flow
- use an integer-literal iteration cap as its primary stopping mechanism
- omit reference to `stop_reason` as the loop-breaking signal

And that the package broadly does not branch on `claim_type` equality
outside of the tool-schema definitions and the cost-estimate module.

Each test parses the relevant file with `ast` and walks the tree. There are
no runtime imports of claims_intake here — the audit is static, so it works
even if loop.py / tools.py do not run end-to-end.
"""

from __future__ import annotations

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parents[1] / "claims_intake"
LOOP_PY = PKG / "loop.py"


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


# ---------------------------------------------------------------------------
# Anti-pattern 1 — no string-membership tests against assistant text in the loop
# ---------------------------------------------------------------------------
def test_no_string_membership_against_text_in_loop() -> None:
    """No `"some_token" in <something>` expressions in loop.py.

    Heuristic: any `ast.Compare` node using `ast.In` whose `left` operand is a
    string `ast.Constant` is flagged. The loop has no legitimate reason to test
    for the presence of a magic string inside the model's output — that would be
    natural-language-driven control flow.
    """
    tree = _parse(LOOP_PY)
    offenders = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            # Check if any operator is ast.In and left operand is a string Constant
            if any(isinstance(op, ast.In) for op in node.ops):
                if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                    offenders.append(ast.unparse(node))

    assert not offenders, f"Found string membership tests: {offenders}"


# ---------------------------------------------------------------------------
# Anti-pattern 2 — no integer-literal iteration cap as the primary stop mechanism
# ---------------------------------------------------------------------------
def test_no_integer_literal_iteration_cap_in_loop() -> None:
    """No `for _ in range(<int literal>)` and no `while <var> < <int literal>` in loop.py.

    Token/wall-clock/config-sourced budgets are explicitly allowed because they
    read their cap from a `Budget` instance (an attribute access or a function
    arg), not from a literal. If you need a cap, pass it in.
    """
    tree = _parse(LOOP_PY)
    offenders = []

    for node in ast.walk(tree):
        # Check for `for _ in range(<int literal>, ...)`
        if isinstance(node, ast.For):
            if isinstance(node.iter, ast.Call):
                if isinstance(node.iter.func, ast.Name) and node.iter.func.id == "range":
                    # Check if any argument is an int Constant
                    for arg in node.iter.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, int):
                            offenders.append(f"for loop with range({arg.value})")

        # Check for `while <var> < <int literal>`
        elif isinstance(node, ast.While):
            if isinstance(node.test, ast.Compare):
                for comp in node.test.comparators:
                    if isinstance(comp, ast.Constant) and isinstance(comp.value, int):
                        offenders.append(f"while loop comparing to int literal {comp.value}")

    assert not offenders, (
        f"Found integer-literal iteration caps: {offenders}. "
        "Use a Budget instead."
    )


# ---------------------------------------------------------------------------
# Positive evidence — stop_reason is the value that breaks the while loop
# ---------------------------------------------------------------------------
def test_stop_reason_is_loop_control() -> None:
    """loop.py references `stop_reason` AND a `while` loop exits via return/raise on it."""
    tree = _parse(LOOP_PY)

    # Check for at least one reference to `stop_reason`
    has_stop_reason_ref = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute) and node.attr == "stop_reason":
            has_stop_reason_ref = True
            break
        elif isinstance(node, ast.Name) and node.id == "stop_reason":
            has_stop_reason_ref = True
            break

    assert has_stop_reason_ref, "loop.py must reference 'stop_reason'"

    # Check that at least one while loop exits via return/raise on stop_reason
    found_proper_exit = False
    for node in ast.walk(tree):
        if isinstance(node, ast.While):
            body_code = ast.unparse(node.body)
            has_stop_reason = "stop_reason" in body_code
            has_exit = "return" in body_code or "raise" in body_code
            if has_stop_reason and has_exit:
                found_proper_exit = True
                break

    assert found_proper_exit, (
        "loop.py must have a while loop whose body exits (return/raise) based on stop_reason"
    )


# ---------------------------------------------------------------------------
# Decision-tree-in-Python — no `if claim_type == "..."` branches in the package
# ---------------------------------------------------------------------------
def test_no_claim_type_equality_branching_in_package() -> None:
    """Decision logic about claim type lives in the model, not in Python.

    tools.py is exempt (it defines the enum in input_schema).
    pricing.py is exempt (it may map claim_type to per-queue cost weights).
    """
    offenders = []
    exempt_files = {"tools.py", "pricing.py", "__init__.py"}

    # Walk every .py file under PKG
    for py_file in PKG.rglob("*.py"):
        # Skip exempt files
        if py_file.name in exempt_files:
            continue

        tree = _parse(py_file)

        # Find every ast.Compare with ast.Eq operator and claim_type on the left
        for node in ast.walk(tree):
            if isinstance(node, ast.Compare):
                # Check if any operator is ast.Eq
                if any(isinstance(op, ast.Eq) for op in node.ops):
                    # Check if left operand is Name or Attribute named "claim_type"
                    is_claim_type = False
                    if isinstance(node.left, ast.Name) and node.left.id == "claim_type":
                        is_claim_type = True
                    elif isinstance(node.left, ast.Attribute) and node.left.attr == "claim_type":
                        is_claim_type = True

                    # Check if any comparator is a string Constant
                    if is_claim_type:
                        for comp in node.comparators:
                            if isinstance(comp, ast.Constant) and isinstance(comp.value, str):
                                offenders.append(
                                    f"{py_file.name}:{node.lineno}: {ast.unparse(node)}"
                                )

    assert not offenders, (
        f"Found claim_type equality branches (move to model via tool calls): {offenders}"
    )
