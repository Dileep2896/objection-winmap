from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Objection = Literal["spouse/partner", "price", "think about it", "competitor", "timing", "trust"]


class Utterance(BaseModel):
    speaker: Literal["customer", "rep"]
    ts: float = Field(ge=0, allow_inf_nan=False)
    text: str = Field(min_length=1, max_length=10000)


class MeetingIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    rep_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    team_id: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    customer_name: str = Field(default="Homeowner", max_length=120)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    outcome: Literal["closed", "lost"]
    deal_value: float = Field(default=12000, gt=0, allow_inf_nan=False)
    utterances: list[Utterance] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def chronological(self):
        if any(a.ts > b.ts for a, b in zip(self.utterances, self.utterances[1:], strict=False)):
            raise ValueError("Utterances must be ordered by timestamp.")
        return self


class Rep(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    team_id: str


class ObjectionMoment(BaseModel):
    objection: Objection
    ts: float
    customer_quote: str
    response_ts: float | None = None
    rep_response: str = ""
    tactics: list[str] = Field(default_factory=list)
    quality_score: float = 0


class BestResponse(BaseModel):
    rep_name: str
    meeting_id: str
    ts: float
    quote: str


class WinMapRow(BaseModel):
    objection: Objection
    occurrences: int
    top_occurrences: int
    rest_occurrences: int
    top_close_rate: float
    rest_close_rate: float
    gap: float
    gap_ci_low: float
    gap_ci_high: float
    est_revenue_lost: float
    best_response: BestResponse | None
    top_tactics: list[str]
    sufficient_data: bool


class WinMap(BaseModel):
    team_id: str
    meeting_count: int
    rep_count: int
    top_rep_ids: list[str]
    rows: list[WinMapRow]


class Evidence(BaseModel):
    meeting_id: str
    customer_name: str
    ts: float
    quote: str
    response: str


class DailyBrief(BaseModel):
    rep: Rep
    focus_objection: Objection | None = None
    your_close_rate: float = 0
    top_close_rate: float = 0
    practice_line: str | None = None
    practice_source: BestResponse | None = None
    missing_tactic: str | None = None
    drill: str | None = None
    evidence: list[Evidence] = Field(default_factory=list)
