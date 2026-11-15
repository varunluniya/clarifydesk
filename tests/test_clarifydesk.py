from clarifydesk.core import PROMPT_VERSIONS, ACTIVE_VERSION, parse_json_response, validate_and_route


def test_two_versions_registered():
    assert set(PROMPT_VERSIONS) == {"ticket_extract_v1", "ticket_extract_v2"}


def test_active_version_points_at_v2():
    assert ACTIVE_VERSION == "ticket_extract_v2"


def test_v1_lacks_no_fence_instruction_v2_has_it():
    assert "ONLY" not in PROMPT_VERSIONS["ticket_extract_v1"]["template"]
    assert "ONLY" in PROMPT_VERSIONS["ticket_extract_v2"]["template"]


def test_parser_strips_code_fence_and_preamble():
    raw = 'Here is the data:\n```json\n{"category": "BUG", "urgency": 5, "summary": "x"}\n```'
    parsed = parse_json_response(raw)
    assert parsed == {"category": "BUG", "urgency": 5, "summary": "x"}


def test_parser_returns_error_for_unparseable_input():
    parsed = parse_json_response("not json at all, no braces")
    assert parsed["error"] == "no JSON object found"


def test_parser_returns_error_for_malformed_json():
    parsed = parse_json_response("{not: valid json}")
    assert parsed["error"] == "invalid JSON"


def test_validate_passes_clean_case():
    parsed = {"category": "FEATURE_REQUEST", "urgency": 2, "summary": "short summary"}
    routed = validate_and_route(parsed)
    assert routed["needs_human_review"] is False


def test_validate_flags_invalid_category():
    parsed = {"category": "ESCALATION", "urgency": 3, "summary": "ok"}
    routed = validate_and_route(parsed)
    assert routed["needs_human_review"] is True
    assert "category" in routed["reason"]


def test_validate_flags_non_integer_urgency():
    parsed = {"category": "BUG", "urgency": "very high", "summary": "ok"}
    routed = validate_and_route(parsed)
    assert routed["needs_human_review"] is True
    assert "urgency" in routed["reason"]


def test_validate_flags_oversized_summary():
    parsed = {"category": "BUG", "urgency": 3, "summary": " ".join(["word"] * 20)}
    routed = validate_and_route(parsed)
    assert routed["needs_human_review"] is True
    assert "15-word" in routed["reason"]


def test_valid_json_but_invalid_content_still_flagged():
    # Demonstrates parsing and validation are distinct defenses.
    parsed = parse_json_response('{"category": "ESCALATION", "urgency": "very high", "summary": "ok"}')
    assert "error" not in parsed  # parses fine
    routed = validate_and_route(parsed)
    assert routed["needs_human_review"] is True  # but content is invalid
