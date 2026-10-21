import json
import os
from pathlib import Path

from sqlalchemy.orm import Session

from .db import Base, Meeting, RepRecord, make_engine, save_meeting
from .transcriber import FixtureTranscriber

PACKAGE = Path(__file__).resolve().parent
SEED_DIR = PACKAGE / "fixtures" if (PACKAGE / "fixtures").exists() else PACKAGE.parents[1] / "seed"


def seed_database(session: Session):
    team = json.loads((SEED_DIR / "team.json").read_text())
    for rep in team["reps"]:
        if not session.get(RepRecord, rep["id"]):
            session.add(RepRecord(**rep))
    session.flush()
    transcriber = FixtureTranscriber()
    for path in sorted((SEED_DIR / "transcripts").glob("*.json")):
        if not session.get(Meeting, path.stem):
            save_meeting(session, transcriber.transcribe(path), meeting_id=path.stem, commit=False)
    session.commit()


if __name__ == "__main__":
    engine = make_engine(os.getenv("DATABASE_URL", "sqlite:///./winmap.db"))
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
    engine.dispose()
    print("Summit Roofing seed loaded (idempotent).")
