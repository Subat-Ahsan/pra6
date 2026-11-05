from pathlib import Path

from project.app import app, init_db


def test_index():
    """Ensure the index route returns a 200 status and the hello message."""
    tester = app.test_client()
    response = tester.get("/", content_type="html/text")

    assert response.status_code == 200
    assert response.data == b"Hello, World!"


def test_database():
    """Ensure the database file is created after initializing the database."""
    init_db()
    assert Path("flaskr.db").is_file()