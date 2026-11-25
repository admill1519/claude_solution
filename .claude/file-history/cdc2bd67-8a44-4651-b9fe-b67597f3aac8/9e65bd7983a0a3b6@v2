"""Deterministic tool-output pruning for the verbose `lookup_order` response.

The "Tool Context Pruning" pattern: application-side filtering
of a verbose tool result so only the fields needed for the immediate decision survive
into context. For return/refund reasoning, exactly five fields matter — order identity,
when it was placed, what it cost, whether it shipped, and the return-window deadline.

# Why each kept field is the only one that matters for return/refund reasoning:
#   - order_id: Uniquely identifies the order for routing and refund processing.
#   - order_date: Determines if the order falls within the return eligibility window.
#   - order_total_usd: Caps the maximum refund amount the agent can approve.
#   - fulfillment_status: Determines whether to issue a refund (delivered) vs. cancel (not shipped).
#   - return_eligible_until: Deadline for the agent to approve a return; if exceeded, deny.

Implementation: deterministic field selection (no LLM call). The pruner has no
`anthropic` import — enforced by an AST audit.
"""
from __future__ import annotations

KEPT_FIELDS: tuple[str, ...] = (
    "order_id",
    "order_date",
    "order_total_usd",
    "fulfillment_status",
    "return_eligible_until",
)


class PrunerMissingFieldError(KeyError):
    """Raised when the raw tool response is missing one of the required kept fields."""


def prune_lookup_order(raw: dict) -> dict:
    """Prune the raw lookup_order response to exactly the 5 required fields.

    Args:
        raw: The raw 57-field order lookup response from the tool.

    Returns:
        A new dict with only the KEPT_FIELDS in their declaration order.

    Raises:
        PrunerMissingFieldError: If any required field is missing from the raw response.
    """
    # Check that every required field is present.
    missing = [field for field in KEPT_FIELDS if field not in raw]
    if missing:
        raise PrunerMissingFieldError(f"Missing required fields: {missing}")

    # Return a new dict with only the kept fields, in their declaration order.
    return {field: raw[field] for field in KEPT_FIELDS}
