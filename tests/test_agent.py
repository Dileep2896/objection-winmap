import pytest

from objection_winmap.agent import HeuristicObjectionAgent
from objection_winmap.schemas import MeetingIn


@pytest.mark.parametrize(
    "text,expected",
    [
        ("I need to talk to my wife first.", "spouse/partner"),
        ("Can we talk it over with both of us?", "spouse/partner"),
        ("That is too expensive for our roof.", "price"),
        ("Our budget is stretched.", "price"),
        ("Let me think about it.", "think about it"),
        ("I want to sleep on it.", "think about it"),
        ("We have another quote for the shingles.", "competitor"),
        ("The other company is cheaper elsewhere.", "competitor"),
        ("Maybe next month.", "timing"),
        ("It is not the right time.", "timing"),
        ("How do I know you will finish?", "trust"),
        ("Do you have reviews?", "trust"),
        ("My husband wants another quote because of the price.", "spouse/partner"),
        ("The other company has a lower price.", "competitor"),
        ("The roof has hail damage.", None),
        ("The kitchen table is over here.", None),
    ],
)
def test_classifier(text, expected):
    assert HeuristicObjectionAgent.classify(text) == expected


def test_diarization_response_and_distinct_tactics():
    meeting = MeetingIn(
        rep_id="ben",
        team_id="summit",
        outcome="closed",
        utterances=[
            {"speaker": "rep", "ts": 0, "text": "My wife loved the new roof."},
            {"speaker": "customer", "ts": 10, "text": "I need to ask my wife."},
            {"speaker": "rep", "ts": 15, "text": "Totally understand. Can we call her?"},
            {
                "speaker": "rep",
                "ts": 20,
                "text": "Other than that, is there anything else? Totally understand.",
            },
            {"speaker": "customer", "ts": 25, "text": "Let me think about it."},
            {"speaker": "rep", "ts": 30, "text": "Makes sense."},
        ],
    )
    moments = HeuristicObjectionAgent().detect_objections(meeting)
    assert len(moments) == 2
    assert moments[0].ts == 10
    assert moments[0].response_ts == 15
    assert moments[0].rep_response == (
        "Totally understand. Can we call her? "
        "Other than that, is there anything else? Totally understand."
    )
    assert set(moments[0].tactics) == {"empathize", "include_decision_maker", "isolate"}
    assert moments[0].quality_score == 3.5


def test_no_response_does_not_borrow_from_later_objection():
    meeting = MeetingIn(
        rep_id="ben",
        team_id="summit",
        outcome="lost",
        utterances=[
            {"speaker": "customer", "ts": 0, "text": "My wife is not here."},
            {"speaker": "customer", "ts": 2, "text": "It is too expensive."},
            {"speaker": "rep", "ts": 4, "text": "It is $200 per month."},
        ],
    )
    moments = HeuristicObjectionAgent().detect_objections(meeting)
    assert moments[0].rep_response == ""
    assert moments[1].tactics == ["reframe_monthly"]
