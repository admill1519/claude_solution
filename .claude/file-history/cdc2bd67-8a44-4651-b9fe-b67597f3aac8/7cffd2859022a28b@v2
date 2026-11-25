"""Tool schemas and dispatcher.

Seven tools, registered with Anthropic tool-use shape. The dispatcher returns
serialized JSON strings to be wrapped as `tool_result` content. Errors follow
the "Graceful Tool Failure" shape:

    {"is_error": true,
     "error_category": "transient"|"permanent",
     "is_retryable": bool,
     "message": "..."}

Errors are never raised to the loop.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from claims_intake.session import ClaimSession

CLAIM_TYPES = ["property_damage", "theft", "liability", "auto"]
SEVERITIES = ["low", "medium", "high"]

# ----------------------------------------------------------------------------
# Schemas — passed verbatim to the Anthropic Messages API as the `tools` arg.
# ----------------------------------------------------------------------------

# TODO: Populate TOOL_SCHEMAS with the first four tool schemas. Each schema
# is a dict with "name", "description", and "input_schema". Tool descriptions are read by
# the model on every turn — write them as if you were teaching the model what each tool is
# for and *when* to call it. Categorical fields ("claim_type", "severity") must use
# Anthropic's tool-use `enum` shape against CLAIM_TYPES and SEVERITIES.
#
#   - lookup_policy(policy_id: str)
#     Returns the policy record. Used early in the conversation.
#   - record_claim_fact(field: str, value: str)
#     Records one normalized fact (incident_date, location, items_lost, ...).
#   - classify_claim(claim_type: enum CLAIM_TYPES, confidence: number in [0,1], rationale: str)
#     Commits the model to a claim type with a confidence score.
#   - assess_severity(severity: enum SEVERITIES, rationale: str)
#     Commits the model to a severity bucket.
#
# Later tools (request_clarification, route_to_adjuster, escalate_to_human) extend this list.
TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "lookup_policy",
        "description": "Retrieve a policy record by policy_id. Use this early in the conversation to understand the customer's coverage and deductible.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_id": {"type": "string", "description": "The policy ID to look up"}
            },
            "required": ["policy_id"],
        },
    },
    {
        "name": "record_claim_fact",
        "description": "Record a normalized fact about the claim (e.g., incident_date, location, items_lost). Call this repeatedly to build up the case facts.",
        "input_schema": {
            "type": "object",
            "properties": {
                "field": {"type": "string", "description": "The fact field name (e.g., 'location', 'incident_date')"},
                "value": {"type": "string", "description": "The fact value"},
            },
            "required": ["field", "value"],
        },
    },
    {
        "name": "classify_claim",
        "description": "Classify the claim into a type with a confidence score (0–1). This is a commit — once set, it guides the rest of the conversation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_type": {"type": "string", "enum": CLAIM_TYPES, "description": "The claim type"},
                "confidence": {"type": "number", "description": "Confidence score between 0 and 1"},
                "rationale": {"type": "string", "description": "Why you chose this type"},
            },
            "required": ["claim_type", "confidence", "rationale"],
        },
    },
    {
        "name": "assess_severity",
        "description": "Assess the claim severity (low, medium, high). This is a commit — routing and escalation decisions depend on it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "severity": {"type": "string", "enum": SEVERITIES, "description": "The severity level"},
                "rationale": {"type": "string", "description": "Why you chose this severity"},
            },
            "required": ["severity", "rationale"],
        },
    },
    {
        "name": "request_clarification",
        "description": "Ask the claimant a question to resolve ambiguity. If a matching scripted response exists, it is returned; otherwise 'NO_RESPONSE' is returned.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The question to ask the claimant"},
                "ambiguity_between": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of claim types under consideration",
                },
            },
            "required": ["question", "ambiguity_between"],
        },
    },
    {
        "name": "route_to_adjuster",
        "description": "Route the claim to an adjuster queue. This is a terminal action — the claim exits the loop.",
        "input_schema": {
            "type": "object",
            "properties": {
                "queue": {"type": "string", "enum": CLAIM_TYPES, "description": "The adjuster queue"},
                "claim_summary": {"type": "string", "description": "A brief summary of the claim"},
            },
            "required": ["queue", "claim_summary"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate the claim to a human for manual review. This is a terminal action — the claim exits the loop.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Reason for escalation (e.g., 'unresolved_ambiguity', 'policy_exception')"},
                "structured_summary": {
                    "type": "object",
                    "properties": {
                        "policy_id": {"type": "string"},
                        "root_cause": {"type": "string"},
                        "candidate_claim_types": {"type": "array", "items": {"type": "string"}},
                        "case_facts": {"type": "object"},
                        "recommended_action": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                    "required": [
                        "policy_id",
                        "root_cause",
                        "candidate_claim_types",
                        "case_facts",
                        "recommended_action",
                        "confidence",
                    ],
                },
            },
            "required": ["reason", "structured_summary"],
        },
    },
]

# ----------------------------------------------------------------------------
# Errors — Graceful Tool Failure shape
# ----------------------------------------------------------------------------


def _err(category: str, retryable: bool, message: str) -> str:
    return json.dumps({
        "is_error": True,
        "error_category": category,
        "is_retryable": retryable,
        "message": message,
    })


def _ok(payload: dict[str, Any]) -> str:
    return json.dumps(payload)


# ----------------------------------------------------------------------------
# Tool implementations
# ----------------------------------------------------------------------------


def _t_lookup_policy(session: ClaimSession, inp: dict[str, Any]) -> str:
    policy_id = inp.get("policy_id")
    if not isinstance(policy_id, str):
        return _err("permanent", False, "policy_id must be a string")
    policy = session.policies.get(policy_id)
    if policy is None:
        return _err("permanent", False, f"Policy {policy_id} not found")
    return _ok(policy)


def _t_record_claim_fact(session: ClaimSession, inp: dict[str, Any]) -> str:
    field = inp.get("field")
    value = inp.get("value")
    if not isinstance(field, str) or not isinstance(value, str):
        return _err("permanent", False, "field and value must be strings")
    session.case_facts[field] = value
    return _ok({
        "recorded": True,
        "field": field,
        "case_facts_count": len(session.case_facts),
    })


def _t_classify_claim(session: ClaimSession, inp: dict[str, Any]) -> str:
    claim_type = inp.get("claim_type")
    confidence = inp.get("confidence")
    rationale = inp.get("rationale")

    if claim_type not in CLAIM_TYPES:
        return _err("permanent", False, f"claim_type must be one of {CLAIM_TYPES}")
    if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
        return _err("permanent", False, "confidence must be a number between 0 and 1")
    if not isinstance(rationale, str):
        return _err("permanent", False, "rationale must be a string")

    session.classification = {
        "claim_type": claim_type,
        "confidence": confidence,
        "rationale": rationale,
    }
    return _ok({
        "recorded": True,
        "claim_type": claim_type,
        "confidence": confidence,
        "rationale": rationale,
    })


def _t_assess_severity(session: ClaimSession, inp: dict[str, Any]) -> str:
    severity = inp.get("severity")
    rationale = inp.get("rationale")

    if severity not in SEVERITIES:
        return _err("permanent", False, f"severity must be one of {SEVERITIES}")
    if not isinstance(rationale, str):
        return _err("permanent", False, "rationale must be a string")

    session.severity = {
        "severity": severity,
        "rationale": rationale,
    }
    return _ok({
        "recorded": True,
        "severity": severity,
        "rationale": rationale,
    })


def _t_request_clarification(session: ClaimSession, inp: dict[str, Any]) -> str:
    question = inp.get("question")
    ambiguity_between = inp.get("ambiguity_between")

    if not isinstance(question, str):
        return _err("permanent", False, "question must be a string")
    if not isinstance(ambiguity_between, list) or len(ambiguity_between) < 2:
        return _err("permanent", False, "ambiguity_between must be a list of at least 2 entries")

    # Record the clarification asked
    session.clarifications_asked.append({
        "question": question,
        "ambiguity_between": ambiguity_between,
    })

    # Try to find a matching response
    question_lower = question.lower()
    for key, response in session.clarification_responses.items():
        if key.lower() in question_lower:
            return _ok({"claimant_reply": response})

    return _ok({"claimant_reply": "NO_RESPONSE"})


def _t_route_to_adjuster(session: ClaimSession, inp: dict[str, Any]) -> str:
    # Guard against double-terminal
    if session.terminal_called:
        return _err("permanent", False, "Terminal action already called (routing or escalation)")

    queue = inp.get("queue")
    claim_summary = inp.get("claim_summary")

    # Validate inputs
    if queue not in CLAIM_TYPES:
        return _err("permanent", False, f"queue must be one of {CLAIM_TYPES}")
    if not isinstance(claim_summary, str):
        return _err("permanent", False, "claim_summary must be a string")

    # Require classification and severity
    if session.classification is None:
        return _err("permanent", False, "classify_claim must be called before routing")
    if session.severity is None:
        return _err("permanent", False, "assess_severity must be called before routing")

    # Build the routing record
    record = {
        "claim_id": session.claim_id,
        "policy_id": session.policy_id,
        "claim_type": session.classification["claim_type"],
        "severity": session.severity["severity"],
        "confidence": session.classification["confidence"],
        "rationale": session.classification["rationale"],
        "claim_summary": claim_summary,
        "case_facts": session.case_facts,
    }
    session.routing = record

    # Append to queue file
    queue_file = session.run_dir / "queues" / f"{queue}.jsonl"
    _append_jsonl(queue_file, record)

    return _ok({"routed": True, "queue": queue})


def _t_escalate_to_human(session: ClaimSession, inp: dict[str, Any]) -> str:
    # Guard against double-terminal
    if session.terminal_called:
        return _err("permanent", False, "Terminal action already called (routing or escalation)")

    reason = inp.get("reason")
    structured_summary = inp.get("structured_summary")

    # Validate reason
    if not isinstance(reason, str):
        return _err("permanent", False, "reason must be a string")

    # Validate structured_summary and check for required fields
    if not isinstance(structured_summary, dict):
        return _err("permanent", False, "structured_summary must be a dict")

    required_fields = {
        "policy_id",
        "root_cause",
        "candidate_claim_types",
        "case_facts",
        "recommended_action",
        "confidence",
    }
    missing = required_fields - set(structured_summary.keys())
    if missing:
        return _err("permanent", False, f"structured_summary missing fields: {', '.join(sorted(missing))}")

    # Build the escalation record
    record = {
        "claim_id": session.claim_id,
        "policy_id": session.policy_id,
        "reason": reason,
        **structured_summary,
        "case_facts_at_escalation": session.case_facts,
    }
    session.escalation = record

    # Append to escalations file
    esc_file = session.run_dir / "escalations.jsonl"
    _append_jsonl(esc_file, record)

    return _ok({"escalated": True})


# ----------------------------------------------------------------------------
# Dispatcher
# ----------------------------------------------------------------------------


_DISPATCH = {
    "lookup_policy": _t_lookup_policy,
    "record_claim_fact": _t_record_claim_fact,
    "classify_claim": _t_classify_claim,
    "assess_severity": _t_assess_severity,
    "request_clarification": _t_request_clarification,
    "route_to_adjuster": _t_route_to_adjuster,
    "escalate_to_human": _t_escalate_to_human,
}


def make_executor(session: ClaimSession) -> Executor:
    """Return a ToolExecutor callable bound to this session."""

    def execute(name: str, tool_input: dict[str, Any]) -> str:
        handler = _DISPATCH.get(name)
        if handler is None:
            return _err("permanent", False, f"unknown tool: {name}")
        try:
            return handler(session, tool_input)
        except Exception as exc:
            # Defensive: anything raised inside a handler becomes a graceful error,
            # never crashes the loop.
            return _err("transient", True, f"{type(exc).__name__}: {exc}")

    return execute


# Type alias for clarity; the loop only sees a Callable.
Executor = Any


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
