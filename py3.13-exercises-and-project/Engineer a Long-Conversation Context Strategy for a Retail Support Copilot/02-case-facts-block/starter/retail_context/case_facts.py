"""Case-facts extraction into a persistent block at the top of context.

Extraction is LLM-driven: one Claude call against the full transcript that returns
strict JSON for the 12 required fields. This is commonly called a *scratchpad* — same
concept, different word: a dense structured block that survives compression and is
placed at the top boundary of context so the model can recover transactional facts
without scanning thousands of tokens of narrative.

Missing-field behavior raises `CaseFactExtractionError` listing the gaps — silent
null-fill is forbidden.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from retail_context.client import complete_with_system, get_model
from retail_context.transcript import Transcript

REQUIRED_FIELDS: tuple[str, ...] = (
    "customer_id",
    "refund_order_id",
    "refund_amount_usd",
    "refund_status",
    "subscription_id",
    "subscription_plan",
    "subscription_cancel_reason",
    "subscription_status",
    "active_payment_method_last4",
    "new_payment_method_last4",
    "payment_update_failure_code",
    "payment_update_status",
)


@dataclass
class CaseFacts:
    """Extracted case facts from a support transcript."""

    customer_id: str
    refund_order_id: str
    refund_amount_usd: float
    refund_status: str
    subscription_id: str
    subscription_plan: str
    subscription_cancel_reason: str
    subscription_status: str
    active_payment_method_last4: str
    new_payment_method_last4: str
    payment_update_failure_code: str
    payment_update_status: str

    def to_markdown(self) -> str:
        """Render the case facts as a Markdown block with group labels."""
        lines = ["# Case Facts", ""]

        # Customer group
        lines.append(f"**Customer**: {self.customer_id}")

        # Refund group
        lines.append(f"**Refund (resolved)**: order {self.refund_order_id}, ${self.refund_amount_usd:.2f}, {self.refund_status}")

        # Subscription group
        lines.append(f"**Subscription (resolved)**: {self.subscription_id}, plan {self.subscription_plan}, cancelled ({self.subscription_cancel_reason}), {self.subscription_status}")

        # Payment group
        lines.append(f"**Payment update (active)**: {self.active_payment_method_last4} → {self.new_payment_method_last4}, {self.payment_update_failure_code}, {self.payment_update_status}")

        return "\n".join(lines)


class CaseFactExtractionError(ValueError):
    def __init__(self, missing: list[str], raw: dict[str, Any]):
        super().__init__(f"case-facts extraction missing required fields: {missing}")
        self.missing = missing
        self.raw = raw


_SYSTEM_PROMPT = """You are a case-facts extractor. Your job is to read a support transcript and extract 12 required fields into a strict JSON object.

Required output format: return ONLY a JSON object with these 12 keys:
{
  "customer_id": <string or null>,
  "refund_order_id": <string or null>,
  "refund_amount_usd": <number or null>,
  "refund_status": <string or null>,
  "subscription_id": <string or null>,
  "subscription_plan": <string or null>,
  "subscription_cancel_reason": <string or null>,
  "subscription_status": <string or null>,
  "active_payment_method_last4": <string or null>,
  "new_payment_method_last4": <string or null>,
  "payment_update_failure_code": <string or null>,
  "payment_update_status": <string or null>
}

Extraction rules:
- customer_id: Unique identifier for the customer. String.
- refund_order_id: The order ID related to a refund request. String.
- refund_amount_usd: The refund amount in USD. Must be a number (not a string).
- refund_status: Status of the refund (e.g., "approved", "pending", "denied"). Preserve the exact status token from the transcript.
- subscription_id: Unique identifier for the subscription. String.
- subscription_plan: Name/type of the subscription plan. String.
- subscription_cancel_reason: Reason given for subscription cancellation. String.
- subscription_status: Status of the subscription (e.g., "active", "cancelled", "suspended"). Preserve the exact status token from the transcript.
- active_payment_method_last4: Last 4 digits of the currently active payment method. Zero-padded string (e.g., "0042").
- new_payment_method_last4: Last 4 digits of a new payment method being added. Zero-padded string (e.g., "0042").
- payment_update_failure_code: Error/failure code for a payment update attempt. Preserve verbatim.
- payment_update_status: Status of the payment update (e.g., "failed", "pending", "success"). Preserve the exact status token from the transcript.

Important:
- If a field is not mentioned in the transcript, set it to null. DO NOT invent or guess values.
- Output ONLY the JSON object. No prose, no markdown, no code fences, no explanation.
- Status tokens (like "approved", "pending", "denied") must be preserved exactly as they appear in the transcript.
"""


def _parse_json(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.rstrip().endswith("```"):
            raw = raw.rsplit("```", 1)[0]
    return json.loads(raw)


def extract(
    transcript: Transcript,
    *,
    model: str | None = None,
    log_path: Path | None = None,
) -> CaseFacts:
    # 1. Build the user message
    user = f"Transcript:\n\n{transcript.full_text}"

    # 2. Call complete_with_system to get extraction
    text, input_tokens, output_tokens = complete_with_system(
        _SYSTEM_PROMPT,
        user,
        model=model,
        max_tokens=2048,
    )

    # 3. Parse the response text
    parsed = _parse_json(text)

    # 4. Write audit log if log_path was given
    if log_path:
        actual_model = model or get_model()
        log_data = {
            "model": actual_model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "raw": parsed,
        }
        log_path.write_text(json.dumps(log_data, indent=2))

    # 5. Validate that all required fields are present, non-null, non-empty
    missing = []
    for field_name in REQUIRED_FIELDS:
        value = parsed.get(field_name)
        if value is None or value == "":
            missing.append(field_name)

    if missing:
        raise CaseFactExtractionError(missing=missing, raw=parsed)

    # 6. Construct and return CaseFacts with explicit type casting
    return CaseFacts(
        customer_id=str(parsed["customer_id"]),
        refund_order_id=str(parsed["refund_order_id"]),
        refund_amount_usd=float(parsed["refund_amount_usd"]),
        refund_status=str(parsed["refund_status"]),
        subscription_id=str(parsed["subscription_id"]),
        subscription_plan=str(parsed["subscription_plan"]),
        subscription_cancel_reason=str(parsed["subscription_cancel_reason"]),
        subscription_status=str(parsed["subscription_status"]),
        active_payment_method_last4=str(parsed["active_payment_method_last4"]),
        new_payment_method_last4=str(parsed["new_payment_method_last4"]),
        payment_update_failure_code=str(parsed["payment_update_failure_code"]),
        payment_update_status=str(parsed["payment_update_status"]),
    )


def to_dict(facts: CaseFacts) -> dict[str, Any]:
    return asdict(facts)
