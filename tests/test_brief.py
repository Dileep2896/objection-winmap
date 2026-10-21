import pytest

from objection_winmap.brief import choose_focus, compute_brief
from objection_winmap.db import Meeting, RepRecord


def test_ben_brief_is_verbatim_and_cited(session):
    brief = compute_brief(session, "ben")
    assert brief.rep.name == "Ben K."
    assert brief.focus_objection == "spouse/partner"
    assert brief.your_close_rate == pytest.approx(1 / 5)
    assert brief.top_close_rate == pytest.approx(7 / 12)
    assert brief.missing_tactic == "include_decision_maker"
    source = session.get(Meeting, brief.practice_source.meeting_id)
    assert source.outcome == "closed"
    transcript = " ".join(u.text for u in source.utterances if u.speaker == "rep")
    assert brief.practice_line in transcript
    assert brief.evidence
    assert all(session.get(Meeting, e.meeting_id).outcome == "lost" for e in brief.evidence)
    assert all(session.get(Meeting, e.meeting_id).rep_id == "ben" for e in brief.evidence)


def test_focus_weighting_and_alphabetical_tie():
    assert choose_focus([("price", 0.2, 5), ("spouse/partner", 0.3, 4)]) == "spouse/partner"
    assert choose_focus([("trust", 0.5, 2), ("price", 0.2, 5)]) == "price"
    assert choose_focus([("price", -0.1, 5)]) is None
    assert choose_focus([]) is None


def test_unknown_and_no_data(session):
    with pytest.raises(LookupError):
        compute_brief(session, "nobody")
    session.add(RepRecord(id="new", name="New R.", team_id="summit"))
    session.commit()
    brief = compute_brief(session, "new")
    assert brief.focus_objection is None
    assert brief.evidence == []
