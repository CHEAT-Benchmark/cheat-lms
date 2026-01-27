"""Tests for Flask application."""

import pytest
from app import create_app, db
from app.config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    TELEMETRY_ENABLED = False


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


class TestAuth:
    def test_login_page_loads(self, client):
        response = client.get("/login")
        assert response.status_code == 200
        assert b"Log In" in response.data

    def test_login_valid_credentials(self, client):
        response = client.post("/login", data={
            "username": "jsmith",
            "password": "student123"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Dashboard" in response.data

    def test_login_invalid_credentials(self, client):
        response = client.post("/login", data={
            "username": "jsmith",
            "password": "wrongpassword"
        }, follow_redirects=True)
        assert response.status_code == 200
        assert b"Invalid username or password" in response.data

    def test_logout(self, client):
        # Login first
        client.post("/login", data={
            "username": "jsmith",
            "password": "student123"
        })

        # Then logout
        response = client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"Log In" in response.data


class TestDashboard:
    def test_dashboard_requires_login(self, client):
        response = client.get("/dashboard", follow_redirects=True)
        assert response.status_code == 200
        assert b"Log In" in response.data

    def test_dashboard_shows_courses(self, client):
        # Login
        client.post("/login", data={
            "username": "jsmith",
            "password": "student123"
        })

        response = client.get("/dashboard")
        assert response.status_code == 200
        assert b"My Courses" in response.data


class TestCourseView:
    def test_course_view_requires_login(self, client):
        response = client.get("/course/1", follow_redirects=True)
        assert b"Log In" in response.data
