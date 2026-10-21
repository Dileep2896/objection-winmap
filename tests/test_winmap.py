import pytest

from objection_winmap.db import Meeting, RepRecord, save_meeting
from objection_winmap.schemas import MeetingIn
from objection_winmap.seed import seed_database
from objection_winmap.winmap import compute_winmap


def test_seed_story_and_rates(session):
    result = compute_winmap(session, "summit")
    assert len(result.rows) == 6
    assert set(result.top_rep_ids) == {"ethan", "sophia"}
    spouse = result.rows[0]
    assert spouse.objection == "spouse/partner"
    assert spouse.top_close_rate == pytest.approx(7 / 12)
    assert spouse.rest_close_rate == pytest.approx(3 / 16)
    assert spouse.occurrences == 28
    assert spouse.est_revenue_lost == pytest.approx(76000)
    assert spouse.sufficient_data
    assert spouse.gap_ci_low < spouse.gap < spouse.gap_ci_high
    assert spouse.best_response
    assert session.get(Meeting, spouse.best_response.meeting_id).outcome == "closed"
    assert "include_decision_maker" in spouse.top_tactics
    assert result.rows == sorted(result.rows, key=lambda r: -r.est_revenue_lost)


def test_min_sample_and_revenue_configuration(session):
    result = compute_winmap(session, "summit", avg_deal_size=6000)
    assert result.rows[0].est_revenue_lost == pytest.approx(38000)
    assert not next(r for r in result.rows if r.objection == "trust").sufficient_data


def test_seed_idempotent(session):
    before = session.query(Meeting).count()
    seed_database(session)
    assert session.query(Meeting).count() == before == 72


def test_unranked_rep_counts_occurrences_only_and_repeated_objections_once(session):
    session.add(RepRecord(id="rookie", name="New R.", team_id="summit"))
    session.commit()
    before = compute_winmap(session, "summit").rows[0]
    save_meeting(
        session,
        MeetingIn(
            rep_id="rookie",
            team_id="summit",
            outcome="closed",
            utterances=[
                {"speaker": "customer", "ts": t, "text": "My wife needs to see this."}
                for t in [0, 10]
            ],
        ),
    )
    result = compute_winmap(session, "summit")
    after = result.rows[0]
    assert after.occurrences == before.occurrences + 1
    assert after.top_close_rate == before.top_close_rate
    assert after.rest_close_rate == before.rest_close_rate
    assert "rookie" not in result.top_rep_ids


def test_team_isolation(session):
    result = compute_winmap(session, "unknown")
    assert result.meeting_count == 0
    assert all(r.occurrences == 0 and not r.sufficient_data for r in result.rows)


def test_best_quote_is_highest_quality_eligible_won_response(session):
    from objection_winmap.winmap import team_meetings

    result = compute_winmap(session, "summit")
    for row in result.rows:
        candidates = [
            (m, o)
            for m in team_meetings(session, "summit")
            if m.rep_id in result.top_rep_ids and m.outcome == "closed"
            for o in m.moments
            if o.objection == row.objection and o.rep_response
        ]
        expected = min(
            candidates, key=lambda item: (-item[1].quality_score, item[0].id, item[1].ts)
        )
        assert row.best_response.meeting_id == expected[0].id
        assert row.best_response.quote == expected[1].rep_response
