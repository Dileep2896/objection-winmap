import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from objection_winmap.db import Base, make_engine
from objection_winmap.main import create_app
from objection_winmap.seed import seed_database


@pytest.fixture
def session():
    engine = make_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_database(session)
        yield session
    engine.dispose()


@pytest.fixture
def client():
    with TestClient(create_app("sqlite://")) as client:
        yield client
