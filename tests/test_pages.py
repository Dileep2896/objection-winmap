import pytest


@pytest.mark.parametrize(
    "url,text",
    [
        ("/", "Win-Map"),
        ("/reps/ben", "Daily Brief"),
        ("/story", "kitchen-table meetings"),
    ],
)
def test_pages(client, url, text):
    response = client.get(url)
    assert response.status_code == 200
    assert text in response.text


def test_story_uses_computed_numbers_and_accessible_motion(client):
    data = client.get("/api/winmap?team_id=summit").json()
    story = client.get("/story").text
    total = sum(r["est_revenue_lost"] for r in data["rows"] if r["sufficient_data"])
    assert f'data-target="{int(total)}"' in story
    assert "prefers-reduced-motion" in client.get("/static/story.js").text
    assert "prefers-reduced-motion" in client.get("/static/styles.css").text


def test_missing_rep_page(client):
    assert client.get("/reps/missing").status_code == 404
