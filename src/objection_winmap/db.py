from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from sqlalchemy.pool import StaticPool

from .agent import HeuristicObjectionAgent, ObjectionAgent
from .schemas import MeetingIn


class Base(DeclarativeBase):
    pass


class RepRecord(Base):
    __tablename__ = "reps"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    team_id: Mapped[str] = mapped_column(String(80), index=True)
    name: Mapped[str] = mapped_column(String(120))


class Meeting(Base):
    __tablename__ = "meetings"
    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    rep_id: Mapped[str] = mapped_column(ForeignKey("reps.id"), index=True)
    team_id: Mapped[str] = mapped_column(String(80), index=True)
    customer_name: Mapped[str] = mapped_column(String(120))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    outcome: Mapped[str] = mapped_column(String(10))
    deal_value: Mapped[float] = mapped_column(Float)
    rep: Mapped[RepRecord] = relationship()
    utterances: Mapped[list["UtteranceRecord"]] = relationship(
        cascade="all, delete-orphan", order_by="UtteranceRecord.position"
    )
    moments: Mapped[list["MomentRecord"]] = relationship(
        cascade="all, delete-orphan", order_by="MomentRecord.ts"
    )


class UtteranceRecord(Base):
    __tablename__ = "utterances"
    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), index=True)
    position: Mapped[int]
    speaker: Mapped[str] = mapped_column(String(10))
    ts: Mapped[float]
    text: Mapped[str]


class MomentRecord(Base):
    __tablename__ = "objection_moments"
    id: Mapped[int] = mapped_column(primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), index=True)
    objection: Mapped[str] = mapped_column(String(40), index=True)
    ts: Mapped[float]
    customer_quote: Mapped[str]
    response_ts: Mapped[float | None]
    rep_response: Mapped[str]
    tactics: Mapped[list[str]] = mapped_column(JSON)
    quality_score: Mapped[float]


def make_engine(url: str):
    if url.startswith(("postgres://", "postgresql://")):
        url = "postgresql+psycopg://" + url.split("://", 1)[1]
    options = {}
    if url.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
        if url in ("sqlite://", "sqlite:///:memory:"):
            options["poolclass"] = StaticPool
    engine = create_engine(url, **options)
    if url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def foreign_keys(connection, _record):
            connection.execute("PRAGMA foreign_keys=ON")

    return engine


def save_meeting(
    session: Session,
    payload: MeetingIn,
    *,
    agent: ObjectionAgent | None = None,
    meeting_id: str | None = None,
    commit: bool = True,
) -> Meeting:
    rep = session.get(RepRecord, payload.rep_id)
    if not rep or rep.team_id != payload.team_id:
        raise ValueError("Choose an existing rep belonging to this team.")
    moments = (agent or HeuristicObjectionAgent()).detect_objections(payload)
    meeting = Meeting(id=meeting_id or str(uuid4()), **payload.model_dump(exclude={"utterances"}))
    meeting.utterances = [
        UtteranceRecord(position=i, **u.model_dump()) for i, u in enumerate(payload.utterances)
    ]
    meeting.moments = [MomentRecord(**m.model_dump()) for m in moments]
    session.add(meeting)
    if commit:
        session.commit()
    else:
        session.flush()
    return meeting
