import pytest
from productivity_app import create_app, db


@pytest.fixture()
def client():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
    })

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


def test_signup_and_login_flow(client):
    signup_response = client.post(
        "/signup",
        json={"username": "alice", "password": "secret123"},
    )
    assert signup_response.status_code == 201

    login_response = client.post(
        "/login",
        json={"username": "alice", "password": "secret123"},
    )
    assert login_response.status_code == 200

    me_response = client.get("/check_session")
    assert me_response.status_code == 200
    assert me_response.get_json()["username"] == "alice"


def test_notes_are_private_to_their_owner(client):
    client.post("/signup", json={"username": "alice", "password": "secret123"})
    client.post("/signup", json={"username": "bob", "password": "secret123"})
    client.post("/login", json={"username": "alice", "password": "secret123"})

    create_response = client.post(
        "/notes",
        json={"title": "Study", "content": "Review Flask auth", "category": "work"},
    )
    assert create_response.status_code == 201
    note_id = create_response.get_json()["id"]

    client.post("/logout")
    client.post("/login", json={"username": "bob", "password": "secret123"})

    get_response = client.get(f"/notes/{note_id}")
    assert get_response.status_code == 403


def test_notes_crud_and_pagination(client):
    client.post("/signup", json={"username": "alice", "password": "secret123"})
    client.post("/login", json={"username": "alice", "password": "secret123"})

    for index in range(12):
        client.post(
            "/notes",
            json={"title": f"Note {index}", "content": "Body", "category": "general"},
        )

    list_response = client.get("/notes?page=1&per_page=5")
    assert list_response.status_code == 200
    payload = list_response.get_json()
    assert len(payload["notes"]) == 5
    assert payload["page"] == 1
    assert payload["pages"] == 3
