from .core import parse_json_response, validate_and_route

DEMO_RAW_RESPONSES = [
    ("fenced + prefaced (v1 realistic failure)",
     'Here is the extracted ticket data:\n```json\n{"category": "BUG", "urgency": 5, '
     '"summary": "Production API returns 500 errors for all customers since this morning\'s deploy."}\n```'),
    ("clean (v2 happy path)",
     '{"category": "FEATURE_REQUEST", "urgency": 2, "summary": "Customer wants CSV export added to the monthly usage report."}'),
    ("valid JSON, invalid content (messy case)",
     '{"category": "ESCALATION", "urgency": "very high", "summary": "Enterprise customer threatening to churn over repeated outages."}'),
]


def main():
    for label, raw in DEMO_RAW_RESPONSES:
        parsed = parse_json_response(raw)
        routed = validate_and_route(parsed)
        print(f"\n--- {label} ---\nraw: {raw}\nrouted: {routed}")


if __name__ == "__main__":
    main()
