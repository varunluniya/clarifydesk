"""
clarifydesk: a versioned prompt template registry plus a two-stage defensive
parser/validator for structured ticket extraction (category, urgency,
summary).

DISCLOSURE: no live LLM API is called anywhere in this package. Wherever a
"raw model output" is needed to demonstrate the parser/validator, it is a
deterministic, hand-written string chosen to be representative of a real
model's plausible output -- including specific disclosed failure modes
(a markdown code fence, stray preamble text, an out-of-schema value) -- not
a captured live response.
"""
import json
import re

ALLOWED_CATEGORIES = {"ACCOUNT", "BILLING", "BUG", "FEATURE_REQUEST", "OTHER"}

PROMPT_VERSIONS = {
    "ticket_extract_v1": {
        "template": (
            "Extract the following fields from the support ticket below and "
            "respond with a JSON object.\n\nSchema:\n{{...}}\n\nTicket:\n\"{ticket_text}\"\n"
        ),
        "created": "2026-11-05",
        "notes": ("Initial version. States the schema but gives no explicit "
                  "no-preamble/no-code-fence instruction and no worked example."),
    },
    "ticket_extract_v2": {
        "template": (
            "Extract fields ... Respond with ONLY the JSON object -- no markdown "
            "code fences, no explanation, no text before or after it.\n\nSchema:\n{{...}}\n\n"
            "Example:\nTicket: \"...double-charged...\"\n{{\"category\": \"BILLING\", ...}}\n\n"
            "Ticket:\n\"{ticket_text}\"\n"
        ),
        "created": "2026-11-05",
        "notes": ("Added an explicit output-indicator instruction plus a one-shot "
                  "worked example to lock the exact format."),
    },
}
ACTIVE_VERSION = "ticket_extract_v2"


def parse_json_response(raw_response: str) -> dict:
    """Defensive parser: strip a markdown code fence if present, then locate
    the first {...} object even amid stray prose, then attempt to parse it."""
    cleaned = raw_response.strip()
    cleaned = re.sub(r"```(?:json)?", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if not match:
        return {"error": "no JSON object found", "raw": raw_response}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {"error": "invalid JSON", "raw": raw_response}


def validate_and_route(parsed: dict) -> dict:
    """Content-level validation, deliberately separate from parsing: a
    response can parse as perfectly valid JSON and still be unusable
    (out-of-schema category, non-integer urgency, missing/oversized summary)."""
    if "error" in parsed:
        return {**parsed, "needs_human_review": True, "reason": parsed["error"]}
    issues = []
    if parsed.get("category") not in ALLOWED_CATEGORIES:
        issues.append(f"category '{parsed.get('category')}' not in {sorted(ALLOWED_CATEGORIES)}")
    urgency = parsed.get("urgency")
    if not isinstance(urgency, int) or not (1 <= urgency <= 5):
        issues.append(f"urgency '{urgency}' is not an integer in 1..5")
    summary = parsed.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        issues.append("summary is missing or empty")
    elif len(summary.split()) > 15:
        issues.append(f"summary is {len(summary.split())} words, over the 15-word limit")
    if issues:
        return {**parsed, "needs_human_review": True, "reason": "; ".join(issues)}
    return {**parsed, "needs_human_review": False}
