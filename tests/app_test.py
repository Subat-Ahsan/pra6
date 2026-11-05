import json
import os
import pytest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TEST_DB = "test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{BASE_DIR.joinpath(TEST_DB)}"

from app import app, db


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


def login(client, username, password):
    """Login helper function"""
    return client.post(
        "/login",
        data=dict(username=username, password=password),
        follow_redirects=True,
    )


def logout(client):
    """Logout helper function"""
    return client.get("/logout", follow_redirects=True)


def test_index(client):
    """Ensure the index route returns a 200 status"""
    response = client.get("/", content_type="html/text")
    assert response.status_code == 200


def test_database(client):
    """Initial test. Ensure that the test database exists"""
    assert BASE_DIR.joinpath(TEST_DB).is_file()


def test_empty_db(client):
    """Ensure database is blank"""
    rv = client.get("/")
    assert b"No entries yet. Add some!" in rv.data


def test_login_logout(client):
    """Test login and logout using helper functions"""
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"])
    assert b"You were logged in" in rv.data
    rv = logout(client)
    assert b"You were logged out" in rv.data
    rv = login(client, app.config["USERNAME"] + "x", app.config["PASSWORD"])
    assert b"Invalid username" in rv.data
    rv = login(client, app.config["USERNAME"], app.config["PASSWORD"] + "x")
    assert b"Invalid password" in rv.data


def test_messages(client):
    """Ensure that user can post messages"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.post(
        "/add",
        data=dict(title="<Hello>", text="<strong>HTML</strong> allowed here"),
        follow_redirects=True,
    )
    assert b"No entries here so far" not in rv.data
    assert b"&lt;Hello&gt;" in rv.data
    assert b"<strong>HTML</strong> allowed here" in rv.data


def test_delete_message(client):
    """Ensure the messages are being deleted only when logged in"""
    rv = client.get("/delete/1")
    data = json.loads(rv.data)
    assert data["status"] == 0
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    rv = client.get("/delete/1")
    data = json.loads(rv.data)
    assert data["status"] == 1


def test_delete_requires_login(client):
    """Ensure deleting without logging in returns a 401"""
    rv = client.get("/delete/1")
    assert rv.status_code == 401


def test_search_page_loads(client):
    """Ensure the search page loads without a query"""
    rv = client.get("/search/")
    assert rv.status_code == 200


def test_search_matches_title_and_text(client):
    """Ensure search returns matching entries and hides the rest"""
    login(client, app.config["USERNAME"], app.config["PASSWORD"])
    client.post(
        "/add",
        data=dict(title="Apple pie", text="A dessert recipe"),
        follow_redirects=True,
    )
    client.post(
        "/add",
        data=dict(title="Banana bread", text="Needs ripe fruit"),
        follow_redirects=True,
    )
    rv = client.get("/search/?query=apple")
    assert b"Apple pie" in rv.data
    assert b"Banana bread" not in rv.data
    rv = client.get("/search/?query=RIPE")
    assert b"Banana bread" in rv.data
    assert b"Apple pie" not in rv.data

