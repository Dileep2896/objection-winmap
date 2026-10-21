def test_ingestion_changes_winmap_and_persists(client):
    before = client.get("/api/winmap?team_id=summit").json()
    response = client.post(
        "/api/meetings",
        json={
            "rep_id": "ben",
            "team_id": "summit",
            "outcome": "lost",
            "utterances": [
                {"speaker": "customer", "ts": 12, "text": "I need my wife here."},
                {"speaker": "rep", "ts": 16, "text": "I can give you a discount."},
            ],
        },
    )
    assert response.status_code == 201
    meeting = response.json()
    assert meeting["analysis"][0]["objection"] == "spouse/partner"
    assert client.get(f"/api/meetings/{meeting['id']}").status_code == 200
    after = client.get("/api/winmap?team_id=summit").json()
    assert after["rows"][0]["occurrences"] == before["rows"][0]["occurrences"] + 1


def test_validation_and_unknown_resources(client):
    assert client.post("/api/meetings", json={}).status_code == 422
    assert client.get("/api/reps/missing/brief").status_code == 404
    assert client.get("/api/meetings/missing").status_code == 404
    base = {
        "rep_id": "ben",
        "team_id": "wrong",
        "outcome": "lost",
        "utterances": [{"speaker": "customer", "ts": 0, "text": "Hello"}],
    }
    assert client.post("/api/meetings", json=base).status_code == 422
    base["team_id"] = "summit"
    base["utterances"][0]["ts"] = -1
    assert client.post("/api/meetings", json=base).status_code == 422


def test_non_chronological_transcript_rejected(client):
    response = client.post(
        "/api/meetings",
        json={
            "rep_id": "ben",
            "team_id": "summit",
            "outcome": "lost",
            "utterances": [
                {"speaker": "customer", "ts": 20, "text": "Hello"},
                {"speaker": "rep", "ts": 10, "text": "Hello"},
            ],
        },
    )
    assert response.status_code == 422


def test_meeting_survives_app_restart(tmp_path):
    from fastapi.testclient import TestClient

    from objection_winmap.main import create_app

    url = f"sqlite:///{tmp_path / 'persistent.db'}"
    with TestClient(create_app(url)) as first:
        response = first.post(
            "/api/meetings",
            json={
                "rep_id": "ben",
                "team_id": "summit",
                "outcome": "closed",
                "utterances": [{"speaker": "customer", "ts": 3, "text": "My wife is here."}],
            },
        )
        assert response.status_code == 201
        meeting_id = response.json()["id"]
    with TestClient(create_app(url)) as second:
        assert second.get(f"/api/meetings/{meeting_id}").status_code == 200
        assert second.get("/api/winmap").json()["meeting_count"] == 73
