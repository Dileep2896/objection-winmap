import re
from typing import Protocol

from .schemas import MeetingIn, ObjectionMoment
from .taxonomy import PATTERNS, TACTIC_RULES


class ObjectionAgent(Protocol):
    """Typed seam for a PydanticAI agent; no provider keys needed by the demo."""

    output_type = list[ObjectionMoment]

    def detect_objections(self, meeting: MeetingIn) -> list[ObjectionMoment]: ...


class HeuristicObjectionAgent:
    output_type = list[ObjectionMoment]

    @staticmethod
    def classify(text: str) -> str | None:
        return next((name for name, rule in PATTERNS.items() if rule.search(text)), None)

    def detect_objections(self, meeting: MeetingIn) -> list[ObjectionMoment]:
        moments = []
        for i, utterance in enumerate(meeting.utterances):
            objection = self.classify(utterance.text) if utterance.speaker == "customer" else None
            if not objection:
                continue
            replies = []
            for following in meeting.utterances[i + 1 :]:
                if following.speaker == "customer" and self.classify(following.text):
                    break
                if following.speaker == "rep":
                    replies.append(following)
                if len(replies) == 2:
                    break
            response = " ".join(u.text for u in replies)
            tactics = [
                name for name, rule in TACTIC_RULES.items() if re.search(rule, response, re.I)
            ]
            moments.append(
                ObjectionMoment(
                    objection=objection,
                    ts=utterance.ts,
                    customer_quote=utterance.text,
                    response_ts=replies[0].ts if replies else None,
                    rep_response=response,
                    tactics=tactics,
                    quality_score=len(tactics) + 0.5 * (meeting.outcome == "closed"),
                )
            )
        return moments
