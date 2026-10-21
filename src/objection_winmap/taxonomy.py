import re

# Specific categories precede generic price language; one label per utterance.
OBJECTION_RULES = {
    "spouse/partner": r"\b(my (wife|husband|partner)|talk (it )?over with|both of us)\b",
    "competitor": r"\b(another quote|other company|cheaper elsewhere|quote from)\b",
    "price": r"\b(too (expensive|much)|price|cost|budget|afford)\b",
    "think about it": r"\b(think about it|sleep on it|not today)\b",
    "timing": r"\b(next (month|year)|not the right time|later)\b",
    "trust": r"\b(reviews|scam|how do I know|guarantee)\b",
}
PATTERNS = {key: re.compile(value, re.I) for key, value in OBJECTION_RULES.items()}
TACTIC_RULES = {
    "include_decision_maker": r"\b(call (her|him|them)|join us|three-way)\b",
    "isolate": r"\bother than that,? is there anything else\b",
    "reframe_monthly": r"\b(per month|a day)\b",
    "social_proof": r"\b(neighbors|on your street)\b",
    "empathize": r"\b(totally understand|makes sense)\b",
    "urgency_honest": r"\bthis week[’']s install slot\b",
}
LABELS = {
    "spouse/partner": "Spouse / partner",
    "price": "Price",
    "think about it": "Think about it",
    "competitor": "Competitor",
    "timing": "Timing",
    "trust": "Trust",
}
TACTIC_LABELS = {
    "include_decision_maker": "Include the decision-maker",
    "isolate": "Isolate the objection",
    "reframe_monthly": "Reframe the monthly cost",
    "social_proof": "Use local social proof",
    "empathize": "Acknowledge the concern",
    "urgency_honest": "Offer honest urgency",
}
FOCUS_NOTES = {
    "spouse/partner": "The person who isn’t in the room can still be part of the conversation.",
    "price": "Help the homeowner understand what the investment looks like in everyday terms.",
    "think about it": "Find the unresolved concern behind the request for more time.",
    "competitor": "Make the differences in scope concrete before discussing a discount.",
    "timing": "Understand the timing constraint and offer a realistic next step.",
    "trust": "Give the homeowner evidence they can verify, from people they recognize.",
}
DRILLS = {
    "spouse/partner": "Ask a teammate to play the absent partner; practice inviting them "
    "into a three-way call, then isolate any remaining concern.",
    "price": "Practice explaining the monthly payment, then ask which part feels out of reach.",
    "think about it": "Ask a teammate to say “I need to think”; "
    "uncover the one unresolved concern.",
    "competitor": "Compare two roofing scopes aloud, using one local customer example.",
    "timing": "Practice offering a real installation window without inventing a deadline.",
    "trust": "Practice offering a neighbor reference and explaining the written warranty.",
}
