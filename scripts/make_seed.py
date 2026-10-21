"""Generate fictional kitchen-table meetings with a fixed, independently labeled design."""

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "seed"
RNG = random.Random(260621)
REPS = [
    ("ethan", "Ethan R."),
    ("sophia", "Sophia L."),
    ("ben", "Ben K."),
    ("ryan", "Ryan C."),
    ("michael", "Michael B."),
    ("olivia", "Olivia M."),
    ("james", "James T."),
    ("ava", "Ava D."),
    ("noah", "Noah S."),
    ("mia", "Mia P."),
]
QUESTIONS = {
    "spouse/partner": [
        "I need to talk to my wife before we sign anything for the roof.",
        "My husband handles the big decisions. He is at work right now.",
        "My partner should hear this too. It is a big decision for both of us.",
    ],
    "price": [
        "That is too expensive with the deductible we already paid.",
        "Our budget is stretched after replacing the water heater.",
        "I cannot afford that amount for shingles right now.",
    ],
    "think about it": [
        "I need to think about it before signing.",
        "Can we sleep on it? This is a big commitment.",
        "Not today. I want a little space to decide.",
    ],
    "competitor": [
        "We have another quote coming in on Thursday.",
        "The other company offered the same shingles for less.",
        "I got a quote from a roofer my brother knows.",
    ],
    "timing": [
        "Could we wait until next month to do the roof?",
        "It is not the right time with school starting.",
        "We were hoping to wait until next year.",
    ],
    "trust": [
        "How do I know your crew will finish before the rain?",
        "Do you have reviews from homeowners near us?",
        "What guarantee do I get on the workmanship?",
    ],
}
TOP = {
    "spouse/partner": "Totally understand. This is a decision for both of you. Could we "
    "call her and walk through the photos together? Other than that, "
    "is there anything else keeping you from moving forward?",
    "price": "Makes sense. The financing option is $189 per month. Other than that, "
    "is there anything else about the scope that worries you?",
    "think about it": "Totally understand. Other than that, is there anything else "
    "you would need to feel comfortable with the roof?",
    "competitor": "Makes sense. Your neighbors on your street used our crew; "
    "we can compare the flashing and disposal line by line.",
    "timing": "Makes sense. This week's install slot is still available, but we can "
    "schedule after your trip if that works better.",
    "trust": "Totally understand. Your neighbors on your street can tell you about "
    "our crew, and I can show you the written workmanship coverage.",
}
REST = {
    "spouse/partner": "I could take $500 off if you sign today. Otherwise I can leave "
    "the estimate here and check back with you.",
    "price": "I could ask my manager if there is room to take a little off the total.",
    "think about it": "Sure. I will leave my card and give you a call next week.",
    "competitor": "I think our work is better. I could ask about matching their number.",
    "timing": "Okay, I can check back with you in a few weeks.",
    "trust": "We have been doing this a long time. You will be fine.",
}


def generate():
    ROOT.mkdir(exist_ok=True)
    (ROOT / "transcripts").mkdir(exist_ok=True)
    team = {
        "id": "summit",
        "name": "Summit Roofing Co.",
        "avg_deal_size": 12000,
        "reps": [{"id": i, "name": n, "team_id": "summit"} for i, n in REPS],
    }
    (ROOT / "team.json").write_text(json.dumps(team, indent=2) + "\n")
    records = []
    for index, (rep, _) in enumerate(REPS):
        count = 12 if index < 2 else 6
        wins = [7, 6, 1, 2, 2, 2, 1, 1, 1, 1][index]
        for j in range(count):
            records.append(
                {
                    "id": f"{rep}-{j + 1:02}",
                    "rep_id": rep,
                    "top": index < 2,
                    "outcome": "closed" if j < wins else "lost",
                    "objections": [],
                }
            )

    def assign(objection, top, wins, losses, mandatory=()):
        chosen = [r for r in records if r["id"] in mandatory]
        for outcome, target in [("closed", wins), ("lost", losses)]:
            pool = [
                r
                for r in records
                if r["top"] == top
                and r["outcome"] == outcome
                and r not in chosen
                and (top or r["rep_id"] != "ben")
            ]
            RNG.shuffle(pool)
            used = sum(r["outcome"] == outcome for r in chosen)
            chosen.extend(pool[: target - used])
        for r in chosen:
            r["objections"].append(objection)

    assign("spouse/partner", True, 7, 5)
    assign("spouse/partner", False, 3, 13, ["ben-01", "ben-02", "ben-03", "ben-04", "ben-05"])
    assign("price", True, 5, 5)
    assign("price", False, 6, 14, ["ben-02", "ben-06"])
    assign("think about it", True, 5, 5)
    assign("think about it", False, 3, 13, ["ben-03"])
    for objection, n in [("competitor", 4), ("timing", 3), ("trust", 4)]:
        assign(objection, True, 2, n - 2)
        assign(objection, False, 2, n + 2)

    labels = []
    first_names = ["Jordan", "Casey", "Morgan", "Taylor", "Alex", "Jamie", "Sam", "Drew"]
    streets = ["Oak Lane", "Maple Drive", "Cedar Court", "Pine Street", "Willow Way"]
    for index, record in enumerate(records):
        utterances = []

        def say(speaker, ts, text, objection=None, utterances=utterances, record=record):
            utterances.append({"speaker": speaker, "ts": ts, "text": text})
            if speaker == "customer":
                labels.append(
                    {"meeting_id": record["id"], "ts": ts, "text": text, "objection": objection}
                )

        say("rep", 0, "Thanks for having me over. Let us look at the inspection photos together.")
        say(
            "customer",
            14,
            "The hail came through Tuesday. We found shingle pieces by the driveway.",
        )
        say(
            "rep",
            32,
            "There is bruising on the south slope and some lifted flashing by the chimney.",
        )
        say("customer", 51, "The insurance adjuster was here yesterday and left this report.")
        say(
            "rep",
            75,
            "We will replace the decking where needed and use 25-year architectural "
            "shingles. Cleanup and the magnetic nail sweep are included.",
        )
        for j, objection in enumerate(record["objections"]):
            ts = 125 + j * 110
            say("customer", ts, RNG.choice(QUESTIONS[objection]), objection)
            say("rep", ts + 18, (TOP if record["top"] else REST)[objection])
        end = 160 + len(record["objections"]) * 110
        say("customer", end, "I appreciate you walking me through the photos.")
        say("rep", end + 15, "I will put the full scope and the material list in writing for you.")
        say(
            "customer",
            end + 32,
            "All right, let us get the paperwork started."
            if record["outcome"] == "closed"
            else "I am going to hold off on signing anything.",
        )
        payload = {k: v for k, v in record.items() if k not in ("top", "objections")}
        payload.update(
            team_id="summit",
            customer_name=first_names[index % 8] + " · " + streets[index % 5],
            deal_value=RNG.randrange(11000, 18001, 500),
            occurred_at=f"2026-10-{index % 20 + 1:02}T14:30:00Z",
            utterances=utterances,
        )
        (ROOT / "transcripts" / f"{record['id']}.json").write_text(
            json.dumps(payload, indent=2) + "\n"
        )
    (ROOT / "labels.json").write_text(json.dumps(labels, indent=2) + "\n")
    print(f"Generated {len(records)} meetings and {len(labels)} gold utterance labels.")


if __name__ == "__main__":
    generate()
