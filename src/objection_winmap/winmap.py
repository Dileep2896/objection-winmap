from collections import Counter

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from .db import Meeting, RepRecord
from .schemas import BestResponse, WinMap, WinMapRow
from .stats import cohort_split, diff_interval
from .taxonomy import LABELS, TACTIC_RULES


def team_meetings(session: Session, team_id: str) -> list[Meeting]:
    return list(
        session.scalars(
            select(Meeting)
            .where(Meeting.team_id == team_id)
            .options(selectinload(Meeting.moments), joinedload(Meeting.rep))
            .order_by(Meeting.id)
        )
    )


def compute_winmap(session: Session, team_id: str, avg_deal_size: float = 12000) -> WinMap:
    meetings = team_meetings(session, team_id)
    counts = {}
    for m in meetings:
        wins, n = counts.get(m.rep_id, (0, 0))
        counts[m.rep_id] = wins + (m.outcome == "closed"), n + 1
    top, rest = cohort_split(counts)
    rows = []
    for objection in LABELS:
        affected = [m for m in meetings if any(o.objection == objection for o in m.moments)]
        first = [m for m in affected if m.rep_id in top]
        second = [m for m in affected if m.rep_id in rest]
        k1, k2 = (sum(m.outcome == "closed" for m in cohort) for cohort in (first, second))
        n1, n2 = len(first), len(second)
        p1, p2 = k1 / n1 if n1 else 0, k2 / n2 if n2 else 0
        low, high = diff_interval(k1, n1, k2, n2)
        responses = [
            (m, o)
            for m in first
            if m.outcome == "closed"
            for o in m.moments
            if o.objection == objection and o.rep_response
        ]
        responses.sort(key=lambda item: (-item[1].quality_score, item[0].id, item[1].ts))
        best = None
        if responses:
            meeting, moment = responses[0]
            best = BestResponse(
                rep_name=meeting.rep.name,
                meeting_id=meeting.id,
                ts=moment.response_ts,
                quote=moment.rep_response,
            )
        tactic_counts = []
        for cohort in (first, second):
            tactic_counts.append(
                Counter(
                    t
                    for m in cohort
                    for t in {t for o in m.moments if o.objection == objection for t in o.tactics}
                )
            )
        tactics = [
            t
            for t in TACTIC_RULES
            if tactic_counts[0][t]
            and tactic_counts[0][t] / (n1 or 1) > tactic_counts[1][t] / (n2 or 1)
        ]
        tactics.sort(
            key=lambda t: (
                -(tactic_counts[0][t] / (n1 or 1) - tactic_counts[1][t] / (n2 or 1)),
                list(TACTIC_RULES).index(t),
            )
        )
        rows.append(
            WinMapRow(
                objection=objection,
                occurrences=len(affected),
                top_occurrences=n1,
                rest_occurrences=n2,
                top_close_rate=p1,
                rest_close_rate=p2,
                gap=p1 - p2,
                gap_ci_low=low,
                gap_ci_high=high,
                est_revenue_lost=n2 * max(p1 - p2, 0) * avg_deal_size,
                best_response=best,
                top_tactics=tactics,
                sufficient_data=n1 >= 5 and n2 >= 5,
            )
        )
    rows.sort(key=lambda r: (-r.est_revenue_lost, r.objection))
    reps = list(session.scalars(select(RepRecord).where(RepRecord.team_id == team_id)))
    return WinMap(
        team_id=team_id,
        meeting_count=len(meetings),
        rep_count=len(reps),
        top_rep_ids=sorted(top),
        rows=rows,
    )
