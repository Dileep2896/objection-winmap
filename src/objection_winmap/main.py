import math
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .brief import compute_brief
from .db import Base, Meeting, RepRecord, make_engine, save_meeting
from .schemas import DailyBrief, MeetingIn, ObjectionMoment, WinMap
from .seed import seed_database
from .taxonomy import FOCUS_NOTES, LABELS, TACTIC_LABELS
from .winmap import compute_winmap

PACKAGE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=PACKAGE / "templates")
templates.env.filters["pct"] = lambda v: f"{v * 100:.0f}%"
templates.env.filters["money"] = lambda v: f"${v:,.0f}"
templates.env.filters["timecode"] = lambda v: f"{int(v) // 60:02}:{int(v) % 60:02}"


def create_app(database_url: str | None = None) -> FastAPI:
    engine = make_engine(database_url or os.getenv("DATABASE_URL", "sqlite:///./winmap.db"))
    avg_deal_size = float(os.getenv("AVG_DEAL_SIZE_USD", "12000"))
    if not math.isfinite(avg_deal_size) or avg_deal_size <= 0:
        raise ValueError("AVG_DEAL_SIZE_USD must be a finite positive number.")

    @asynccontextmanager
    async def lifespan(app):
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            if session.scalar(select(func.count()).select_from(RepRecord)) == 0:
                seed_database(session)
        yield
        engine.dispose()

    app = FastAPI(title="Objection Win-Map", lifespan=lifespan)
    app.state.engine = engine
    app.mount("/static", StaticFiles(directory=PACKAGE / "static"), name="static")

    def render(request, template, **context):
        return templates.TemplateResponse(
            request=request,
            name=template,
            context={
                "labels": LABELS,
                "tactic_labels": TACTIC_LABELS,
                "focus_notes": FOCUS_NOTES,
                **context,
            },
        )

    @app.get("/health")
    def health():
        with Session(engine) as session:
            session.execute(select(1))
        return {"status": "ok"}

    @app.get("/tokens.css", include_in_schema=False)
    def tokens():
        path = PACKAGE / "static/tokens.css"
        return FileResponse(
            path if path.exists() else PACKAGE.parents[1] / "tokens.css", media_type="text/css"
        )

    def meeting_data(meeting):
        return {
            "id": meeting.id,
            "rep_id": meeting.rep_id,
            "team_id": meeting.team_id,
            "outcome": meeting.outcome,
            "customer_name": meeting.customer_name,
            "utterances": [
                {"speaker": u.speaker, "ts": u.ts, "text": u.text} for u in meeting.utterances
            ],
            "analysis": [
                ObjectionMoment.model_validate(m, from_attributes=True) for m in meeting.moments
            ],
        }

    @app.post("/api/meetings", status_code=201)
    def ingest(payload: MeetingIn):
        with Session(engine) as session:
            try:
                return meeting_data(save_meeting(session, payload))
            except ValueError as error:
                raise HTTPException(422, str(error)) from error

    @app.get("/api/meetings/{meeting_id}")
    def get_meeting(meeting_id: str):
        with Session(engine) as session:
            meeting = session.get(Meeting, meeting_id)
            if not meeting:
                raise HTTPException(404, "Meeting not found.")
            return meeting_data(meeting)

    @app.get("/api/winmap", response_model=WinMap)
    def winmap_api(team_id: str = "summit"):
        with Session(engine) as session:
            return compute_winmap(session, team_id, avg_deal_size)

    @app.get("/api/reps/{rep_id}/brief", response_model=DailyBrief)
    def brief_api(rep_id: str):
        with Session(engine) as session:
            try:
                return compute_brief(session, rep_id)
            except LookupError as error:
                raise HTTPException(404, str(error)) from error

    @app.get("/")
    def index(request: Request):
        with Session(engine) as session:
            data = compute_winmap(session, "summit", avg_deal_size)
            reps = list(
                session.scalars(
                    select(RepRecord).where(RepRecord.team_id == "summit").order_by(RepRecord.name)
                )
            )
            return render(
                request,
                "winmap.html",
                active="winmap",
                winmap=data,
                reps=reps,
                top_names=[rep.name for rep in reps if rep.id in data.top_rep_ids],
                total=sum(r.est_revenue_lost for r in data.rows if r.sufficient_data),
                avg_deal_size=avg_deal_size,
            )

    @app.get("/reps/{rep_id}")
    def brief_page(request: Request, rep_id: str):
        return render(request, "brief.html", active="brief", brief=brief_api(rep_id))

    @app.get("/meetings/{meeting_id}")
    def meeting_page(request: Request, meeting_id: str):
        with Session(engine) as session:
            meeting = session.get(Meeting, meeting_id)
            if not meeting:
                raise HTTPException(404, "Meeting not found.")
            return render(request, "meeting.html", active="winmap", meeting=meeting)

    @app.get("/story")
    def story(request: Request):
        data = winmap_api("summit")
        spouse = next(r for r in data.rows if r.objection == "spouse/partner")
        return render(
            request,
            "story.html",
            active="story",
            winmap=data,
            spouse=spouse,
            total=int(sum(r.est_revenue_lost for r in data.rows if r.sufficient_data)),
        )

    return app


app = create_app()
