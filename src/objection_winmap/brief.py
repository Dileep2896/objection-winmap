from sqlalchemy.orm import Session

from .db import RepRecord
from .schemas import DailyBrief, Evidence, Rep
from .taxonomy import DRILLS
from .winmap import compute_winmap, team_meetings


def choose_focus(candidates: list[tuple[str, float, int]]) -> str | None:
    positive = [
        (objection, gap * frequency)
        for objection, gap, frequency in candidates
        if gap > 0 and frequency > 0
    ]
    return min(positive, key=lambda item: (-round(item[1], 12), item[0]))[0] if positive else None


def compute_brief(session: Session, rep_id: str) -> DailyBrief:
    rep = session.get(RepRecord, rep_id)
    if not rep:
        raise LookupError("Rep not found.")
    result = DailyBrief(rep=Rep.model_validate(rep))
    winmap = compute_winmap(session, rep.team_id)
    meetings = [m for m in team_meetings(session, rep.team_id) if m.rep_id == rep_id]
    rates, affected, candidates = {}, {}, []
    for row in winmap.rows:
        subset = [m for m in meetings if any(o.objection == row.objection for o in m.moments)]
        if not row.sufficient_data or not subset or not row.best_response:
            continue
        rate = sum(m.outcome == "closed" for m in subset) / len(subset)
        rates[row.objection], affected[row.objection] = rate, subset
        candidates.append((row.objection, row.top_close_rate - rate, len(subset)))
    focus = choose_focus(candidates)
    if not focus:
        return result
    row = next(r for r in winmap.rows if r.objection == focus)
    own_tactics = {
        t for m in affected[focus] for o in m.moments if o.objection == focus for t in o.tactics
    }
    result.focus_objection = focus
    result.your_close_rate = rates[focus]
    result.top_close_rate = row.top_close_rate
    result.practice_line = row.best_response.quote
    result.practice_source = row.best_response
    result.missing_tactic = next((t for t in row.top_tactics if t not in own_tactics), None)
    result.drill = DRILLS[focus]
    losses = sorted(
        (m for m in affected[focus] if m.outcome == "lost"),
        key=lambda m: (m.occurred_at, m.id),
        reverse=True,
    )
    for meeting in losses[:3]:
        moment = next(o for o in meeting.moments if o.objection == focus)
        result.evidence.append(
            Evidence(
                meeting_id=meeting.id,
                ts=moment.ts,
                customer_name=meeting.customer_name,
                quote=moment.customer_quote,
                response=moment.rep_response,
            )
        )
    return result
